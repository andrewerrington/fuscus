#!/usr/bin/env python3

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

import math

from constants import *
from tempControl import MODES, STATES, MIN_COOL_ON_TIME, MIN_HEAT_ON_TIME
import ticks


# Constant strings used multiple times
STR_Beer_ = "Beer "
STR_Fridge_ = "Fridge "
STR_Const_ = "Const."
STR_Cool = "Cool"
STR_Heat = "Heat"
STR_ing_for = "ing for"
STR_Wait_to_ = "Wait to "
STR__time_left = " time left"
STR_empty_string = ""


# Other constants
LCD_FLAG_DISPLAY_ROOM = 0x01
LCD_FLAG_ALTERNATE_ROOM = 0x02

# Variables.  #FIXME consider making a class, with these as class variables
flags = LCD_FLAG_ALTERNATE_ROOM
stateOnDisplay = None


def init():
	#stateOnDisplay = 0xFF; // set to unknown state to force update
	#flags = LCD_FLAG_ALTERNATE_ROOM
	#lcd.init(); // initialize LCD
	#lcd.begin(20, 4)
	#lcd.clear()
	pass	#FIXME this code needs to do something. Probably.


def printStationaryText():
	"""Print the stationary text on the lcd."""
	
	LCD.printat(0, 0, "Mode   ")
	LCD.printat(0, 1, STR_Beer_)

	LCD.printat(0, 2, "Room  " if (flags & LCD_FLAG_DISPLAY_ROOM) else STR_Fridge_)
	
	# The Nokia screen is not wide enough for this, but the
	# web interface will show it
	printDegreeUnit(18, 1)
	printDegreeUnit(18, 2)


def printDegreeUnit(x, y):
	"""Print degree sign + temp unit."""
	LCD.cursor(x,y)
	LCD.print('°')
	LCD.print(tempControl.cc.tempFormat)


def printMode():
	"""Print mode on the right location on the first line, after "Mode   "."""
	LCD.printat(7, 0, ' '*13)
	LCD.cursor(7,0)

	if (tempControl.getMode() == MODES['MODE_FRIDGE_CONSTANT']):
		LCD.print(STR_Fridge_)
		LCD.print(STR_Const_)
			
	elif (tempControl.getMode() == MODES['MODE_BEER_CONSTANT']):
		LCD.print(STR_Beer_)
		LCD.print(STR_Const_)
			
	elif (tempControl.getMode() == MODES['MODE_BEER_PROFILE']):
		LCD.print(STR_Beer_)
		LCD.print("Profile")
			
	elif (tempControl.getMode() == MODES['MODE_OFF']):
		LCD.print("Off")
			
	elif (tempControl.getMode() == MODES['MODE_TEST']):
		LCD.print("** Testing **")
			
	else:
		LCD.print("Invalid mode")
			
	#lcd.printSpacesToRestOfLine();


