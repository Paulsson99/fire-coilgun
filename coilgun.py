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
	):
		self.capacitance = capacitance

		self.R = R
		self.R_pot = R_pot

		# Is ready
		self.READY = False

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
		if self.READY:
			return True
		self.READY = voltage > max_voltage
		return (voltages < max_voltage) or self.READY

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
		logger: logging.Logger = None
	):
		self.coils = coils
		self.arduino = arduino
		self.projectile_dimeter = projectile_dimeter

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
		self.MAIN_HV_OFF()
		# Drain and turn off HV to all CBs
		self.DRAIN_CB([True] * len(self))
		self.HV_2_CB([False] * len(self))

		for coil in self.coils:
			coil.reset()

		# Logging
		self.logger.debug("Coilgun was turned off")

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
		self.logger.debug(f"Sensors were blocked for {blocking_times_us} us")

		# Calculate the projectile velocities at the sensors
		blocking_times = np.array([int(t_us) * 1e-6 for t_us in blocking_times_us.split(Arduino.SEP)])
		velocities = self.projectile_dimeter / blocking_times
		self.logger.debug(f"Calculated velocities for the projectile: {velocities}")

		return velocities

	def READY_2_FIRE(self):
		"""Check if the coilgun is ready to fire"""
		for coil in self.coils:
			if not coil.READY:
				return False
		return True

	def MAIN_HV_ON(self):
		"""Turn on HIGH VOLTAGE"""
		self.arduino.send("ON")
		response = self.arduino.read()
		if not response == Arduino.HV_ON:
			self.logger.warning(f"Arduino did not turn on main HV correctly")
			raise CommunicationError("Arduino did not turn on main HV correctly")
		self.logger.debug(f"Main HV turned on")

	def MAIN_HV_OFF(self):
		"""Turn off HIGH VOLTAGE"""
		self.arduino.send("OFF")
		response = self.arduino.read()
		if not response == Arduino.OV_OFF:
			self.logger.critical(f"Arduino did not turn off main HV correctly")
			raise CommunicationError("Arduino did not turn off main HV correctly")
		self.logger.debug(f"Main HV turned off")

	def DRAIN_CB(self, CBs_to_drain: list[bool]):
		"""Drain all CBs"""
		message = ''.join(['1' for CB in CBs_to_drain if CB else '0'])
		self.logger.debug(f"Draining command: {message}")

		response = self.arduino.read()
		if not Arduino.DRAIN_RESPONSE in response:
			self.logger.critical(f"Arduino did not drain CBs correctly")
			raise CommunicationError("Arduino did not drain CBs correctly")
		self.logger.debug(f"CBs drained")

	def HV_2_CB(self, HV_states: list[bool]):
		"""Turn HV ON/OFF"""
		message = ''.join(['1' for CB in HV_states if CB else '0'])
		self.logger.debug(f"HV command: {message}")

		response = self.arduino.read()
		if not Arduino.DRAIN_RESPONSE in response:
			self.logger.critical(f"Arduino did not set HV to CBs correctly")
			raise CommunicationError("Arduino did not set HV to CBs correctly")
		self.logger.debug(f"HV set")

	def CHARGE_COILGUN(self, max_voltages: list[float]):
		"""Charge the coilgun"""
		self.DRAIN_CB([False] * len(self))
		self.HV_2_CB([True] * len(self))
		self.MAIN_HV_ON()

		self.logger.info(f"Charging coilgun to {voltages}V")

		try:
			while not self.READY_2_FIRE():
				voltages = self.read_voltages()
				HV_on_off = []
				for coil, voltage, max_voltage in zip(self.coils, voltages, max_voltages):
					HV_on_off.append(coil.control_voltage(voltage, max_voltage))
				self.HV_2_CB(HV_on_off)

				self.logger.info(f"Voltages are: {voltages}V")
				self.logger.debug(f"HV that are on are: {HV_on_off}")
		except KeyboardInterrupt:
			pass
		finally:
			self.MAIN_HV_OFF()
			self.HV_2_CB([False] * len(self))

		self.logger.info("Coilgun is ready to FIRE!")

	def shutdown(self):
		"""Cleanup"""
		self.logger.debug("Shutting down coilgun...")
		self.OFF()
		self.arduino.close()
		GPIO.cleanup()
		self.logger.debug("Shutdown sucessfull!")

	def __len__(self) -> int:
		"""Get length of the coilgun (number of coils)"""
		return len(self.coils)












