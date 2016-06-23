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

class lcd:
    """Buffer LCD text and control LCD hardware."""

    def __init__(self, lines=4, chars=20, hardware=None):
        print("lcd object %s x %s created" % (lines, chars))
        self.lines = lines
        self.chars = chars
        self.clear()
        self.hardware = hardware

    def print(self, txt):
        self.buffer[self.y] = self.buffer[self.y][:self.x] + txt + self.buffer[self.y][self.x + len(txt):]
        self.buffer[self.y] = self.buffer[self.y][:self.chars]
        self.x += len(txt)

    def println(self, txt):
        self.print(txt)
        self.y = (self.y + 1) % self.lines
        self.x = 0

    def printat(self, x, y, txt):
        self.cursor(x, y)
        self.print(txt)

    def clear(self):
        self.buffer = [' ' * self.chars] * self.lines
        self.x = 0
        self.y = 0

    def cursor(self, x, y):
        self.x = x
        self.y = y

    def tab(self, x):
        self.x = x

    # The following functions call the actual hardware functions
    def update(self):
        # print("Copy buffer to LCD hardware")
        print(self.buffer)
        if self.hardware is not None:
            self.hardware.copy_to_display(self.buffer)

    def backlight(self, percent):
        if self.hardware is not None:
            self.hardware.backlight(percent)
