from communication import Arduino, Potentiometer
from coilgun import Coil, Coilgun
import config
import yaml
import time
from utils import print_data

import numpy as np


def get_voltages(coils: int):
	""""Get voltages from user"""
	voltages = []
	print("Please give voltages to charge all the coils to:")
	for i in range(coils):
		volt = None
		while volt is None:
			input_volt = input(f"Voltage for coil {i+1}: ")
			try:
				volt = float(input_volt)
			except ValueError:
				print(f"Could not convert input {input_volt} to a float... Try again")
		voltages.append(volt)
	return voltages

def fire(coilgun: Coilgun):
	"""Fire the coilgun"""
	coilgun.reset()

	voltages = get_voltages(len(coilgun))
	set_voltages = coilgun.set_voltages(voltages)
	print_data(set_voltages, units='V', prefix='Voltages set to: ')

	if not input('Press enter to start charging (q to quit): ') == '':
		return
	
	# Start charging
	coilgun.charge()

	while not coilgun.ready2fire():
		current_voltages = coilgun.read_voltages()
		print(current_voltages)

	print("Coilgun is ready to FIRE!")
	if not input("Press enter to FIRE! (q to quit): ") == '':
		coilgun.stop_charge()
		return

	# Countdown
	for i in range(3):
		time.sleep(1)
		print(3-i)
	coilgun.HV_OFF()
	time.sleep(1)
	print("FIRE!!!")

	fire_voltages = np.array(coilgun.read_voltages())
	velocities = coilgun.fire()

	time.sleep(1)
	after_fire_voltages = np.array(coilgun.read_voltages())

	print_data(velocities, units='m/s', prefix='Projectile velocity was: ')

	if np.any(after_fire_voltages > 30):
		print("Warning!!! Not all CBs are empty!")
		print_data(after_fire_voltages, units='V', prefix="The voltages are: ")
		if input("Empty CBs anyway (y/n): ") == 'y':
			coilgun.DRAIN_CB()
		else:
			coilgun.fire()
			quit()
	
	coilgun.stop_charge()


def main():
	# Start communication with the Arduino
	arduino = Arduino(config.port, config.baudrate, config.timeout)

	print("Testing communication with the Arduino...")
	if not arduino.connect():
		print("Failed to connect to the Arduino.")
		print("Quiting...")
	print("Communication sucessfull!")

	# Create potentiometer
	potentiometer = Potentiometer()

	# Load coils from config and sort them (named coil1, coil2, ...)
	with open("coils.yaml", "r") as yaml_file:
		coils_dict = yaml.safe_load(yaml_file)
	sorted_coils = sorted(coils_dict.keys())
	coils = [Coil.from_dict(coils_dict[coil]) for coil in sorted_coils]

	coilgun = Coilgun(coils, arduino, potentiometer, config.HV_pin, config.drain_pin, config.projectile_diameter)

	try:
		while True:
			if input("Press enter to start fire sequence (q to quit): ") == '':
				fire(coilgun)
			else:
				print("Quiting...")
				break
	finally:
		# Alwasy turn off HV and drain the CBs
		# coilgun.shutdown()
		pass
	coilgun.shutdown()

if __name__ == '__main__':
	main()