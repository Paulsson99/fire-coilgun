from requests import ReadTimeout
from communication import Arduino, Potentiometer
import RPi.GPIO as GPIO
import time
import numpy as np


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
		c1: float,
		c2: float,
		c3: float,
		k1: float,
		k2: float
	):
		self.capacitance = capacitance

		self.R = R
		self.R_pot = R_pot
		# Total resistance in the voltage divider
		self.R_tot = self.R + self.R_pot

		self.threshold_voltage = threshold_voltage

		# Pins
		self.set_voltage_pin = set_voltage_pin
		self.ready_pin = ready_pin

		GPIO.setup(self.set_voltage_pin, GPIO.OUT)
		GPIO.setup(self.ready_pin, GPIO.IN)

		GPIO.output(self.set_voltage_pin, GPIO.HIGH)

		# Is ready
		self.isready = False

		# Set a unique ID
		self.id = Coil.TOTAL
		Coil.TOTAL += 1

		# Potentiometer is set to
		self.pot_x = 0

		# Constants
		self.c1 = c1
		self.c2 = c2
		self.c3 = c3
		self.k1 = k1
		self.k2 = k2

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

		bias = self.calculate_bias_point(self.pot_x)

		# Convert to voltage over CB
		return (pot_voltage - bias) / self.calculate_voltage_slope(bias)

	def calculate_bias_point(self, x: int) -> float:
		"""Calculate bias point for the potentiometer"""
		return self.k1*x + self.k2
	
	def calculate_voltage_slope(self, bias_point: float) -> float:
		return self.c1*bias_point**2 + self.c2*bias_point + self.c3

	def set_voltage(self, voltage: float, potentiometer: Potentiometer) -> float:
		"""Set the maximum voltage over the CB by turning a potentiometer"""

		bias_point = self.calculate_bias_point(self.pot_x)
		for i in range(30):
			# Exact position for the potentiometer
			x = self.R_tot * (self.threshold_voltage - bias_point) / (self.R_pot * voltage)

			# Convert to an int (0-255)
			x2send = round(x*255)

			# x2send must be between 0 and 255
			x2send = max(min(x2send, 255), 0)

			bias_point = self.calculate_bias_point(x2send)

		# What is the actual voltage set
		if x2send:
			real_voltage = self.R_tot * (self.threshold_voltage - bias_point) / (x2send / 255 * self.R_pot)
		else:
			real_voltage = float('inf')

		if x > 1:
			print(f"{voltage}V is to low a voltage for the feedback to work. Setting voltage {real_voltage}V instead.")

		self.set_pot(x2send, potentiometer)

		return real_voltage

	def set_pot(self, x: int, potentiometer: Potentiometer):
		"""Set the potentiometer"""
		self.pot_x = x
		# Pull selector pin LOW before transfering data
		GPIO.output(self.set_voltage_pin, GPIO.LOW)
		potentiometer.set(x)
		GPIO.output(self.set_voltage_pin, GPIO.HIGH)

	def ready2fire(self):
		"""Check if the coil is ready to fire"""
		if self.isready:
			# If it has ever been ready it is more or less ready now also
			return True
		self.isready = not GPIO.input(self.ready_pin)
		return self.isready

	def reset(self):
		"""Reset the coil"""
		self.isready = False


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

		self.reset()

	def reset(self):
		"""Reset the coilgun"""
		self.HV_OFF()
		self.DRAIN_CB()
		for coil in self.coils:
			coil.reset()

	def set_voltages(self, voltages: list[float]):
		"""Set the maximum voltages for all CBs"""
		set_voltages = []
		for coil, voltage in zip(self.coils, voltages):
			set_voltage = coil.set_voltage(voltage, potentiometer=self.potentiometer)
			set_voltages.append(set_voltage)
		return set_voltages

	def read_voltages(self):
		"""Read all voltages for all CBs"""

		# Read all voltages with the Arduino
		pot_values = Coil.read_voltages(arduino=self.arduino)

		return [coil.read_voltage(pot_values) for coil in self.coils]

	def fire(self):
		"""Fire the coilgun"""
		self.arduino.send(Arduino.FIRE)
		blocking_times_us = self.arduino.read()

		# Calculate the projectile velocities at the sensors
		blocking_times = np.array([int(t_us) * 1e-6 for t_us in blocking_times_us.split(Arduino.SEP)])
		velocities = self.projectile_dimeter / blocking_times

		return velocities

	def charge(self):
		"""Charge the coilgun"""
		self.CHARGE_CB()
		self.HV_ON()

	def stop_charge(self):
		self.HV_OFF()
		self.DRAIN_CB()

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

	def DRAIN_CB(self):
		"""Drain all CBs"""
		GPIO.output(self.drain_voltage_pin, GPIO.LOW)

	def CHARGE_CB(self):
		"""No drain of CBs"""
		GPIO.output(self.drain_voltage_pin, GPIO.HIGH)

	def shutdown(self):
		"""Cleanup"""
		print("Shutting down coilgun...")
		self.HV_OFF()
		self.DRAIN_CB()
		self.arduino.close()
		self.potentiometer.close()
		GPIO.cleanup()
		print("Shutdown sucessfull!")

	def __len__(self) -> int:
		"""Get length of the coilgun (number of coils)"""
		return len(self.coils)












