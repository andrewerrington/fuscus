#!/usr/bin/env python3
"""Main program for BrewPi Fuscus temperature controller."""

import logging
logging.basicConfig(filename='fuscus.log', level=logging.DEBUG)

#
# Copyright 2012-2013 BrewPi/Elco Jacobs.
# Copyright 2015 Andrew Errington
#
# This file is part of BrewPi.
# 
# BrewPi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# BrewPi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with BrewPi.  If not, see <http://www.gnu.org/licenses/>.
#


import time
import signal

import AppConfigDefault # FIXME is this needed?

#import piLink
#piLink = piLink.piLink()

import ui

# global class objects static and defined in constants.py
# instantiate and configure the sensors, actuators and controllers we want to use

from constants import *

keepRunning = True

#ValueActuator alarm;
#UI ui;


def killhandle(signum, frame):
	'''Handle shutdown cleanly by stopping main loop.'''
	global keepRunning
	if signum == signal.SIGINT:
		print("SIGINT detected.  Main loop will stop.")
		keepRunning = False
	elif signum == signal.SIGTERM:
		print("SIGTERM detected.  Main loop will stop.")
		keepRunning = False


def setup():
	#resetEeprom = platform_init()	# FIXME: not implemented
    #eepromManager.init()	# FIXME: not implemented
    #ui.init()
	#f,portName=piLink.init()
	print("started")
	logging.debug("started")
	#tempControl.init()
	#settingsManager.loadSettings()	# FIXME No settings manager
	# FIXME The next two lines are temporary code to make things work.
	# They should be done by the settings manager.
	tempControl.loadDefaultSettings()
	tempControl.loadDefaultConstants()

	start = time.time()
	delay = ui.showStartupPage(piLink.portName)
	while (time.time()-start <= delay):
		ui.ticks()
	
	ui.showControllerPage()

	logging.debug("init complete")
	print("init complete")


def loop():
	'''Main loop.'''
	lastUpdate = -1	# initialise at -1 to update immediately

	oldState = None

	spinner = '|/-\\'
	spinindex = 0

	while keepRunning:
		ui.ticks()
		if (time.time() - lastUpdate >= 1.0): # update settings every second
			# round to nearest 1 second boundary to keep in sync with real time	
			lastUpdate = round(time.time())

			tempControl.updateTemperatures()
			tempControl.detectPeaks()
			tempControl.updatePID()
			oldState = tempControl.getState()
			tempControl.updateState()

			if (oldState != tempControl.getState()):
				print("State changed from %s to %s"%(oldState, tempControl.getState()))
				piLink.printTemperatures()	# add a data point at every state transition
			
			tempControl.updateOutputs()
			ui.update()

			# We have two lines free at the bottom of the display.

			# Show local time YYYY-MM-DD hh:mm (16 characters.)
			ui.LCD.printat(0, 5, time.strftime("%Y-%m-%d %H:%M")) 

			# Last character is a spinner to show we haven't crashed
			ui.LCD.print("%s"%spinner[spinindex])
			spinindex = (spinindex + 1) % 4

		#listen for incoming serial connections while waiting to update
		piLink.receive()

		time.sleep(0.05) # Don't hog the processor

	piLink.cleanup()
	ui.LCD.printat(0, 5, "Shutting down.   ")
	ui.update()


if __name__ == "__main__":
	import RPi.GPIO as GPIO
	logging.info('Started')
	signal.signal(signal.SIGTERM, killhandle)
	signal.signal(signal.SIGINT, killhandle)
	setup()
	loop()	# loop() will exit if we get one of the above signals
	heater.off()
	cooler.off()
	print("Stopping threads")
	tempControl.beerSensor.stop()
	tempControl.ambientSensor.stop()
	tempControl.fridgeSensor.stop()
	encoder.stop()
	print("Waiting for threads to finish.")
	tempControl.beerSensor.join()
	tempControl.ambientSensor.join()
	tempControl.fridgeSensor.join()
	encoder.join()
	GPIO.cleanup()
	print("Finished")
	logging.info('Finished')
