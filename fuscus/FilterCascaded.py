#!/usr/bin/env python3
"""Implement a cascaded IIR filter."""

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


from decimal import Decimal

import FilterFixed


# Use 3 filter sections. This gives excellent filtering, without adding
# too much delay.
# For 3 sections the stop band attenuation is 3x the single section
# attenuation in dB.
# The delay is also tripled.


class CascadedFilter:
	"""CascadedFilter implements a filter consisting of multiple second order sections."""

	def __init__(self, NUM_SECTIONS = 3):
		self.NUM_SECTIONS = NUM_SECTIONS
		self.sections = []
		for i in range(self.NUM_SECTIONS):
			self.sections.append(FilterFixed.FixedFilter(b=2))


	def setCoefficients(self, bValue):
		for section in self.sections:
			section.setCoefficients(bValue)


	def init(self, val):
		for section in self.sections:
			section.init(val)


	def add(self, val):
		# adds a value and returns the most recent filter output
		# val is input for next section, which is the output of the previous section
		# Internally we use Decimal, but other callers expect float.
		val = Decimal(val) 
		for section in self.sections:
			val = section.add(val)
			
		return float(val)


	def readInput(self):
		"""Returns the most recent filter input."""
		return self.sections[0].readInput()	# return input of first section


	def readOutput(self):
		"""Return output of last section."""
		return self.sections[-1].readOutput() 

	def readPrevOutput(self):
		"""Return previous output of last section."""
		return self.sections[-1].readPrevOutput() 


	def detectPosPeak(self):
		"""Detect peaks in last section."""
		return self.sections[-1].detectPosPeak()


	def detectNegPeak(self):
		"""Detect peaks in last section."""
		return self.sections[-1].detectNegPeak()