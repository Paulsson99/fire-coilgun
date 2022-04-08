import spidev
import serial
import time


class Arduino:
	"""Class for communicating with a Arduino"""

	# Commands
	FIRE = "FIRE"
	READ_VOLTAGES = "VOLTAGE"
	TEST = "TEST"
	END = '\n'
	SEP = ','


	def __init__(self, port: str, baudrate: int, timeout: int=1):
		self.port = port
		self.baudrate = baudrate
		self.timeout = timeout

		self.arduino = None

	def send(self, message: str):
		"""Send a message to the Arduino"""
		self.arduino.write(bytes(message, 'utf-8'))

	def read(self) -> str:
		"""Read a response from the Arduino"""
		response = ""
		while True:
			char = self.arduino.read().decode('utf-8')
			if Arduino.END == char or char == '':
				break
			response += char
		return response

	def test_connection(self, test_times: int=10) -> bool:
		"""Test the connection with the Arduino"""
		for i in range(test_times):
			self.send(Arduino.TEST)
			response = self.read()

			if response == "OK":
				return True
			time.sleep(1)
		return False

	def connect(self) -> bool:
		"""Connect to the Arduino"""
		self.arduino = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
		self.arduino.flush()
		time.sleep(1)
		if not self.test_connection():
			self.close()
			return False
		return True

	def close(self):
		"""Close connection to the Arduino"""
		self.arduino.close()


class Potentiometer:
	"""Class for setting the resistance in a digtal potentiometer"""

	MSB = 0b00010001 	# Command byte for writing to the potentiometer

	def __init__(self):
		self.spi = spidev.SpiDev()
		self.spi.open(0, 0)
		self.spi.max_speed_hz = 976000
		self.selector_pins = []

	def set(self, x: int):
		"""
		Set the resistance of a potentiometer. 
		Select the potentiometer by pulling C0 LOW and HIGH
		"""
		self.spi.xfer([self.MSB, x])

	def close(self):
		self.spi.close()

class PinIsNotConfigured(Exception):
	pass
