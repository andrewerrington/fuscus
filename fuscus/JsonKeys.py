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


JSONKEY_mode = "mode"
JSONKEY_beerSetting = "beerSet"
JSONKEY_fridgeSetting = "fridgeSet"
JSONKEY_heatEstimator = "heatEst"
JSONKEY_coolEstimator = "coolEst"

# constant
JSONKEY_tempFormat = "tempFormat"
JSONKEY_tempSettingMin = "tempSetMin"
JSONKEY_tempSettingMax = "tempSetMax"
JSONKEY_pidMax = "pidMax"
JSONKEY_Kp = "Kp"
JSONKEY_Ki = "Ki"
JSONKEY_Kd = "Kd"
JSONKEY_iMaxError = "iMaxErr"
JSONKEY_idleRangeHigh = "idleRangeH"
JSONKEY_idleRangeLow = "idleRangeL"
JSONKEY_heatingTargetUpper = "heatTargetH"
JSONKEY_heatingTargetLower = "heatTargetL"
JSONKEY_coolingTargetUpper = "coolTargetH"
JSONKEY_coolingTargetLower = "coolTargetL"
JSONKEY_maxHeatTimeForEstimate = "maxHeatTimeForEst"
JSONKEY_maxCoolTimeForEstimate = "maxCoolTimeForEst"
JSONKEY_fridgeFastFilter = "fridgeFastFilt"
JSONKEY_fridgeSlowFilter = "fridgeSlowFilt"
JSONKEY_fridgeSlopeFilter = "fridgeSlopeFilt"
JSONKEY_beerFastFilter = "beerFastFilt"
JSONKEY_beerSlowFilter = "beerSlowFilt"
JSONKEY_beerSlopeFilter = "beerSlopeFilt"
JSONKEY_lightAsHeater = "lah"
JSONKEY_rotaryHalfSteps = "hs"

# variable
JSONKEY_beerDiff = "beerDiff"
JSONKEY_diffIntegral = "diffIntegral"
JSONKEY_beerSlope = "beerSlope"
JSONKEY_p = "p"
JSONKEY_i = "i"
JSONKEY_d = "d"
JSONKEY_estimatedPeak = "estPeak"	# current peak estimate
JSONKEY_negPeakEstimate = "negPeakEst"	# last neg peak estimate before switching to idle
JSONKEY_posPeakEstimate = "posPeakEst"
JSONKEY_negPeak = "negPeak"	# last true neg peak
JSONKEY_posPeak = "posPeak"

JSONKEY_logType = "logType"
JSONKEY_logID = "logID"