import serial
import serial.tools.list_ports
import time


class Arduino:
	"""Class for communicating with a Arduino"""

	HEADER = "1"

	# Commands
	FIRE = "FIRE"
	READ_VOLTAGES = "VOLTAGE"
	ON = "ON"
	OFF = "OFF"
	HV = "HV"
	DRAIN = "DRAIN"
	COUNTDOWN = "COUNTDOWN"
	CHARGE = "CHARGE"
	DISPLAY_CHARGE = "DISPLAY_CHARGE"
	TEST = "TEST"
	SENSORS = "SENSORS"
	ABORT = "ABORT"
	BLINK = "BLINK"

	# Expected responses
	OK = "OK"			# A good test
	HV_ON = "HV ON"		# HV sucessfully turned on
	HV_OFF = "HV OFF"	# HV sucessfully turned off
	DRAIN_RESPONSE = "Drain pins set to: "
	COUNTDOWN_RESPONSE = "COUNTDOWN STARTED"
	CHARGE_RESPONSE = "CHARGING COILGUN"
	DISPLAY_CHARGE_RESPONSE = "DISPLAY SET TO: "
	HV_RESPONSE = "HV pins set to: "
	SENSOR_RESPONSE = "Sensors are: "
	ABORT_RESPONSE = "ABORTING"
	BLINK_RESPONSE = "BLINKING"

	# Communication chars
	END = '\n'
	SEP = ','


	def __init__(self, port: str, baudrate: int, timeout: int=10):
		self.port = port
		self.baudrate = baudrate
		self.timeout = timeout

		self.arduino = None

	def send(self, message: str):
		"""Send a message to the Arduino"""
		self.arduino.write(bytes(Arduino.HEADER, 'utf-8'))
		ready = self.read()
		if ready == Arduino.OK:
			self.arduino.write(bytes(message + Arduino.END, 'utf-8'))
		else:
			self.send(message)

	def read(self) -> str:
		"""Read a response from the Arduino"""
		response = ""
		while True:
			char = self.arduino.read().decode('utf-8')
			if Arduino.END == char:
				break
			elif char:
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
		try:
			self.arduino = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
		except serial.SerialException:
			print(f"Could not connect to port {self.port} as it does not exist or it is busy. Try one of these instead:")
			print('\n'.join([comport.device for comport in serial.tools.list_ports.comports()]))
			quit()
		self.flush_serial()
		time.sleep(1)
		if not self.test_connection():
			self.close()
			return False
		return True

	def flush_serial(self):
		"""Clear Serial buffer"""
		self.arduino.reset_input_buffer()
		self.arduino.reset_output_buffer()

	def close(self):
		"""Close connection to the Arduino"""
		self.arduino.close()


class CommunicationError(Exception):
	pass
