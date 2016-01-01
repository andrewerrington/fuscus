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

import logging
import pickle

import ticks

import tempSensor

# Constants from tempControl.h
# Values represent time in seconds

# Set minimum off time to prevent short cycling the compressor in seconds
MIN_COOL_OFF_TIME = 300
# Use a minimum off time for the heater as well, so it heats in cycles,
# not lots of short bursts
MIN_HEAT_OFF_TIME = 300
# Minimum on time for the cooler.
MIN_COOL_ON_TIME = 180
# Minimum on time for the heater.
MIN_HEAT_ON_TIME = 180
# Use a large minimum off time in fridge constant mode. No need for
# very fast cycling.
MIN_COOL_OFF_TIME_FRIDGE_CONSTANT = 600
# Set a minimum off time between switching between heating and cooling
MIN_SWITCH_TIME = 600
# Time allowed for peak detection
COOL_PEAK_DETECT_TIME = 1800
HEAT_PEAK_DETECT_TIME = 900

MODES = {	'MODE_FRIDGE_CONSTANT' : 'f',
			'MODE_BEER_CONSTANT' : 'b',
			'MODE_BEER_PROFILE' : 'p',
			'MODE_OFF' : 'o',
			'MODE_TEST' : 't',
		}

STATES = {	'IDLE' : 0,
			'STATE_OFF' : 1,
			'DOOR_OPEN' : 2,	# used by the Display only
			'HEATING' : 3,
			'COOLING' : 4,
			'WAITING_TO_COOL' : 5,
			'WAITING_TO_HEAT' : 6,
			'WAITING_FOR_PEAK_DETECT' : 7,
			'COOLING_MIN_TIME' : 8,
			'HEATING_MIN_TIME' : 9,
		}


# These two structs are stored in and loaded from EEPROM
class ControlSettings:
	def __init__(self):
		self.mode = None
		self.beerSetting = None
		self.fridgeSetting = None
		self.heatEstimator = None # updated automatically by self learning algorithm
		self.coolEstimator = None # updated automatically by self learning algorithm

class ControlVariables:
	def __init__(self):
		self.beerDiff = 0
		self.diffIntegral = 0
		self.beerSlope = 0
		self.p = 0
		self.i = 0
		self.d = 0
		self.estimatedPeak = 0
		self.negPeakEstimate = 0	# last estimate
		self.posPeakEstimate = 0
		self.negPeak = 0	# last detected peak
		self.posPeak = 0

class ControlConstants:
	def __init__(self):
		self.tempFormat = None
		self.tempSettingMin = None
		self.tempSettingMax = None
		self.Kp = None
		self.Ki = None
		self.Kd = None
		self.iMaxError = None
		self.idleRangeHigh = None
		self.idleRangeLow = None
		self.heatingTargetUpper = None
		self.heatingTargetLower = None
		self.coolingTargetUpper = None
		self.coolingTargetLower = None
		self.maxHeatTimeForEstimate = None	# max time for heat estimate in seconds
		self.maxCoolTimeForEstimate = None	# max time for heat estimate in seconds
		# for the filter coefficients the b value is stored. a is calculated from b.
		self.fridgeFastFilter = None	# for display, logging and on-off control
		self.fridgeSlowFilter = None	# for peak detection
		self.fridgeSlopeFilter = None	# not used in current control algorithm
		self.beerFastFilter = None	# for display and logging
		self.beerSlowFilter = None	# for on/off control algorithm
		self.beerSlopeFilter = None	# for PID calculation
		self.lightAsHeater = None		# use the light to heat rather than the configured heater device
		self.rotaryHalfSteps = None	# define whether to use full or half steps for the rotary encoder
		self.pidMax = None


