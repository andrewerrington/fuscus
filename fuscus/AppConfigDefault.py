'''/*
* Copyright 2013 BrewPi/Elco Jacobs.
* Copyright 2013 Matthew McGowan
*
* This file is part of BrewPi.
*
* BrewPi is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* BrewPi is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with BrewPi. If not, see <http://www.gnu.org/licenses/>.
*/
#pragma once'''
# Enable printing debug only log messages and debug only wrapped statements
BREWPI_DEBUG = 0
# Set which debug messages are printed
BREWPI_LOG_ERRORS = 1
BREWPI_LOG_WARNINGS = 1
BREWPI_LOG_INFO = 1
BREWPI_LOG_DEBUG = 0

# This flag virtualizes as much of the hardware as possible, so the code can be run in the AvrStudio simulator, which
# only emulates the microcontroller, not any attached peripherals.

BREWPI_EMULATE = 0

TEMP_SENSOR_CASCADED_FILTER = 1
TEMP_CONTROL_STATIC = 1

# Enable the simulator. Real sensors/actuators are replaced with simulated versions. In particular, the values reported by
# temp sensors are based on a model of the fridge/beer.

BREWPI_SIMULATE = 0
BREWPI_EEPROM_HELPER_COMMANDS = BREWPI_DEBUG or BREWPI_SIMULATE
OPTIMIZE_GLOBAL = 1
BUILD_NAME = 'Python'

# Enable the LCD menu.
BREWPI_MENU = 1
DISPLAY_TIME_HMS = 1
