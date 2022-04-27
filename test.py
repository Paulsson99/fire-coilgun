from communication import Arduino
from coilgun import Coil, Coilgun
import config
import yaml
import time
import logging
from utils import print_data


def test_decorator(func):
	def test_wrapper(*args, **kwargs):
		print(f"Testing {func.__name__[5:]}. Go to the next test by pressing ctrl+C")
		try:
			while True:
				func(*args, **kwargs)
		except KeyboardInterrupt:
			pass
	return test_wrapper


def test_coilgun():
	arduino = Arduino(config.port, config.baudrate, config.timeout)

	print("Testing communication with the Arduino...")
	if not arduino.connect():
		print("Failed to connect to the Arduino.")
		print("Quiting...")
	print("Communication sucessfull!")

	with open("coils.yaml", "r") as yaml_file:
		coils_dict = yaml.safe_load(yaml_file)

	sorted_coils = sorted(coils_dict.keys())

	coils = [Coil.from_dict(coils_dict[coil]) for coil in sorted_coils]

	# Create a logger
	logger = logging.getLogger('Coilgun')
	# Add console logging to the logger
	c_handler = logging.StreamHandler()
	c_handler.setLevel(logging.DEBUG)
	c_format = logging.Formatter('%(name)s : %(levelname)s : %(message)s')
	c_handler.setFormatter(c_format)
	logger.addHandler(c_handler)
	logger.setLevel(logging.DEBUG)

	
	coilgun = Coilgun(coils, arduino, config.projectile_diameter, config.projectile_mass, logger=logger)

	# Turn ON all coils so they can be tested
	# for coil in coilgun:
	# 	coil.turn_on()

	# coilgun.CHARGE_COILGUN([150])
	# coilgun.FIRE()
	# test_FIRE(coilgun)

	# coilgun.ON()
	# try: 
	# 	while True:
	# 		time.sleep(1)
	# 		print_data(coilgun.READ_VOLTAGES(), units='V')
	# except KeyboardInterrupt:
	# 	pass

	# coilgun.DRAIN_ALL(True)

	# try: 
	# 	while True:
	# 		time.sleep(1)
	# 		print_data(coilgun.READ_VOLTAGES(), units='V')
	# except KeyboardInterrupt:
	# 	pass

	test_MAIN_HV(coilgun)
	for coil in coilgun:
		test_DRAIN(coilgun, coil)
	for coil in coilgun:
		test_HV(coilgun, coil)
	test_READ_VOLTAGE(coilgun)
	test_FIRE(coilgun)
	test_SENSORS(coilgun)

	coilgun.shutdown()

@test_decorator
def test_MAIN_HV(coilgun: Coilgun):
	"""Test turning main HV ON/OFF"""
	coilgun.MAIN_HV_ON()
	time.sleep(1)
	coilgun.MAIN_HV_OFF()
	time.sleep(1)

@test_decorator
def test_DRAIN(coilgun: Coilgun, coil: Coil):
	"""Test turning ON/OFF the drain for a coil"""
	coils_to_turn_ON_OFF = [True] * len(coilgun)
	coils_to_turn_ON_OFF[coil.id] = False

	coilgun.DRAIN_CB(coils_to_turn_ON_OFF)
	time.sleep(1)
	coilgun.DRAIN_ALL(True)
	time.sleep(1)

@test_decorator
def test_HV(coilgun: Coilgun, coil: Coil):
	"""Test turning ON/OFF the HV for a coil"""
	coils_to_turn_ON_OFF = [False] * len(coilgun)
	coils_to_turn_ON_OFF[coil.id] = True

	coilgun.HV_2_CB(coils_to_turn_ON_OFF)
	time.sleep(1)

	coilgun.HV_ALL(False)
	time.sleep(1)

@test_decorator
def test_READ_VOLTAGE(coilgun: Coilgun):
	"""Test reading the voltage for all the coils"""
	print(coilgun.READ_VOLTAGES())
	time.sleep(1)

@test_decorator
def test_FIRE(coilgun: Coilgun):
	"""Test firering the coilgun"""
	vel, trigger = coilgun.FIRE()
	print(vel)
	print(trigger)
	time.sleep(1)

@test_decorator
def test_SENSORS(coilgun: Coilgun):
	"""Test the sensors"""
	print(coilgun.SENSORS())
	time.sleep(1)

if __name__ == '__main__':
	test_coilgun()
    