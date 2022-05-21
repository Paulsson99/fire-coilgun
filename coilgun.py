from communication import Arduino, CommunicationError
import numpy as np
import time
import logging


class Coil:
	"""Class for handling a single Coil in a coilgun"""

	TOTAL = 0

	def __init__(
		self,
		capacitance: float,			# Total capacitance in the capacitance bank [F]
		R1: float, 					# First resistance in the voltage divider
		R2: float, 					# Second resistance in the voltage divider
		state: bool 				# Is the coil on?
	):
		self.capacitance = capacitance

		self.R1 = R1
		self.R2 = R2

		# Is ready
		self.READY = False

		self.ON = state

		# Set a unique ID
		self.id = Coil.TOTAL
		Coil.TOTAL += 1

	@classmethod
	def read_voltages(cls, arduino: Arduino) -> list[int]:
		"""Read voltages from all CBs"""
		# Send command
		arduino.send(Arduino.READ_VOLTAGES)
		# Receive response
		voltages = arduino.read()

		# Convert to integers and split the string into an array
		return [int(v) for v in voltages.split(Arduino.SEP)]

	@classmethod
	def from_dict(cls, coil_dict: dict):
		"""Create a coil from a dict"""
		return cls(**coil_dict)

	def read_voltage(self, voltages: list[int]) -> float:
		"""Read the voltage over this CB"""

		# Take out the voltage for this CB
		pot_voltage = voltages[self.id]

		# Convert from 0-1023 to 0-5V
		pot_voltage = pot_voltage * 5 / 1023

		# Convert to voltage over CB
		return pot_voltage * (self.R1 + self.R2) / self.R2

	def control_voltage(self, voltage, max_voltage) -> bool:
		"""
		Control the voltage for the coil. 
		Return true if it needs more voltage, False otherwise
		"""
		# if voltage < max_voltage:
		# 	return True
		# else:
		# 	self.READY = False
		# 	return False
		if self.READY or not self.ON:
			return False
		self.READY = voltage > max_voltage
		return (voltage < max_voltage) or self.READY

	def efficiency(self, v1: float, v2: float, voltage: float, m: float) -> float:
		"""
		Calculate coil efficiency
		v1: Projectile velocity before the coil
		v2: Projectile velocity after the coil
		voltage: Voltage in the CB
		m: Projectile mass
		"""
		E_k = m * (v2**2 - v1**2) / 2
		return E_k / self.CB_energy(voltage)

	def CB_energy(self, voltage):
		"""Calculate energy in the CB for voltage"""
		return self.capacitance * voltage**2 / 2

	def turn_on(self):
		"""Turn on the coil"""
		self.ON = True

	def turn_off(self):
		"""Turn off the coil"""
		self.ON = False

	def reset(self):
		"""Reset the coil"""
		self.READY = False



