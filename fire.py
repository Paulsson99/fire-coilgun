from communication import Arduino, Potentiometer
from coilgun import Coil, Coilgun
import yaml


# Pins
HV_pin = 4
drain_pin = 5

# Data
projectile_diameter = 8.8e-3


def main():
	arduino = Arduino.start("/dev/ttyACM0", 9600, 10)

	if not arduino.connect():
		print("Failed to connect to the Arduino.")
		print("Quiting...")

	potentiometer = Potentiometer()

	with open("coils.yaml", "r") as yaml_file:
		coils_dict = yaml.safe_load(yaml_file)

	sorted_coils = sorted(coils_dict.keys())

	coils = [Coil.from_dict(coils_dict[coil]) for coil in sorted_coils]

	try:
		coilgun = Coilgun(coils, arduino, potentiometer, HV_pin, drain_pin, projectile_diameter)
	finally:
		coilgun.close()

if __name__ == '__main__':
	main()