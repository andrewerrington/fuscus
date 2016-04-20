#!/usr/bin/env python3
"""PCD8544 driver for Nokia 5110 display and compatibles."""

#
# Copyright 2013 XavierBerger (https://github.com/XavierBerger/pcd8544)
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

# Original source: https://github.com/XavierBerger/pcd8544

# Code picked up Raspberry Pi forums  
# http://www.raspberrypi.org/phpBB3/viewtopic.php?p=301522#p301522
#
# Conversion to RPi.GPIO by Andrew Errington July 2015

import time

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)

import spidev
from font4x7 import FONT, PIXELS_PER_COLUMN

#from PIL import Image,ImageDraw,ImageFont

X_PIXELS = 84
Y_PIXELS = 48

PIXELS_PER_ROW = 8	# This must be 8, otherwise things get very hard.

ROWS = Y_PIXELS // PIXELS_PER_ROW
COLUMNS = ((X_PIXELS - 1) // PIXELS_PER_COLUMN)+1	# ceiling function

CLSBUF = [0]*(X_PIXELS*(Y_PIXELS//8))

ORIGINAL_CUSTOM = FONT['\x7f']

def bit_reverse(value, width = 8):
	result = 0
	for _ in range(width):
		result = (result << 1) | (value & 1)
		value >>= 1

	return result

BITREVERSE = map(bit_reverse, range(256))


class pcd8544:
	
	def __init__(self, DC = 16, RST = 18, LED = 12,
		dev = (0, 0), speed = 4000000, backlight = 0,
		contrast = 185):
	
		self._DC = DC
		self._RST = RST
		self._LED = LED
		
		self.font = FONT
		
		if self._LED is not None:
			GPIO.setup(self._LED, GPIO.OUT)

			# 100Hz refresh, should be low flicker
			self.backlight_control = GPIO.PWM(self._LED, 100)

		self.spi = spidev.SpiDev()
		self.spi.open(dev[0], dev[1])
		self.spi.max_speed_hz = speed

		# Set pin directions.  Hold RST low to reset.
		GPIO.setup(self._DC, GPIO.OUT)
		GPIO.setup(self._RST, GPIO.OUT, initial=GPIO.LOW)

		time.sleep(0.100)
		GPIO.output(RST, GPIO.HIGH)
		# Extended mode, bias, vop, basic mode, non-inverted display.
		self.set_contrast(contrast)

		if self._LED is not None:
			# Turn the backlight to zero brightness.
			self.backlight_control.start(0)
			# Then set the desired brightness (so we get a range check on the argument).
			self.backlight(backlight)
		
		self.cls()
		self.x = 0
		self.y = 0


	def lcd_cmd(self, value):
		GPIO.output(self._DC, GPIO.LOW)
		self.spi.writebytes([value])


	def lcd_data(self, value):
		GPIO.output(self._DC, GPIO.HIGH)
		self.spi.writebytes([value])


	def update(self):
		pass


	def clear(self):
		self.cls()


	def cls(self):
		self.gotoxy(0, 0)
		GPIO.output(self._DC, GPIO.HIGH)
		self.spi.writebytes(CLSBUF)


	def backlight(self, percent):
		if self._LED is not None:
			if ((percent is True) or (percent > 100)):
				self.backlight_control.ChangeDutyCycle(100)
			elif ((percent is False) or (percent < 0)):
				self.backlight_control.ChangeDutyCycle(0)
			else:
				self.backlight_control.ChangeDutyCycle(percent)


	def set_contrast(self, contrast):
		if (0x80 <= contrast < 0xFF):
			GPIO.output(self._DC, GPIO.LOW)
			self.spi.writebytes([0x21, 0x14, contrast, 0x20, 0x0c])


	def gotoxy(self, x, y):
		if ((0 <= x < COLUMNS*PIXELS_PER_COLUMN) and (0 <= y < ROWS)):
			GPIO.output(self._DC, GPIO.LOW)
			self.spi.writebytes([x+128, y+64])
			self.x = x
			self.y = y


	def gotorc(self, r, c):
		self.gotoxy(c*PIXELS_PER_COLUMN, r)


	def printat(self, r, c, string):
		self.gotorc(r, c)
		self.text(string)


	def print(self,string):
		self.text(string)


	def println(self,string):
		self.text(string)	# FIXME: go to start of next line


	def text(self, string):
		for char in string:
			self.display_char(char)


	def centre_text(self, r, word):
		self.gotorc(r, max(0, (COLUMNS - len(word)) // 2))
		self.text(word)


	def show_custom_char(self):
		self.display_char('\x7f')


	def define_custom_char(self, values):
		FONT['\x7f'] = values


	def restore_custom_char(self):
		self.define_custom_char(ORIGINAL_CUSTOM)


	def alt_custom_char(self):
		self.define_custom_char([0x00, 0x50, 0x3C, 0x52, 0x44])


	def pi_custom_char(self, ):
		self.define_custom_char([0x19, 0x25, 0x5A, 0x25, 0x19])


	def display_char(self, char):
		try:
			GPIO.output(self._DC, GPIO.HIGH)
			if self.x + len(self.font[char]) < X_PIXELS:
				self.spi.writebytes(self.font[char] + [0])
				self.x += len(self.font[char]) + 1
			else:
				self.spi.writebytes(self.font[char])
				self.x += len(self.font[char])

		except KeyError:
			pass # Ignore undefined characters.


	def load_bitmap(self, filename, reverse = False):
		mask = 0x00 if reverse else 0xff
		self.gotoxy(0, 0)
		with open(filename, 'rb') as bitmap_file:
			for x in range(6):
				for y in range(84):
					bitmap_file.seek(0x3e + y * 8 + x)
					self.lcd_data(BITREVERSE[ord(bitmap_file.read(1))] ^ mask)


	def copy_to_display(self, buffer):
		"""Copy lines from buffer to display.
		Limit rows and columns to what is physically available."""
		self.clear()
		r = 0
		for line in buffer:
			self.gotoxy(0, r)
			self.print(line[:COLUMNS])
			r += 1
			if r == ROWS:
				break


	def show_image(self, im):
		# Rotate and mirror the image
		rim = im.rotate(-90).transpose(Image.FLIP_LEFT_RIGHT)

		# Change display to vertical write mode for graphics
		GPIO.output(self._DC, GPIO.LOW)
		self.spi.writebytes([0x22])

		# Start at upper left corner
		self.gotoxy(0, 0)
		# Put on display with reversed bit order
		GPIO.output(self._DC, GPIO.HIGH)
		self.spi.writebytes([BITREVERSE[ord(x)] for x in list(rim.tostring())])

 		# Switch back to horizontal write mode for text
		GPIO.output(self._DC, GPIO.LOW)
		self.spi.writebytes([0x20])

