import spidev


class Arduino:
	"""Class for communicating with a Arduino"""

	# Commands
	FIRE = "FIRE"
	READ_VOLTAGE = "VOLTAGE"
	END = '\n'
	SEP = ','


	def __init__(self, port: str, baudrate: int, timeout: int):
		self.port = port
		self.baudrate = baudrate
		self.timeout = timeout

	def send(self, message: str):
		"""Send a message to the Arduino"""
		print(message)

	def read(self) -> str:
		"""Read a response from the Arduino"""
		print("Reading")

	def test_connection(self):
		"""Test the connection with the Arduino"""

	def connect(self) -> bool:
		"""Connect to the Arduino"""
		print("Connection on")

	def close(self):
		"""Close connection to the Arduino"""
		print("Closing connection")


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
		spi.xfer([self.MSB, x])

class PinIsNotConfigured(Exception):
	pass
