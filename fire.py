from communication import Arduino
from coilgun import Coil, Coilgun
import config
import yaml
import time
from utils import print_data
import logging

import numpy as np
import pandas as pd
from datetime import datetime
import os

# For logging of a shot
# Number of windings on a coil
windings = [100, 100, 100, 100, 100, 100, 100]
# Position relative sensor [mm] (end of sensor to start of coil)
positions = [1, 1, 1, 1, 1, 1, 1]


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

def manual_fire(coilgun: Coilgun):
	"""Fire the coilgun manualy"""
	coilgun.ON()
	try: 
		while True:
			time.sleep(1)
			print_data(coilgun.READ_VOLTAGES(), units='V')
	except KeyboardInterrupt:
		pass
	# Countdown
	for i in range(3):
		time.sleep(1)
		print(3-i)
	time.sleep(1)
	print("FIRE!!!")

	fire_voltages = np.array(coilgun.READ_VOLTAGES())
	velocities, trigger_times = coilgun.FIRE()

	coil_efficiency, total_efficiency = coilgun.efficiency(fire_voltages, velocities)
	coil_efficiency = np.array(coil_efficiency)

	print_data(fire_voltages, units='V', prefix='Coilgun fired at: ')
	print_data(velocities, units='m/s', prefix='Projectile velocity was: ')
	print_data(coil_efficiency*100, units=r'%', prefix="Efficiency for all the coils was: ")
	print(f"Total efficiency was {total_efficiency*100:.2f}%")

	log_shot(
		filename=config.data_logging_path,
		voltages=fire_voltages, 
		velocities=velocities, 
		efficiencies=total_efficiency,
		trigger_times=trigger_times
	)

	time.sleep(1)
	after_fire_voltages = np.array(coilgun.READ_VOLTAGES())

	# Drain all CBs that are safe to drain
	coilgun.DRAIN_CB(after_fire_voltages < coilgun.MAX_VOLTAGE_FOR_SAFE_DRAIN)

	time.sleep(1)
	after_drain_voltages = np.array(coilgun.READ_VOLTAGES())

	if np.any(after_drain_voltages > coilgun.MAX_VOLTAGE_FOR_SAFE_DRAIN):
		print("Warning!!! Not all CBs are empty!")
		print_data(after_drain_voltages, units='V', prefix="The voltages are: ")
		if input("Empty CBs anyway (y/n): ") == 'y':
			coilgun.DRAIN_ALL(True)
		else:
			print_data(after_drain_voltages, units='V', prefix="Fire with coilgun at: ")
			input("FIRE!!!")
			coilgun.FIRE()
			quit()
	
	coilgun.OFF()

def fire(coilgun: Coilgun):
	"""Fire the coilgun"""
	coilgun.OFF()

	voltages = get_voltages(len(coilgun))
	print_data(voltages, units='V', prefix='Voltages set to: ')

	if not input('Press enter to start charging (q to quit): ') == '':
		return
	
	# Start charging
	try:
		coilgun.CHARGE_COILGUN(voltages)
	except KeyboardInterrupt:
		# Manually stop the charge
		coilgun.HV_ALL(HV_state=False)

	print("Coilgun is ready to FIRE!")
	if not input("Press enter to FIRE! (q to quit): ") == '':
		return

	# Countdown
	for i in range(3):
		time.sleep(1)
		print(3-i)
	time.sleep(1)
	print("FIRE!!!")

	fire_voltages = np.array(coilgun.READ_VOLTAGES())
	velocities = coilgun.FIRE()

	print_data(velocities, units='m/s', prefix='Projectile velocity was: ')

	time.sleep(1)
	after_fire_voltages = np.array(coilgun.READ_VOLTAGES())

	# Drain all CBs that are safe to drain
	coilgun.DRAIN_CB(after_fire_voltages < coilgun.MAX_VOLTAGE_FOR_SAFE_DRAIN)

	if np.any(after_fire_voltages > coilgun.MAX_VOLTAGE_FOR_SAFE_DRAIN):
		print("Warning!!! Not all CBs are empty!")
		print_data(after_fire_voltages, units='V', prefix="The voltages are: ")
		if input("Empty CBs anyway (y/n): ") == 'y':
			coilgun.DRAIN_ALL(True)
		else:
			coilgun.FIRE()
			quit()
	
	coilgun.OFF()


def log_shot(filename, voltages, velocities, efficiencies, trigger_times):
	"""Log a shot"""
	data = {
		'Velocities [m/s]': velocities,
		'Voltages [V]': voltages,
		'Efficiency [%]': efficiencies * 100,
		'Windings [-]': windings,
		'Positions [mm]': positions,
		'Trigger times [s]': trigger_times
	}
	df = pd.DataFrame(data=data)

	df.to_csv(filename + "_" + datetime.now().strftime('%d-%m-%Y %H-%M-%S') + '.csv', mode='w', header=True)

def main():
	# Start communication with the Arduino
	arduino = Arduino(config.port, config.baudrate, config.timeout)

	print("Testing communication with the Arduino...")
	if not arduino.connect():
		print("Failed to connect to the Arduino.")
		print("Quiting...")
	print("Communication sucessfull!")

	# Load coils from config and sort them (named coil1, coil2, ...)
	with open("coils.yaml", "r") as yaml_file:
		coils_dict = yaml.safe_load(yaml_file)
	sorted_coils = sorted(coils_dict.keys())
	coils = [Coil.from_dict(coils_dict[coil]) for coil in sorted_coils]

	# Create a logger
	logger = logging.getLogger('Coilgun')
	logger.setLevel(logging.DEBUG)

	# Add console logging to the logger
	c_handler = logging.StreamHandler()
	c_handler.setLevel(config.console_logger_level)
	c_format = logging.Formatter(config.console_logger_format)
	c_handler.setFormatter(c_format)
	logger.addHandler(c_handler)

	# Add file logger to the logger
	f_handler = logging.FileHandler(filename=config.logfile, mode=config.filemode)
	f_handler.setLevel(config.file_logger_level)
	f_format = logging.Formatter(config.file_logger_format)
	f_handler.setFormatter(f_format)
	logger.addHandler(f_handler)

	coilgun = Coilgun(coils, arduino, config.projectile_diameter, config.projectile_mass, logger=logger)

	try:
		while True:
			if input("Press enter to start fire sequence (q to quit): ") == '':
				# fire(coilgun)
				manual_fire(coilgun)
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