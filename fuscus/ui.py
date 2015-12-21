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

import displayLCD as display

from constants import *

# Not sure where to put this at the moment.  It's a utility
# to get our IP address.
# http://stackoverflow.com/a/24196955
import socket
import fcntl
import struct

def get_ip_address(ifname):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	return socket.inet_ntoa(fcntl.ioctl(
		s.fileno(), 0x8915,  # SIOCGIFADDR
		struct.pack(b'256s', bytes(ifname[:15],'utf-8'))
	)[20:24])


def init():
	#turn on the buzzer for a short time
	#initialise the hardware
	#initialise the rotary encoder
	pass

def showStartupPage(port_name):
	LCD.clear()
	LCD.println(" BrewPi - Fuscus ")
	LCD.println("  version 0.1.0")
	LCD.println(port_name)
	
	try:
		eth0_addr=get_ip_address('eth0')
	except:
		eth0_addr=''

	try:
		wlan0_addr=get_ip_address('wlan0')
	except:
		wlan0_addr=''

	if wlan0_addr!='':
		LCD.println(wlan0_addr)
	elif eth0_addr!='':
		LCD.println(eth0_addr)
	else:
		LCD.println('No network')

	LCD.backlight(BACKLIGHT_BRIGHT_LEVEL)
	LCD.update()
	# Return value is how long to leave startup page (in seconds)
	return 5
		
def showControllerPage():
	LCD.clear()
	display.printStationaryText()
	display.printState()
	LCD.update()

def update():
	# update the lcd for the chamber being displayed
	display.printState()
	display.printAllTemperatures()
	display.printMode()
	#display.updateBacklight(); 
	LCD.update()
	
def ticks():
	# Do UI housekeeping
	pass