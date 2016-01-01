#!/usr/bin/env python3
"""Constants and hardware definitions for BrewPi Fuscus."""

#
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

import configparser

import tempControl
import relay
import rotaryEncoder
import pcd8544
import lcd
import door
import Menu
import piLink

# Port for TCP/IP control FIXME: not implemented yet
port = 25518

# GPIO pins (board numbering: GPIO.setmode(GPIO.BOARD))
# Rotary encoder (3 GPIO + 3.3V & GND)
rotary_PB = 5	# Pin 5 has a 1.8k pull-up.  Also used to restart from halt.
rotary_A = 13
rotary_B = 11

# LCD module (Nokia 5110 screen/PCD8544 controller) (6 GPIO + 3.3V & GND)
lcd_RST = 22
lcd_DC = 21
lcd_LED = 12
lcd_DIN = 19	# These three pins are fixed to the hardware SPI module.
lcd_SCLK = 23	# The numbers here are for reference only.
lcd_SCE = 24	# We can see which pins are in use.

# Relay board (2x 240Vac 10A relays) (2 GPIO + 3.3V + 5V + GND)
relay_HOT = 16
relay_COLD = 18

# Door (1 GPIO + GND)
door_pin = 3	# Pin 3 has a 1.8k pull-up

# One-wire bus (implemented by external system) (1 GPIO + 3.3V + GND)
one_wire = 7	# This number is for reference only

# One-wire sensor IDs
config = configparser.ConfigParser()
config.read('fuscus.ini')
sensors = config['sensors']
ID_fridge = sensors.get('fridge')
ID_beer = sensors.get('beer')
ID_ambient = sensors.get('ambient')

if not(ID_fridge):
	raise ValueError("1-wire address of fridge not specified in 'fuscus.ini'.")

if ID_beer == '':
	ID_beer = None
	
if ID_ambient == '':
	ID_ambient = None

print("Fridge sensor : %s"%ID_fridge)
print("Beer sensor   : %s"%ID_beer)
print("Ambient sensor: %s"%ID_ambient)

# Unused GPIOs for reference
ser_TX = 8
ser_RX = 10
free_1 = 15
free_2 = 26

# Backlight control
# FIXME Unused
BACKLIGHT_AUTO_OFF_SECONDS = 120
BACKLIGHT_DIM_SECONDS = 30

BACKLIGHT_BRIGHT_LEVEL = 50
BACKLIGHT_DIM_LEVEL = 20

# Global objects for our hardware devices
DOOR = door.door(door_pin)

encoder = rotaryEncoder.rotaryEncoder(rotary_A, rotary_B, rotary_PB)
encoder.start()

heater = relay.relay(relay_HOT, invert = True)
cooler = relay.relay(relay_COLD, invert = True)

LCD_hardware = pcd8544.pcd8544(DC = lcd_DC, RST = lcd_RST)

# Nokia LCD has 17 chars by 6 lines, but original display and web display
# show 20 chars by 4 lines.
LCD = lcd.lcd(lines = 6, chars = 20, hardware = LCD_hardware)

tempControl = tempControl.tempController(ID_fridge, ID_beer, ID_ambient,
							cooler = cooler, heater = heater, door = DOOR)

piLink = piLink.piLink(tempControl=tempControl)

menu = Menu.Menu(encoder=encoder, tempControl=tempControl, piLink=piLink)