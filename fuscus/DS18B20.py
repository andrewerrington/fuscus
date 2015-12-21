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


# Threaded class to read DS18B20 sensor
# You can read .temperature as often as you like, but it's only updated
# every samplePeriod seconds (and the driver takes about 800ms to
# return a value).
# Return value is a float, temperature in degrees C,
# or None if the sensor can not be read.


# How many times to try reading a stuck sensor before giving up.
RETRY_LIMIT = 10


class DS18B20(threading.Thread):

	def __init__(self, deviceID, samplePeriod = 1):
		"""deviceID is the 1-wire address.  samplePeriod is in seconds."""
		threading.Thread.__init__(self)

		self.deviceID = deviceID
		self.filename =  "/sys/bus/w1/devices/%s/w1_slave"%deviceID

		self.samplePeriod = samplePeriod
		
		# Initialise temperature to None, meaning no reading is available
		self.temperature = None

		self.running = False


	def run(self):
		
		self.running = True

		while(self.running):
			# update temperature every time around this loop

			retries = 0	# Sometimes the sensor gets 'stuck'
			
			while True:
				# Attempt to read the sensor, and deal with common errors.
				
				try:
					tfile = open(self.filename)
					text = tfile.read()
					tfile.close
				except: 
					self.temperature = None
					print("Could not open '%s'"%self.deviceID)
					break

				if text.split("\n")[0][-3:] == "YES":
					temperature = float(text.split("\n")[1].split(" ")[9][2:])/1000
				else:
					self.temperature = None
					print("Error reading '%s'"%self.deviceID)
					break

				if temperature == 85.0:
					# A common error condition.  If your application
					# encounters this temperature genuinely in your
					# environment consider removing this test.
					if retries < RETRY_LIMIT:
						print("Discarding 85.0 reading.  Re-reading '%s'"%device)
						retries += 1
						continue
					else:
						self.temperature = None
						print("Sensor '%s' stuck on 85.0 after %s retries.  Giving up."%(self.deviceID,RETRY_LIMIT))
						break
				
				self.temperature = temperature
				break

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
			print(tempsensor.temperature)	# Result is float in degrees C,
											# or None for error
			time.sleep(1) 	# You can read it as often as you like, but it
							# will only change every samplePeriod seconds.

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