#!/usr/bin/env python3

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

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)

class door:
	def __init__(self, pin, invert=False):
		self._pin = pin
		self.inverted = bool(invert)
		
		GPIO.setup(self._pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	@property
	def isOpen(self):
		return bool(GPIO.input(self._pin)^self.inverted)