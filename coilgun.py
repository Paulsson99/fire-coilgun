from communication import Arduino, Potentiometer
import RPi.GPIO as GPIO
import time


# Settings
GPIO.setmode(GPIO.BCM)


class Coil:
	"""Class for handling a single Coil in a coilgun"""

	TOTAL = 0

	def __init__(
		self,
		capacitance: float,			# Total capacitance in the capacitance bank [F]
		R: float, 					# Resistance for the resistor in the voltage divider
		R_pot: float, 				# Total resistance over the potentiometer
		threshold_voltage: float, 	# Threshold voltage for switching power ON/OFF
		set_voltage_pin: int, 		# Pin for setting the voltage with the potentiometer
		ready_pin: int, 			# Pin for checking if CB is ready to fire
	):
		self.capacitance = capacitance

		self.R = R
		self.R_pot = R_pot
		# Total resistance in the voltage divider
		self.R_tot = self.R + self.R_pot

		# Pins
		self.set_voltage_pin = set_voltage_pin
		self.drain_voltage_pin = drain_voltage_pin

		GPIO.setup(self.set_voltage_pin, GPIO.OUT)
		GPIO.setup(self.ready_pin, GPIO.IN)

		GPIO.output(self.set_voltage_pin, GPIO.HIGH)
		GPIO.output(self.drain_voltage_pin, GPIO.LOW)


		# Set a unique ID
		self.id = CB.TOTAL
		CB.TOTAL += 1

	@classmethod
	def read_voltages(cls, arduino: Arduino) -> list[int]:
		"""Read voltages from all CBs"""
		# Send command
		arduino.send(Arduino.read_voltage)
		# Receive response
		voltages = arduino.read()

		# Convert to integers and split the string into an array
		return [int(v) for v in voltages.split(Arduino.SEP)]

	@classmethod
	def from_dict(cls, coil_dict: dict) -> cls:
		"""Create a coil from a dict"""
		return cls(**coil_dict)

	def read_voltage(self, voltages: list[int]) -> float:
		"""Read the voltage over this CB"""

		# Take out the voltage for this CB
		pot_voltage = voltages[self.id]

		# Convert from 0-1023 to 0-5V
		pot_voltage = pot_voltage * 5 / 1023

		# Convert to voltage over CB
		return pot_voltage * self.R_tot / self.R_pot

	def set_voltage(self, voltage: float, potentiometer: Potentiometer) -> float:
		"""Set the maximum voltage over the CB by turning a potentiometer"""

		# Exact position for the potentiometer
		x = (self.R_tot * self.threshold_voltage) / (self.R_pot * voltage)

		# Convert to an int (0-255)
		x2send = round(x*255)

		# x2send must be between 0 and 255 (x is never less than 0)
		x2send = min(x2send, 255)

		# What is the actual voltage set
		real_voltage = self.R_tot * self.threshold_voltage / (x2send / 255 * self.R_pot)

		if x > 1:
			print(f"{voltage}V is to low a voltage for the feedback to work. Setting voltage {real_voltage}V instead.")

		# Pull selector pin LOW before transfering data
		GPIO.output(self.set_voltage_pin, GPIO.LOW)
		potentiometer.set(x2send, pin=self.set_voltage_pin)
		GPIO.output(self.set_voltage_pin, GPIO.HIGH)

		return real_voltage

	def ready2fire(self):
		"""Check if the coil is ready to fire"""
		return GPIO.input(self.ready_pin)


class Coilgun:
	"""Class for controling the coilgun"""

	def __init__(
		self, 
		coils: list[Coil], 
		arduino: Arduino, 
		potentiometer: Potentiometer, 
		HV_pin: int,
		drain_voltage_pin: int,
		projectile_dimeter: float
	):
		self.coils = coils
		self.arduino = arduino
		self.potentiometer = potentiometer
		self.HV_pin = HV_pin
		self.drain_voltage_pin = drain_voltage_pin
		self.projectile_dimeter = projectile_dimeter

		GPIO.setup(self.HV_pin, GPIO.OUT)
		GPIO.setup(self.drain_voltage_pin, GPIO.OUT)

		self.HV_OFF()
		self.drain()

	def set_voltages(self, voltages: list[float]):
		"""Set the maximum voltages for all CBs"""
		set_voltages = []
		for coil, voltage in zip(self.coils, voltages):
			set_voltage = coil.set_voltage(voltage, potentiometer=self.potentiometer)
			set_voltages.append(set_voltage)

			print(f"Coil {coil.id} set to {set_voltage:.1f}V")
		return set_voltages

	def read_voltages(self):
		"""Read all voltages for all CBs"""

		# Read all voltages with the Arduino
		pot_values = Coil.read_voltages(arduino=self.arduino)

		return [coil.read_voltage(pot_values) for coil in self.coils]

	def charge(self, max_voltages: list[float]):
		"""Charge the coilgun"""
		self.set_voltages(max_voltages)

		self.no_drain()
		self.HV_ON()

		while not self.ready2fire():
			time.sleep(1)
			voltages = self.read_voltages()

			# TODO: Something better here (LED strip and more)
			print(voltages)

		self.HV_OFF()

	def fire(self, max_voltages: list[float]):
		"""Fire the coilgun"""
		self.arduino.send(Arduino.FIRE)
		blocking_times_us = self.arduino.read()

		# Calculate the projectile velocities at the sensors
		velocities = [projectile_dimeter / (int(t_us) * 1e-6) for t_us in blocking_times_us.split(Arduino.SEP)]

		self.drain()

		return velocities

	def ready2fire(self):
		"""Check if the coilgun is ready to fire"""
		for coil in self.coils:
			if not coil.ready2fire():
				return False
		return True

	def HV_ON(self):
		"""Turn on HIGH VOLTAGE"""
		GPIO.output(self.HV_pin, GPIO.LOW)

	def HV_OFF(self):
		"""Turn off HIGH VOLTAGE"""
		GPIO.output(self.HV_pin, GPIO.HIGH)

	def drain(self):
		"""Drain all CBs"""
		GPIO.output(self.drain_voltage_pin, GPIO.HIGH)

	def no_drain(self):
		"""No drain of CBs"""
		GPIO.output(self.drain_voltage_pin, GPIO.LOW)












