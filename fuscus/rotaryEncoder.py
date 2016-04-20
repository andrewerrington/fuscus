#!/usr/bin/env python3
"""Threaded rotary encoder driver."""

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

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)


class rotaryEncoder(threading.Thread):
	"""A threaded rotary encoder driver.  Read .pos or .pushed any time."""
	
	def __init__(self, A, B, PB, dummy = False):
		"""Initialise hardware.  A and B are the quadrature pins, PB is the pushbutton."""
		
		threading.Thread.__init__(self)
		
		self._A = A
		self._B = B
		self._PB = PB

		self._dummy = dummy	# Special flag for no physical hardware
		
		if not self._dummy:
			GPIO.setup(self._PB, GPIO.IN, pull_up_down=GPIO.PUD_UP)
			GPIO.setup(self._A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
			GPIO.setup(self._B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

			# Initialise internal state of Gray code
			self._state = GPIO.input(self._B)<<3 | GPIO.input(self._A)<<2 | \
					GPIO.input(self._B)<<1 | GPIO.input(self._A)
		else:
			self._state = 0		

		self.internal_pos = 0	# There are four states per physical click.
		self.pos = 0			# infinite position value.  +ve is clockwise
		self.last_pos = 0
		
		self.running = False


	def run(self):
		
		self.running = True

		while(self.running):
			# Reading a rotary encoder is quite simple.  There are two
			# inputs, which can be high or low.  When the encoder moves
			# from one position to another, only one input changes.  If
			# we look at the current state of the pins and the previous
			# state we can see which way the encoder has turned.
			
			# There are two bits of current state, and two bits of
			# previous state, so we can combine them to make a single
			# 4-bit value, with 16 possible combinations.  Not all of
			# them are valid, so we only need to take action on some
			# of them.
			
			self._state <<= 2	# Move the previous state to bits 3 and 2
			self._state &= 0x0F # Mask off the old previous state
			# Read the current state (two IO pins) into bits 1 and 0
			if not self._dummy:
				self._state |= GPIO.input(self._B)<<1 | GPIO.input(self._A)

			# Now look at the bit pattern created by the two pairs
			# of bits.
			
			# These four patterns show that the current state is the
			# same as the previous state, so we do nothing.
			# [0b0000, 0b0101, 0b1010, 0b1111]
			
			# These four patterns show that two bits have changed
			# between the previous state and the current state.  This
			# is an error- maybe we missed a step when polling.  We
			# don't know what happened, so do nothing.
			# [0b0011, 0b0110, 0b1001, 0b1100]

			# The remaining eight patterns show that a single bit has
			# changed.  So we can determine which way the encoder
			# has moved.

			if self._state in [0b0001, 0b0111, 0b1110, 0b1000]:
				# One step CW
				self.internal_pos += 1
			elif self._state in [0b0010, 0b1011, 0b1101, 0b0100]:
				# One step ACW
				self.internal_pos -= 1

			# There are four state transitions per physical click
			self.pos = self.internal_pos//4
			
			# If we are in state 00 then we are on a click position,
			# so set the internal counter to an integer multiple of 4
			if self._state & 0x03 == 0:
				self.internal_pos = self.pos * 4
			
			if self._dummy:
				# If there's no hardware, don't sample often
				time.sleep(2)
			else:
				time.sleep(0.001)


	def stop(self):
		self.running = False

	@property
	def pushed(self):
		if not self._dummy:
			return not(GPIO.input(self._PB))	# The button is pushed (shorted to GND)
		else:
			return False

	@property
	def changed(self):
		# returns True if the value changed since the last call of changed.
		if(self.pos != self.last_pos):
			self.last_pos = self.pos
			return True

		return False


if __name__ == "__main__":
	# Tiny test routine, hardcoded pins.
	import time

	encoder = rotaryEncoder(13, 11, 5)
	
	try:
		print("Starting rotary encoder thread.")
		encoder.start()

		while not encoder.pushed:
			if encoder.changed:
				print(encoder.pos)
			time.sleep(0.1)

	except KeyboardInterrupt:
		print("Ctrl-C")

	except:
		print("Encoder error:", sys.exc_info()[0])
		raise

	print("Stopping rotary encoder thread")
	encoder.stop()
	print("Waiting for rotary encoder thread to finish.")
	encoder.join()
	
	print("Done")
