#!/usr/bin/env python3
"""Simple class for turning a relay on or off."""

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


import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)


class relay:
    """Simple class for controlling a relay."""

    def __init__(self, pin, invert=False, init=False):
        self._pin = pin  # GPIO pin number (board numbering)
        self.inverted = bool(invert)  # Is the hardware active low (True)
        # or active high (False)
        self.state = bool(init)  # We can read this class variable to get
        # the current state

        # Configure the I/O pin and set its initial state.
        GPIO.setup(self._pin, GPIO.OUT, initial=init ^ invert)

    def set_output(self, state):
        """Set output pin based on desired state and hardware inversion."""
        self.state = bool(state)
        GPIO.output(self._pin, self.state ^ self.inverted)

    def on(self):
        """Turn relay on."""
        self.set_output(True)

    def off(self):
        """Turn relay off."""
        self.set_output(False)
