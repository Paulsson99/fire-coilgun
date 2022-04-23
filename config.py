# Data
projectile_diameter = 8.8e-3

# Arduino
port = "/dev/cu.usbmodem14201" # To list do: import serial.tools.list_ports; print([comport.device for comport in serial.tools.list_ports.comports()])
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