class tempController:
	
	def __init__(self, ID_fridge, ID_beer=None, ID_ambient=None,
				cooler=None, heater=None, door=None):
		# We must have at least a fridge sensor
		
		self.cs = ControlSettings()
		self.cv = ControlVariables()
		self.cc = ControlConstants()
		
		# State variables
		self.state = STATES['IDLE']
		self.cs.mode = MODES['MODE_OFF']

		self.doPosPeakDetect = None
		self.doNegPeakDetect = None
		
		self.door = door
		self.doorOpen = None

		self.cooler = cooler
		self.heater = heater
		self.light = None	# Not implemented
		self.fan = None		# Not implemented
		
		self.lastIdleTime = ticks.seconds()
		self.waitTime = None
		
		self.storedBeerSetting = None

		#cameraLight.setActive(false);
	
		#this is for cases where the device manager hasn't configured beer/fridge sensor.
		#if (self.beerSensor==None):
		self.beerSensor = tempSensor.sensor(ID_beer)

		#if (self.fridgeSensor==None):
		self.fridgeSensor = tempSensor.sensor(ID_fridge)
	
		self.ambientSensor = tempSensor.sensor(ID_ambient)
		
		self.beerSensor.init()
		self.fridgeSensor.init()
		self.ambientSensor.init()

		self.updateTemperatures()
		self.reset()
	
		# Do not allow heating/cooling directly after reset.
		# A failing script + CRON + Arduino uno (which resets on serial
		# connect) could damage the compressor
		# For test purposes, set these to -3600 to eliminate waiting
		# after reset
		self.lastHeatTime = ticks.seconds()
		self.lastCoolTime = ticks.seconds()
		
		self.integralUpdateCounter = 0


	def reset(self):
		self.doPosPeakDetect = False
		self.doNegPeakDetect = False


	def updateSensor(self, sensor):
		sensor.update()
		#if not (sensor.isConnected()):
		#	sensor.init();


	def updateTemperatures(self):
		self.updateSensor(self.beerSensor)
		self.updateSensor(self.fridgeSensor)
	
		# Read ambient sensor to keep the value up to date.
		# If no sensor is connected, this does nothing.
		# This prevents a delay in serial response because
		# the value is not up to date.
		#if(ambientSensor->read() == TEMP_SENSOR_DISCONNECTED){
		#ambientSensor->init(); # try to reconnect a disconnected, but installed sensor
		self.updateSensor(self.ambientSensor)

	
	def modeIsBeer(self):
		return self.cs.mode in (MODES['MODE_BEER_CONSTANT'],
						  MODES['MODE_BEER_PROFILE'])


	def updatePID(self):
		#static unsigned char integralUpdateCounter = 0;
		if (self.modeIsBeer()):
			print ("Mode is beer")
			#if(isDisabledOrInvalid(cs.beerSetting)){
			if (self.cs.beerSetting is None):
				print ("beerSetting is None")
				# beer setting is not updated yet
				# set fridge to unknown too
				self.cs.fridgeSetting = None
				return

			# fridge setting is calculated with PID algorithm.
			# Beer temperature error is input to PID
			self.cv.beerDiff = self.cs.beerSetting - self.beerSensor.readSlowFiltered()
			self.cv.beerSlope = self.beerSensor.readSlope()
			fridgeFastFiltered = self.fridgeSensor.readFastFiltered()

			self.integralUpdateCounter += 1
			
			print ("integralUpdateCounter %s"%self.integralUpdateCounter)

			if (self.integralUpdateCounter == 60):
				self.integralUpdateCounter = 0
				integratorUpdate = self.cv.beerDiff
				# Only update integrator in IDLE, because that's when the
				# fridge temp has reached the fridge setting.
				# If the beer temp is still not correct, the fridge setting
				# is too low/high and integrator action is needed.
				if (self.state != STATES['IDLE']):
					integratorUpdate = 0

				elif (abs(integratorUpdate) < self.cc.iMaxError):
					# difference is smaller than iMaxError
					# check additional conditions to see if integrator
					# should be active to prevent windup
					updateSign = bool(integratorUpdate > 0)	# True = positive, False = negative
					integratorSign = bool(self.cv.diffIntegral > 0)
					if (updateSign == integratorSign):
						# beerDiff and integrator have same sign. Integrator would be increased.
						# If actuator is already at max increasing actuator will only cause integrator windup.
						if (self.cs.fridgeSetting >= self.cc.tempSettingMax):
							integratorUpdate = 0
						if (self.cs.fridgeSetting <= self.cc.tempSettingMin):
							integratorUpdate = 0
						if ((self.cs.fridgeSetting - self.cs.beerSetting) >= self.cc.pidMax):
							integratorUpdate = 0
						if ((self.cs.beerSetting - self.cs.fridgeSetting) >= self.cc.pidMax):
							integratorUpdate = 0
						# cooling and fridge temp is more than 2 degrees from setting, actuator is saturated. (Note: 1024 is 2 << 9)
						if (not updateSign and (fridgeFastFiltered > (self.cs.fridgeSetting + 2))): # was  +1024))):
							integratorUpdate = 0
						# heating and fridge temp is more than 2 degrees from setting, actuator is saturated.
						if (updateSign and (fridgeFastFiltered < (self.cs.fridgeSetting - 2))): # was -1024))):
							integratorUpdate = 0
					else:
						# integrator action is decreased. Decrease faster than increase.
						integratorUpdate *= 2
				else:
					# decrease integral by 1/8 when far from the end value to reset the integrator
					integratorUpdate = -(self.cv.diffIntegral / 8)

				self.cv.diffIntegral += integratorUpdate

			# calculate PID parts.
			print(vars(self.cc))
			print(vars(self.cv))
			self.cv.p = self.cc.Kp * self.cv.beerDiff
			self.cv.i = self.cc.Ki * self.cv.diffIntegral
			self.cv.d = self.cc.Kd * self.cv.beerSlope
			newFridgeSetting = self.cs.beerSetting
			newFridgeSetting += self.cv.p
			newFridgeSetting += self.cv.i
			newFridgeSetting += self.cv.d
			# constrain to tempSettingMin or beerSetting - pidMAx, whichever is lower.
			lowerBound = self.cc.tempSettingMin if (self.cs.beerSetting <= self.cc.tempSettingMin + self.cc.pidMax) else (self.cs.beerSetting - self.cc.pidMax)
			# constrain to tempSettingMax or beerSetting + pidMAx, whichever is higher.
			upperBound = self.cc.tempSettingMax if (self.cs.beerSetting >= self.cc.tempSettingMax - self.cc.pidMax) else (self.cs.beerSetting + self.cc.pidMax)
			#cs.fridgeSetting = constrain(constrainTemp16(newFridgeSetting), lowerBound, upperBound);
			self.cs.fridgeSetting = max(lowerBound, min(newFridgeSetting, upperBound))

		elif (self.cs.mode == MODES['MODE_FRIDGE_CONSTANT']):
			# FridgeTemperature is set manually, disable beer setpoint
			self.cs.beerSetting = None	#DISABLED_TEMP;


	def updateState(self):

		print("Update state. Mode %s, state %s"%({v: k for k, v in MODES.items()}[self.cs.mode], {v: k for k, v in STATES.items()}[self.state]))

		stayIdle = False
		newDoorOpen = self.door.isOpen

		if (newDoorOpen != self.doorOpen):
			self.doorOpen = newDoorOpen
			print("Fridge door %s"%('opened' if self.doorOpen else 'closed'))
			#FIXME: piLink.printFridgeAnnotation(PSTR("Fridge door %S"), doorOpen ? PSTR("opened") : PSTR("closed"));

		if (self.cs.mode == MODES['MODE_OFF']):
			self.state = STATES['STATE_OFF']
			stayIdle = True

		# stay idle when one of the required sensors is disconnected,
		# or the fridge setting is INVALID_TEMP
		#FIXME: if(isDisabledOrInvalid(cs.fridgeSetting) ||
		#!fridgeSensor->isConnected() ||
		#(!beerSensor->isConnected() && tempControl.modeIsBeer())):
		#	self.state = 'IDLE'
		#	stayIdle = True

		sinceIdle = self.timeSinceIdle()
		sinceCooling = self.timeSinceCooling()
		sinceHeating = self.timeSinceHeating()
		fridgeFast = self.fridgeSensor.readFastFiltered()
		beerFast = self.beerSensor.readFastFiltered()
		secs = ticks.seconds()

		if self.state in (STATES['IDLE'], STATES['STATE_OFF'],
			STATES['WAITING_TO_COOL'], STATES['WAITING_TO_HEAT'],
			STATES['WAITING_FOR_PEAK_DETECT']):
			self.lastIdleTime = secs
			if not stayIdle:
				# set waitTime to zero. It will be set to the maximum
				# required waitTime below when wait is in effect.
				#if(stayIdle):
				#	break
				self.resetWaitTime()
				if (fridgeFast > (self.cs.fridgeSetting+self.cc.idleRangeHigh) ):	# fridge temperature is too high
					self.updateWaitTime(MIN_SWITCH_TIME, sinceHeating)
					if (self.cs.mode == MODES['MODE_FRIDGE_CONSTANT']):
						self.updateWaitTime(MIN_COOL_OFF_TIME_FRIDGE_CONSTANT, sinceCooling)
					else:
						if (beerFast < (self.cs.beerSetting + 0.03125) ): #+ 16) ):	# If beer is already under target, stay/go to idle. 1/2 sensor bit idle zone
							self.state = STATES['IDLE']	# beer is already colder than setting, stay in or go to idle
							#break # FIXME: We need to skip the next if statement
						else:
							self.updateWaitTime(MIN_COOL_OFF_TIME, sinceCooling)
					if (self.cooler != None): # FIXME was &defaultActuator):
						if (self.getWaitTime() > 0):
							self.state = STATES['WAITING_TO_COOL']
						else:
							self.state = STATES['COOLING']
				elif (fridgeFast < (self.cs.fridgeSetting + self.cc.idleRangeLow)):	# fridge temperature is too low
					print("Fridge temperature is too low")
					self.updateWaitTime(MIN_SWITCH_TIME, sinceCooling)
					self.updateWaitTime(MIN_HEAT_OFF_TIME, sinceHeating)
					if (self.cs.mode != MODES['MODE_FRIDGE_CONSTANT']):
						if (beerFast > (self.cs.beerSetting - 0.03125) ): # - 16)){ // If beer is already over target, stay/go to idle. 1/2 sensor bit idle zone
							self.state = STATES['IDLE']	# beer is already warmer than setting, stay in or go to idle
							#break # FIXME: We need to skip the next if statement
					#if(self.heater != &defaultActuator or (self.lightAsHeater and (self.light != &defaultActuator))):
					# FIXME what is &defaultActuator ?
					if ((self.heater != None or
						(self.cc.lightAsHeater and (self.light != None)))):
						if (self.getWaitTime() > 0):
							self.state = STATES['WAITING_TO_HEAT']
						else:
							self.state = STATES['HEATING']
				else:
					self.state = STATES['IDLE']	# within IDLE range, always go to IDLE
					#break
			
			if (self.state == STATES['HEATING']
				or self.state == STATES['COOLING']):
				# If peak detect is not finished, but the fridge wants to switch to heat/cool
				# Wait for peak detection and show on display
				if self.doNegPeakDetect:
					self.updateWaitTime(COOL_PEAK_DETECT_TIME, sinceCooling)
					self.state = STATES['WAITING_FOR_PEAK_DETECT']
				elif self.doPosPeakDetect:
					self.tempControl.updateWaitTime(HEAT_PEAK_DETECT_TIME, sinceHeating)
					self.state = STATES['WAITING_FOR_PEAK_DETECT']

		elif self.state in (STATES['COOLING'], STATES['COOLING_MIN_TIME']):
			self.doNegPeakDetect = True
			self.lastCoolTime = secs
			self.updateEstimatedPeak(self.cc.maxCoolTimeForEstimate, self.cs.coolEstimator, sinceIdle)
			self.state = STATES['COOLING']	# set to cooling here, so the display of COOLING/COOLING_MIN_TIME is correct
			# stop cooling when estimated fridge temp peak lands on target or if beer is already too cold (1/2 sensor bit idle zone)
			if (self.cv.estimatedPeak <= self.cs.fridgeSetting
				or (self.cs.mode != MODES['MODE_FRIDGE_CONSTANT']
				and beerFast < (self.cs.beerSetting - 0.03125))):
				if (sinceIdle > MIN_COOL_ON_TIME):
					self.cv.negPeakEstimate = self.cv.estimatedPeak	# remember estimated peak when I switch to IDLE, to adjust estimator later
					self.state = STATES['IDLE']
					#break
				else:
					self.state = STATES['COOLING_MIN_TIME']
					#break

		elif self.state in (STATES['HEATING'], STATES['HEATING_MIN_TIME']):
			self.doPosPeakDetect = True
			self.lastHeatTime = secs
			self.updateEstimatedPeak(self.cc.maxHeatTimeForEstimate, self.cs.heatEstimator, sinceIdle)
			self.state = STATES['HEATING']	# reset to heating here, so the display of HEATING/HEATING_MIN_TIME is correct
			# stop heating when estimated fridge temp peak lands on target or if beer is already too warm (1/2 sensor bit idle zone)
			if (self.cv.estimatedPeak >= self.cs.fridgeSetting
				or (self.cs.mode != MODES['MODE_FRIDGE_CONSTANT']
				and beerFast > (self.cs.beerSetting + 0.03125))):
				if (sinceIdle > MIN_HEAT_ON_TIME):
					self.cv.posPeakEstimate = self.cv.estimatedPeak	# remember estimated peak when I switch to IDLE, to adjust estimator later
					self.state = STATES['IDLE']
					#break
				else:
					self.state = STATES['HEATING_MIN_TIME']
					#break

		elif self.state in (STATES['DOOR_OPEN']):
			pass	# do nothing
		else:
			logging.debug("Unknown state in updatePID: %s"%self.state)


	def updateEstimatedPeak(self, timeLimit, estimator, sinceIdle):
		activeTime = min(timeLimit, sinceIdle)	# heat or cool time in seconds
		estimatedOvershoot = (estimator * activeTime) / 3600	# overshoot estimator is in overshoot per hour
		if (self.stateIsCooling()):
			estimatedOvershoot = -estimatedOvershoot	# when cooling subtract overshoot from fridge temperature	
		self.cv.estimatedPeak = self.fridgeSensor.readFastFiltered() + estimatedOvershoot


	def updateOutputs(self):
		if (self.cs.mode == MODES['MODE_TEST']):
			return
		#cameraLight.update();
		heating = self.stateIsHeating()
		cooling = self.stateIsCooling()
		self.cooler.set_output(cooling)
		self.heater.set_output(heating)
		#light->setActive(isDoorOpen() || (cc.lightAsHeater && heating) || cameraLightState.isActive());	
		#fan->setActive(heating || cooling);


	def detectPeaks(self):
		"""Detect peaks in fridge temperature to tune overshoot estimators."""
		#LOG_ID_TYPE detected = 0;
		detected = None
		peak = estimate = error = oldEstimator = newEstimator = None
		if (self.doPosPeakDetect and not self.stateIsHeating()):
			# FIXME: Either of these could be None.  Used to be INVALID_TEMP, so the maths would work.
			# INVALID_TEMP = -32768
			# error = peak - estimate
			# peak is invalid, error is very -ve
			# estimate is invalid, error 
			
			peak = self.fridgeSensor.detectPosPeak()
			estimate = self.cv.posPeakEstimate
			#if peak is not None:	# FIXME: This could be moved into if statement below
			#	error = peak - estimate
			oldEstimator = self.cs.heatEstimator
			if peak is not None:	#INVALID_TEMP):
				# positive peak detected
				error = peak - estimate
				if (error > self.cc.heatingTargetUpper):
					# Peak temperature was higher than the estimate.
					# Overshoot was higher than expected
					# Increase estimator to increase the estimated overshoot
					self.increaseEstimator(self.cs.heatEstimator, error)
					
				if (error < self.cc.heatingTargetLower):
					# Peak temperature was lower than the estimate.
					# Overshoot was lower than expected
					# Decrease estimator to decrease the estimated overshoot
					self.decreaseEstimator(self.cs.heatEstimator, error)

				detected = 'INFO_POSITIVE_PEAK'

			elif (self.timeSinceHeating() > HEAT_PEAK_DETECT_TIME):
				if (self.fridgeSensor.readFastFiltered()
					< (self.cv.posPeakEstimate + self.cc.heatingTargetLower)):
					# Idle period almost reaches maximum allowed time for peak detection
					# This is the heat, then drift up too slow (but in the right direction).
					# estimator is too high
					peak = self.fridgeSensor.readFastFiltered()
					self.decreaseEstimator(self.cs.heatEstimator, error)
					detected = 'INFO_POSITIVE_DRIFT'

				else:
					# maximum time for peak estimation reached
					self.doPosPeakDetect = False

			if detected:
				newEstimator = self.cs.heatEstimator
				self.cv.posPeak = peak
				self.doPosPeakDetect = False
			
		elif (self.doNegPeakDetect and not self.stateIsCooling()):
			# FIXME: Either of these could be None.  Used to be INVALID_TEMP, so the maths would work.
			peak = self.fridgeSensor.detectNegPeak()
			estimate = self.cv.negPeakEstimate
			print("peak %s : estimate %s"%(peak, estimate))
			#if peak is not None:	# FIXME: This could be moved into if statement below
			#	error = peak - estimate	# FIXME: Crash if estimate is None
			oldEstimator = self.cs.coolEstimator
			if (peak != None):	#INVALID_TEMP):
				# negative peak detected
				error = peak - estimate	# FIXME: Crash if estimate is None
				if (error < self.cc.coolingTargetLower):
					# Peak temperature was lower than the estimate.
					# Overshoot was higher than expected
					# Increase estimator to increase the estimated overshoot
					self.increaseEstimator(self.cs.coolEstimator, error)
				if (error > self.cc.coolingTargetUpper):
					# Peak temperature was higher than the estimate.
					# Overshoot was lower than expected
					# Decrease estimator to decrease the estimated overshoot
					self.decreaseEstimator(self.cs.coolEstimator, error)

				detected = 'INFO_NEGATIVE_PEAK'
			
			elif (self.timeSinceCooling() > COOL_PEAK_DETECT_TIME):
				if (self.fridgeSensor.readFastFiltered()
					> (self.cv.negPeakEstimate + self.cc.coolingTargetUpper)):
					# Idle period almost reaches maximum allowed time for peak detection
					# This is the cooling, then drift down too slow (but in the right direction).
					# estimator is too high
					peak = self.fridgeSensor.readFastFiltered()
					self.decreaseEstimator(self.cs.coolEstimator, error)	# FIXME: error is not known here
					detected = 'INFO_NEGATIVE_DRIFT'
				else:
					# maximum time for peak estimation reached
					self.doNegPeakDetect = False

			if detected:
				newEstimator = self.cs.coolEstimator
				self.cv.negPeak = peak
				self.doNegPeakDetect = False
			
		if detected:
			# send out log message for type of peak detected
			#logInfoTempTempFixedFixed(detected, peak, estimate, oldEstimator, newEstimator)
			logging.info("Peak detected: %s %s %s %s %s"%(detected, peak, estimate, oldEstimator, newEstimator))


	def increaseEstimator(self, estimator, error):
		"""Increase estimator at least 20%, max 50%."""
		#temperature factor = 614 + constrainTemp(abs(error)>>5, 0, 154);
		#// 1.2 + 3.1% of error, limit between 1.2 and 1.5
		factor = 1.2 + max(0, min(abs(error) * 0.031, 0.3))	# 1.2 + 3.1% of error, limit between 1.2 and 1.5
		estimator *= factor
		if (estimator < 0.05):
			estimator = 0.05	# make estimator at least 0.05
		# FIXME: eepromManager.storeTempSettings();


	def decreaseEstimator(self, estimator, error):
		"""Decrease estimator at least 16.7% (1/1.2), max 33.3% (1/1.5)."""
		#temperature factor = 426 - constrainTemp(abs(error)>>5, 0, 85);
		#// 0.833 - 3.1% of error, limit between 0.667 and 0.833
		factor = 0.833 - max(0, min(abs(error) * 0.031, 0.166))	# 0.833 - 3.1% of error, limit between 0.667 and 0.833
		estimator *= factor
		# FIXME: eepromManager.storeTempSettings();


	def timeSinceCooling(self):
		return ticks.timeSince(self.lastCoolTime)

	
	def timeSinceHeating(self):
		return ticks.timeSince(self.lastHeatTime)


	def timeSinceIdle(self):
		return ticks.timeSince(self.lastIdleTime)


	def loadDefaultSettings(self):
		#if BREWPI_EMULATE
		#	setMode(MODE_BEER_CONSTANT);
		#else	
		#	setMode(MODE_OFF);
		#endif
		self.setMode(MODES['MODE_OFF'])
		self.cs.beerSetting = None	# start with no temp settings
		self.cs.fridgeSetting = None
		self.cs.heatEstimator = 0.2 # intToTempDiff(2)/10; // 0.2
		self.cs.coolEstimator = 5 #intToTempDiff(5);


	def storeConstants(self):
		"""Write variables in cc class to EEPROM (file)."""
		with open('EEPROM.cc', 'wb') as f:
			pickle.dump(vars(self.cc), f, pickle.HIGHEST_PROTOCOL)


	def loadConstants(self):
		"""Read variables in cc class from EEPROM (file)."""
		with open('EEPROM.cc', 'rb') as f:
			data = pickle.load(f)
		
		self.cc.__dict__.update(data)

		self.initFilters()


	def storeSettings(self):
		"""Write variables in cs class to EEPROM (file)."""
		with open('EEPROM.cs', 'wb') as f:
			pickle.dump(vars(self.cs), f, pickle.HIGHEST_PROTOCOL)
		self.storedBeerSetting = self.cs.beerSetting


	def loadSettings(self):
		"""Read variables in cs class from EEPROM (file)."""
		with open('EEPROM.cs', 'rb') as f:
			data = pickle.load(f)
		
		self.cs.__dict__.update(data)

		logging.debug("loaded settings")
		self.storedBeerSetting = self.cs.beerSetting
		self.setMode(self.cs.mode, True)	# Force the mode update

	
	def loadDefaultConstants(self):
		# See ControlConstants class definition for descriptions
		self.cc.tempFormat = 'C'
		self.cc.tempSettingMin = 1
		self.cc.tempSettingMax = 30
		self.cc.Kp = 5.0
		self.cc.Ki = 0.35
		self.cc.Kd = 2.5
		self.cc.iMaxError = 0.5
		self.cc.idleRangeHigh = 1
		self.cc.idleRangeLow = -1
		self.cc.heatingTargetUpper = 0.3
		self.cc.heatingTargetLower = -0.2
		self.cc.coolingTargetUpper = 0.2
		self.cc.coolingTargetLower = -0.3
		self.cc.maxHeatTimeForEstimate = 600
		self.cc.maxCoolTimeForEstimate = 1200
		self.cc.fridgeFastFilter = 1
		self.cc.fridgeSlowFilter = 4
		self.cc.fridgeSlopeFilter = 3
		self.cc.beerFastFilter = 3
		self.cc.beerSlowFilter = 4
		self.cc.beerSlopeFilter = 4
		self.cc.lightAsHeater = 0
		self.cc.rotaryHalfSteps = 0
		self.cc.pidMax = 10

		self.initFilters()

	
	def initFilters(self):
		self.fridgeSensor.setFastFilterCoefficients(self.cc.fridgeFastFilter)
		self.fridgeSensor.setSlowFilterCoefficients(self.cc.fridgeSlowFilter)
		self.fridgeSensor.setSlopeFilterCoefficients(self.cc.fridgeSlopeFilter)
		self.beerSensor.setFastFilterCoefficients(self.cc.beerFastFilter)
		self.beerSensor.setSlowFilterCoefficients(self.cc.beerSlowFilter)
		self.beerSensor.setSlopeFilterCoefficients(self.cc.beerSlopeFilter)

	
	def setMode(self, newMode, force=False):
		logging.debug("TempControl::setMode from %s to %s", self.cs.mode, newMode)
	
		if (newMode != self.cs.mode or self.state == STATES['WAITING_TO_HEAT']
			or self.state == STATES['WAITING_TO_COOL']
			or self.state == STATES['WAITING_FOR_PEAK_DETECT']):
			self.state = STATES['IDLE']
			force = True

		if (force):
			self.cs.mode = newMode
			if (newMode == MODES['MODE_OFF']):
				self.cs.beerSetting = None
				self.cs.fridgeSetting = None
			
			# FIXME: eepromManager.storeTempSettings()


	def getBeerTemp(self):
		if (self.beerSensor.isConnected()):
			return self.beerSensor.readFastFiltered()
		else:
			return None	

	
	def	getBeerSetting(self):
		return self.cs.beerSetting
	
	
	def getFridgeTemp(self):
		if (self.fridgeSensor.isConnected()):
			return self.fridgeSensor.readFastFiltered()
		else:
			return None


	def	getFridgeSetting(self):
		return self.cs.fridgeSetting


	def setBeerTemp(self, newTemp):
		oldBeerSetting = self.cs.beerSetting
		self.cs.beerSetting = newTemp
		if (oldBeerSetting is None or (abs(oldBeerSetting - newTemp) > 0.5)):	# more than half degree C difference with old setting
			self.reset()	# reset controller
		self.updatePID()
		self.updateState()
		#FIXME: Implement this
		#if (self.cs.mode != MODES['MODE_BEER_PROFILE']
		#	or abs(self.storedBeerSetting - newTemp) > 0.25):
			# more than 1/4 degree C difference with EEPROM
			# Do not store settings every time in profile mode, because EEPROM has limited number of write cycles.
			# A temperature ramp would cause a lot of writes
			# If Raspberry Pi is connected, it will update the settings anyway. This is just a safety feature.
			# FIXME: eepromManager.storeTempSettings()

	
	def setFridgeTemp(self, newTemp):
		self.cs.fridgeSetting = newTemp
		self.reset()	# reset peak detection and PID
		self.updatePID()
		self.updateState()
		# FIXME eepromManager.storeTempSettings()


	def stateIsCooling(self):
		return self.state in (STATES['COOLING'], 
						STATES['COOLING_MIN_TIME'])
	
	
	def stateIsHeating(self):
		return self.state in (STATES['HEATING'],
						STATES['HEATING_MIN_TIME'])


	def getRoomTemp(self):
		return self.ambientSensor.temperature


	def getMode(self):
		return self.cs.mode


	def getState(self):
		return self.state


	def getWaitTime(self):
		return self.waitTime
	
	
	def resetWaitTime(self):
		self.waitTime = 0
		
		
	def updateWaitTime(self, newTimeLimit, newTimeSince):
		if (newTimeSince<newTimeLimit):
			self.newWaitTime = newTimeLimit - newTimeSince
			if (self.newWaitTime > self.waitTime):
				self.waitTime = self.newWaitTime


	def isDoorOpen(self):
		return self.doorOpen

	
	def getDisplayState(self):
		return STATES['DOOR_OPEN'] if self.isDoorOpen() else self.getState()
