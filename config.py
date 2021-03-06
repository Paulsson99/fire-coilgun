# Projectile
# projectile_diameter = 8.8e-3 	# [m]
# projectile_mass = 3.0e-3 		# [kg]
projectile_diameter = 16e-3 	# [m]
projectile_mass = 2.3e-3 		# [kg]

# Arduino
port = "/dev/cu.usbmodem14201"
baudrate = 115200
timeout = 10            # [s]

# Logger
import logging

# File logger
logfile = "log.txt"
filemode = 'w'
file_logger_level = logging.DEBUG
file_logger_format = '%(asctime)s : %(name)s : %(levelname)s : %(message)s'

# Console logger
console_logger_level = logging.INFO
console_logger_format = '%(levelname)s : %(message)s'

# Data logging
data_logging_path = "data_loggs/friction_test/data"