def printState():
	"""Print the current state on the last line of the LCD."""

	global stateOnDisplay

	time = None
	state = tempControl.getDisplayState()
	
	if (state != stateOnDisplay):	# only print static text when state has changed
		stateOnDisplay = state
		# Reprint state and clear rest of the line
		
		LCD.printat(0, 3, ' '*20)	# Actually, clear line then overprint
		
		part1 = STR_empty_string
		part2 = STR_empty_string
		
		if (state == STATES['IDLE']):
			part1 = "Idl"
			part2 = STR_ing_for
		elif (state == STATES['WAITING_TO_COOL']):
			part1 = STR_Wait_to_
			part2 = STR_Cool
		elif (state == STATES['WAITING_TO_HEAT']):
			part1 = STR_Wait_to_
			part2 = STR_Heat
		elif (state == STATES['WAITING_FOR_PEAK_DETECT']):
			part1 = "Waiting for peak"
		elif (state == STATES['COOLING']):
			part1 = STR_Cool
			part2 = STR_ing_for
		elif (state == STATES['HEATING']):
			part1 = STR_Heat
			part2 = STR_ing_for
		elif (state == STATES['COOLING_MIN_TIME']):
			part1 = STR_Cool
			part2 = STR__time_left
		elif (state == STATES['HEATING_MIN_TIME']):
			part1 = STR_Heat
			part2 = STR__time_left
		elif (state == STATES['DOOR_OPEN']):
			part1 = "Door open"
		elif (state == STATES['STATE_OFF']):
			part1 = "Temp. control OFF"
		else:
			part1 = "Unknown status!"
		
		LCD.printat(0, 3, part1)
		LCD.print(part2)
		#lcd.printSpacesToRestOfLine();

	sinceIdleTime = tempControl.timeSinceIdle()
	
	if (state == STATES['IDLE']):
		time = min(tempControl.timeSinceCooling(), tempControl.timeSinceHeating())
	elif state in (STATES['COOLING'], STATES['HEATING']):
		time = sinceIdleTime
	elif (state == STATES['COOLING_MIN_TIME']):
		time = MIN_COOL_ON_TIME - sinceIdleTime
	elif (state == STATES['HEATING_MIN_TIME']):
		time = MIN_HEAT_ON_TIME - sinceIdleTime
	elif state in (STATES['WAITING_TO_COOL'], STATES['WAITING_TO_HEAT']):
		time = tempControl.getWaitTime()

	if (time is not None):
		minutes = time / 60
		hours = minutes / 60
		# Nokia LCD is 17 characters wide, so bring nnmnn
		# 3 characters left by padding with spaces on the
		# right so we can see.
		printString="%dm%02d   "%(minutes, time%60)

		# If we have hours, then mnn seconds will not be
		# visible on LCD, but will be visible on web interface.
		if (int(hours) != 0):
			printString="%2dh%02dm%02d"%(hours, minutes%60, time%60)

		LCD.printat(20-len(printString), 3, printString)


def printAllTemperatures():
	"""Print all temperatures on the LCD."""

	global flags

	# alternate between beer and room temp
	if (flags & LCD_FLAG_ALTERNATE_ROOM):
	#	bool displayRoom = ((ticks.seconds()&0x08)==0) && !BREWPI_SIMULATE && tempControl.ambientSensor->isConnected()
		displayRoom = (((int(ticks.seconds())&0x04)==0)
				 and tempControl.ambientSensor is not None)
		if (displayRoom ^ ((flags & LCD_FLAG_DISPLAY_ROOM)!=0)):	# transition
			flags = (flags | LCD_FLAG_DISPLAY_ROOM) if displayRoom else (flags & ~LCD_FLAG_DISPLAY_ROOM)
			printStationaryText()
	
	printBeerTemp()
	printBeerSet()
	printFridgeTemp()
	printFridgeSet()


def printBeerTemp():
	printTemperatureAt(6, 1, tempControl.getBeerTemp())


def printBeerSet():
	printTemperatureAt(12, 1, tempControl.getBeerSetting())


def printFridgeTemp():
	printTemperatureAt(6,2, tempControl.ambientSensor.temperature
					if (flags & LCD_FLAG_DISPLAY_ROOM)
					else tempControl.getFridgeTemp())


def printFridgeSet():
	fridgeSet = tempControl.getFridgeSetting()
	if (flags & LCD_FLAG_DISPLAY_ROOM):	# beer setting is not active
		fridgeSet = None
	printTemperatureAt(12, 2, fridgeSet)


def printTemperatureAt(x, y, temp):
	LCD.cursor(x,y)
	printTemperature(temp)


def printAt(x, y, s):
	LCD.printat(x,y,s)


def printTemperature(temp):
	if (temp is None) or math.isnan(temp): #(isDisabledOrInvalid(temp)):
		LCD.print(" --.-")
		return

	LCD.print("%5.1f"%temp)


def setDisplayFlags(newFlags):
	
	global flags
	
	flags = newFlags
	printStationaryText()
	printAllTemperatures()


def getDisplayFlags():
	return flags


def printAll():	# FIXME: This doesn't seem to be used.
	printStationaryText()
	printState()
	printAllTemperatures()
	printMode()


def update():
	'''Call the update() function to copy the display contents to the hardware.'''
	LCD.update()


#def resetBacklightTimer():
#	lcd.resetBacklightTimer()


#def updateBacklight():
#	lcd.updateBacklight()