class Coilgun:
	"""Class for controling the coilgun"""

	MAX_VOLTAGE_FOR_SAFE_DRAIN = 20

	def __init__(
		self, 
		coils: list[Coil], 
		arduino: Arduino, 
		projectile_dimeter: float,
		projectile_mass: float,
		logger: logging.Logger = None
	):
		self.coils = coils
		self.arduino = arduino
		self.projectile_dimeter = projectile_dimeter
		self.projectile_mass = projectile_mass

		# Create a default logger
		if logger is None:
			logger = logging.getLogger('Coilgun')
			# Add console logging to the logger
			c_handler = logging.StreamHandler()
			c_handler.setLevel(logging.WARNING)
			c_format = logging.Formatter('%(name)s : %(levelname)s : %(message)s')
			c_handler.setFormatter(c_format)
			logger.addHandler(c_handler)
		self.logger = logger

		# Logging
		self.logger.debug(f"Coilgun with {len(self)} coils was created")

		# Startup 
		self.OFF()

	def OFF(self):
		"""Reset the coilgun"""
		self.arduino.flush_serial()
		self.MAIN_HV_OFF()
		# Drain and turn off HV to all CBs
		self.DRAIN_ALL(True)
		self.HV_ALL(False)

		for coil in self.coils:
			coil.reset()

		# Logging
		self.logger.debug("Coilgun was turned off")

	def ON(self):
		self.DRAIN_ALL(False)
		self.MAIN_HV_ON()
		self.HV_ALL(True)
		self.arduino.send(Arduino.CHARGE)
		response = self.arduino.read()
		if not response == Arduino.CHARGE_RESPONSE:
			self.logger.warning(f"Arduino did not swith to the charge state correctly. Responded with: '{response}")
			# raise CommunicationError(f"Arduino did not turn on main HV correctly. Responded with: '{response}")
		else:
			self.logger.debug(f"Arduino swithed to charge state")
		# Logging
		self.logger.debug("Coilgun was turned on")

	def READ_VOLTAGES(self):
		"""Read all voltages for all CBs"""

		# Read all voltages with the Arduino
		pot_values = Coil.read_voltages(arduino=self.arduino)
		self.logger.debug(f"Voltage values read from the Arduino: {pot_values}")

		voltages = [coil.read_voltage(pot_values) for coil in self.coils]
		self.logger.debug(f"Arduino voltages converted to: {voltages}")

		return voltages

	def FIRE(self):
		"""Fire the coilgun"""
		# Fire coilgun and read sensor blocking time in microseconds
		self.arduino.send(Arduino.FIRE)
		self.logger.debug(f"Coilgun fired")
		blocking_times_us = self.arduino.read()
		trigger_times_us = self.arduino.read()
		self.logger.debug(f"Sensors were blocked for {blocking_times_us} us")
		self.logger.debug(f"Sensors blocked at: {trigger_times_us} us")

		# Calculate the projectile velocities at the sensors
		blocking_times = np.array([int(t_us) * 1e-6 for t_us in blocking_times_us.split(Arduino.SEP)])
		trigger_times = np.array([int(t_us) * 1e-6 for t_us in trigger_times_us.split(Arduino.SEP)])
		velocities = self.projectile_dimeter / blocking_times
		self.logger.debug(f"Calculated velocities for the projectile: {velocities}")

		return velocities, trigger_times

	def READY_2_FIRE(self):
		"""Check if the coilgun is ready to fire"""
		for coil in self.coils:
			if not coil.READY:
				return False
		return True

	def MAIN_HV_ON(self):
		"""Turn on HIGH VOLTAGE"""
		self.arduino.send(Arduino.ON)
		response = self.arduino.read()
		if not response == Arduino.HV_ON:
			self.logger.warning(f"Arduino did not turn on main HV correctly. Responded with: '{response}")
			raise CommunicationError(f"Arduino did not turn on main HV correctly. Responded with: '{response}")
		self.logger.debug(f"Main HV turned on")

	def MAIN_HV_OFF(self):
		"""Turn off HIGH VOLTAGE"""
		self.arduino.send(Arduino.OFF)
		response = self.arduino.read()
		if not response == Arduino.HV_OFF:
			self.logger.critical(f"Arduino did not turn off main HV correctly. Responded with: '{response}'")
			raise CommunicationError(f"Arduino did not turn off main HV correctly. Responded with: '{response}'")
		self.logger.debug(f"Main HV turned off")

	def DRAIN_CB(self, CBs_to_drain: list[bool]):
		"""Drain all CBs"""
		# This is flipped because the relay is NC
		# Only 
		CBs_to_drain = [(not CB) and (coil.ON) for CB, coil in zip(CBs_to_drain, self)]
		message = self.convert_bool_list_to_Arduino_message(CBs_to_drain)
		self.logger.debug(f"Draining command: {message}")

		# Send command and message
		self.arduino.send(Arduino.DRAIN)
		self.arduino.send(message)

		response = self.arduino.read()
		if not Arduino.DRAIN_RESPONSE in response:
			self.logger.critical(f"Arduino did not drain CBs correctly. Responded with: '{response}'")
			raise CommunicationError(f"Arduino did not drain CBs correctly. Responded with: '{response}'")
		self.logger.debug(f"CBs drained")

	def DRAIN_ALL(self, drain: bool = True):
		"""Drain or don't drain all CBs depending on the variable 'drain'"""
		self.DRAIN_CB([drain] * len(self))

	def HV_2_CB(self, HV_states: list[bool]):
		"""Turn HV ON/OFF"""
		# Only allow HV to be turned on for a coil that is ON
		HV_states = [HV_state and coil.ON for HV_state, coil in zip(HV_states, self)]
		message = self.convert_bool_list_to_Arduino_message(HV_states)
		self.logger.debug(f"HV command: {message}")

		# Send command and message
		self.arduino.send(Arduino.HV)
		self.arduino.send(message)

		response = self.arduino.read()
		if not Arduino.HV_RESPONSE in response:
			self.logger.critical(f"Arduino did not set HV to CBs correctly. Responded with: '{response}'")
			raise CommunicationError(f"Arduino did not set HV to CBs correctly. Responded with: '{response}'")
		self.logger.debug(f"HV set")

	def HV_ALL(self, HV_state: bool = False):
		"""Turn HV ON/OFF for all coils depending on the variable 'HV_state'"""
		self.HV_2_CB([HV_state] * len(self))

	def START_COUNTDOWN(self):
		"""Start the countdown"""
		self.arduino.send(Arduino.COUNTDOWN)
		response = self.arduino.read()
		if not response == Arduino.COUNTDOWN_RESPONSE:
			self.logger.warning(f"Arduino did not start a countdown correctly. Responded with: '{response}")
			# raise CommunicationError(f"Arduino did not turn on main HV correctly. Responded with: '{response}")
		else:
			self.logger.debug(f"Contdown started")

	def DISPLAY_CHARGE(self, percent):
		"""Display the current percentage of the maximum voltage"""
		self.arduino.send(Arduino.DISPLAY_CHARGE)
		self.arduino.send(str(percent))
		response = self.arduino.read()
		if not Arduino.DISPLAY_CHARGE_RESPONSE in response:
			self.logger.warning(f"Arduino did not display the charge correctly. Responded with: '{response}")
			# raise CommunicationError(f"Arduino did not turn on main HV correctly. Responded with: '{response}")
		else:
			self.logger.debug(f"Displaying charge of {percent:.01%}")

	def CHARGE_COILGUN(self, max_voltages: list[float]):
		"""Charge the coilgun"""
		self.DRAIN_CB([False] * len(self))
		self.HV_2_CB([True] * len(self))
		self.MAIN_HV_ON()

		self.logger.info(f"Charging coilgun to {max_voltages}V")

		try:
			while not self.READY_2_FIRE():
				voltages = self.READ_VOLTAGES()
				HV_on_off = []
				for coil, voltage, max_voltage in zip(self.coils, voltages, max_voltages):
					HV_on_off.append(coil.control_voltage(voltage, max_voltage))
				self.HV_2_CB(HV_on_off)

				self.logger.info(f"Voltages are: {voltages}V")
				self.logger.debug(f"HV that are on are: {HV_on_off}")
		except KeyboardInterrupt:
			self.logger.info(f"Charge of coilgun was stopped manually at: {voltages}V")
			self.ABORT()
		finally:
			self.HV_ALL(False)
			self.MAIN_HV_OFF()

		self.logger.info("Coilgun is ready to FIRE!")

	def SENSORS(self):
		"""Get the state of all the sensors. (Only used for testing)"""
		self.arduino.send(Arduino.SENSORS)
		response = self.arduino.read()

		self.logger.debug(f"Sensors values are: {response}")
		return response

	def BLINK(self):
		self.arduino.send(Arduino.BLINK)
		response = self.arduino.read()
		if not response == Arduino.BLINK_RESPONSE:
			self.logger.warning(f"Arduino did not start blinking correctly. Responded with: '{response}")
			# raise CommunicationError(f"Arduino did not turn on main HV correctly. Responded with: '{response}")
		else:
			self.logger.debug(f"Arduino is now blinking")

	def ABORT(self):
		"""Abort command execution on Arduino"""
		time.sleep(0.01)
		self.arduino.flush_serial()
		self.arduino.send(Arduino.ABORT)
		response = self.arduino.read()

		self.logger.debug("Aborting execution off command on Arduino")

		if not response == Arduino.ABORT_RESPONSE:
			self.logger.critical(f"Arduino did not abort correctly. Responded with: '{response}'")
			raise CommunicationError(f"Arduino did not abort correctly. Responded with: '{response}'")

		

	def convert_bool_list_to_Arduino_message(self, bool_list) -> str:
		"""Convert a list of booleans to a message the Arduino can read"""
		return ''.join(['1' if CB else '0' for CB in bool_list])

	def efficiency(self, voltages: list[float], velocities: list[float]) -> list[float]:
		"""Calculate coilgun efficiency"""
		eta = []
		coilgun_energy = 0
		v_in = 0
		for coil, v_out, voltage in zip(self, velocities, voltages):
			eta.append(coil.efficiency(v_in, v_out, voltage, self.projectile_mass))
			coilgun_energy += coil.CB_energy(voltage)
			# Velocity in before the next coil is the velocity out for this coil
			v_in = v_out
		E_k = self.projectile_mass * velocities[-1]**2 / 2
		return eta, E_k / coilgun_energy

		

	def shutdown(self):
		"""Cleanup"""
		self.ABORT()
		self.logger.info("Shutting down coilgun...")
		self.OFF()
		self.arduino.close()
		self.logger.info("Shutdown sucessfull!")

	def __len__(self) -> int:
		"""Get length of the coilgun (number of coils)"""
		return len(self.coils)

	def __iter__(self):
		"""Iterate over the coils in the coilgun"""
		return iter(self.coils)












