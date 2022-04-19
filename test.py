from communication import Arduino, Potentiometer
from coilgun import Coil, Coilgun
import config
import yaml
import time
from utils import print_data
import RPi.GPIO as GPIO


def test_coilgun():
	arduino = Arduino(config.port, config.baudrate, config.timeout)

	print("Testing communication with the Arduino...")
	if not arduino.connect():
		print("Failed to connect to the Arduino.")
		print("Quiting...")
	print("Communication sucessfull!")

	potentiometer = Potentiometer()

	with open("coils.yaml", "r") as yaml_file:
		coils_dict = yaml.safe_load(yaml_file)

	sorted_coils = sorted(coils_dict.keys())

	coils = [Coil.from_dict(coils_dict[coil]) for coil in sorted_coils]

	
	coilgun = Coilgun(coils[:1], arduino, potentiometer, config.HV_pin, config.drain_pin, config.projectile_diameter)
	
	while True:
		coilgun.HV_OFF()
		print("DRAIN")
		time.sleep(3)
		print("CHARGE")
		coilgun.HV_ON()
		time.sleep(3)



def test_pot():
	potentiometer = Potentiometer()
	pin = 13
	
	GPIO.setup(pin, GPIO.OUT)

	# Pull selector pin LOW before transfering data
	GPIO.output(pin, GPIO.LOW)
	potentiometer.set(250)
	GPIO.output(pin, GPIO.HIGH)

	GPIO.cleanup()


if __name__ == '__main__':
	test_coilgun()
    