from communication import Arduino, Potentiometer
from coilgun import Coil, Coilgun


arduino = Arduino.start("dev/", 9600, 10)

arduino.send("test")
arduino.read()