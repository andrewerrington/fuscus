#!/usr/bin/env python3
"""Threaded class to read DS18B20 temperature sensors."""

#
# Copyright 2015 Andrew Errington
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import threading
import time


# How many times to try reading a stuck sensor before giving up.
RETRY_LIMIT = 10

class DS18B20(threading.Thread):
	"""Threaded class to read DS18B20 sensor.
	
	You can read .temperature as often as you like, but it's only updated
	every samplePeriod seconds (and the driver takes about 800ms to return
	a value).
	Return value is a float, temperature in degrees C,
	or None if the sensor can not be read.
	
	A special deviceID of None is allowed.  This deviceID will always
	return a temperature of None.
	"""

	def __init__(self, deviceID, samplePeriod = 1):
		"""deviceID is the 1-wire address.  samplePeriod is in seconds."""
		threading.Thread.__init__(self)

		self.deviceID = deviceID

		self.samplePeriod = samplePeriod
		
		# Initialise temperature to None, meaning no reading is available
		self.temperature = None

		self.running = False


	def run(self):

		self.running = True

		while (self.running):
			# update temperature every time around this loop

			retries = 0	# Sometimes the sensor gets 'stuck'

			temperature = None	# Default temperature until we get a new one

			# If deviceID is None, don't bother reading it.
			while self.deviceID is not None:
				# Attempt to read the sensor, and deal with common errors.

				filename =  "/sys/bus/w1/devices/%s/w1_slave"%self.deviceID

				try:
					tfile = open(filename)
					text = tfile.read()
					tfile.close
				except: 
					print("Could not open '%s'"%filename)
					break

				if text.split("\n")[0][-3:] == "YES":
					# New data is available.  Extract it from the string.
					new_temperature = float(text.split("\n")[1].split(" ")[9][2:])/1000
				else:
					# Reading the sensor did not return "YES".
					# Let's try again a few times.
					print("Sensor '%s' did not return 'YES'"%self.deviceID)
					print("Sensor returned '%s'"%text)
					if retries < RETRY_LIMIT:
						print("Re-reading '%s'"%self.deviceID)
						retries += 1
						continue
					else:
						print("Sensor '%s' did not return 'YES' after %s retries.  Giving up."%(self.deviceID,RETRY_LIMIT))
						break

				if new_temperature == 85.0:
					# A common error condition.  If your application
					# encounters this temperature genuinely in your
					# environment consider removing this test.
					if retries < RETRY_LIMIT:
						print("Discarding 85.0 reading.  Re-reading '%s'"%self.deviceID)
						retries += 1
						continue
					else:
						print("Sensor '%s' stuck on 85.0 after %s retries.  Giving up."%(self.deviceID,RETRY_LIMIT))
						break
				else:
					# new temperature is acceptable
					temperature = new_temperature

				break

			self.temperature = temperature
			time.sleep(self.samplePeriod)


	def stop(self):
		self.running = False



if __name__ == "__main__":

	# Simple test code.  A sensor must be present,
	# and the W1 driver must be working
	tempsensor = DS18B20("28-0315535f7bff") # Insert your device ID here

	try:
		print("Starting %s"%tempsensor.deviceID)
		tempsensor.start()

		while(True):
			time.sleep(1) 	# You can read the sensor as often as you like,
							# but it only changes every samplePeriod seconds.
			print(tempsensor.temperature)	# Result is float in degrees C,
											# or None for error

	except KeyboardInterrupt:
		print("Ctrl-C")

	except:
		print("Temperature sensor error:", sys.exc_info()[0])
		raise

	finally:
		print("Stopping %s"%tempsensor.deviceID)
		tempsensor.stop()
		print("Waiting for %s to finish."%tempsensor.deviceID)
		tempsensor.join()
	
	print("Done")