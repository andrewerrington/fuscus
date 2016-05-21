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

import pty
import os
import sys
import time
import json
import select
import yaml  # To get around brewpi's terse JSON
import logging
import termios
import datetime

import ui
from constants import *
from JsonKeys import *

STR_WEB_INTERFACE = "in web interface"
STR_TEMPERATURE_PROFILE = "by temperature profile"
STR_MODE = "Mode"
STR_BEER_TEMP = "Beer temp"
STR_FRIDGE_TEMP = "Fridge temp"
STR_FMT_SET_TO = " set to %s "


class piLink:
    def __init__(self, tempControl, path):
        # Set up a pty to accept serial input as if we are an Arduino
        # FIXME: Make this a socket interface.  The main brewpi code can send to a socket.
        # use port 25518 (beer 2 5 5 18)
        os.setegid(20)
        master, slave = pty.openpty()

        # Disable echoing on slave so we don't interpret status strings as commands
        new_settings = termios.tcgetattr(slave)
        new_settings[3] = new_settings[3] & ~termios.ECHO
        termios.tcsetattr(slave, termios.TCSADRAIN, new_settings)

        port_name = os.ttyname(slave)
        os.chmod(port_name, 0o666)

        # Create a new symlink for our instance, as the pty
        # number can change each time.

        # First, delete the symlink for our instance, in case
        # we crashed last time.
        if os.path.islink(path):
            try:
                os.unlink(path)
            except Exception:
                pass

        os.symlink(port_name, path)

        print("Listening on '%s' as '%s'" % (port_name, path))
        self.f = os.fdopen(master, 'wb+', buffering=0)
        self.portName = port_name
        self.path = path
        self.buf = ''

        self.tempControl = tempControl
        self.tempControl.piLink = self  # FIXME is this good practice?

    def cleanup(self):
        # Delete the symlink for our instance when we exit
        if os.path.islink(self.path):
            try:
                os.unlink(self.path)
            except Exception:
                pass

    def updateBuffer(self):
        """ Fetch new data into the buffer and return the first character
        of the buffer
        """
        ready_to_read, ready_to_write, in_error = select.select([self.f], [], [], 0)

        # read a byte and append it to the buffer
        if ready_to_read:
            self.buf += self.f.read(1).decode("utf-8")  # Convert byte to character

        # return a single byte (if there is one)
        inByte = self.buf[0:]
        self.buf = self.buf[1:]
        return inByte

    def receive(self):

        inByte = self.updateBuffer()

        if inByte:

            if inByte in [' ', '\r', '\n']:
                pass

            elif inByte == 'A':  # alarm on
                print("Sound alarm request.  Not supported.")
                # soundAlarm(true)

            elif inByte == 'a':  # alarm off
                print("Silence alarm request.  Not supported.")
                # soundAlarm(false);

            elif inByte == 't':  # temperatures requested
                print("Temperature data request.")
                self.printTemperatures()

            elif inByte == 'C':  # Set default constants
                print("Set default constants request.")
                self.tempControl.loadDefaultConstants()
                # display.printStationaryText()	# FIXME reprint stationary text to update to right degree unit
                self.sendControlConstants(self.tempControl.cc)  # update script with new settings
                logging.info("INFO_DEFAULT_CONSTANTS_LOADED")

            elif inByte == 'S':  # Set default settings
                print("Set default settings request.")
                self.tempControl.loadDefaultSettings()
                self.sendControlSettings(self.tempControl.cs)  # update script with new settings
                logging.info("INFO_DEFAULT_SETTINGS_LOADED")

            elif inByte == 's':  # Control settings requested
                print("Control settings request.")
                self.sendControlSettings(self.tempControl.cs)

            elif inByte == 'c':  # Control constants requested
                print("Control constants request.")
                self.sendControlConstants(self.tempControl.cc)

            elif inByte == 'v':  # Control variables requested
                print("Control variables request.")
                self.sendControlVariables(self.tempControl.cv)

            elif inByte == 'n':  # Version request
                # PSTR(VERSION_STRING), // v:
                # PSTR(stringify(BUILD_NAME)), // n:
                # BREWPI_STATIC_CONFIG, // s:
                # BREWPI_SIMULATE, // y:
                # BREWPI_BOARD, // b:
                # BREWPI_LOG_MESSAGES_VERSION); // l:
                print("Version request.  Sending version.")
                vers = {"v": "0.2.11", "n": "fuscus", "s": 0, "y": 0, "b": "?", "l": "1"}
                self.f.write(bytes('N:' + json.dumps(vers) + '\r\n', 'UTF-8'))

            elif inByte == 'l':  # Display content requested
                print("LCD content request.")
                # Brewpi web interface has only 4 lines, so we don't send the whole buffer
                self.f.write(bytes('L:' + json.dumps(ui.LCD.buffer[:4]) + '\r\n', 'UTF-8'))

            elif inByte == 'j':  # Receive settings as json
                print("Incoming JSON settings.")
                self.receiveJson()

            elif inByte == 'E':  # initialize eeprom
                # FIXME not implemented
                # eepromManager.initializeEeprom()
                # logInfo(INFO_EEPROM_INITIALIZED)
                # settingsManager.loadSettings()
                pass

            elif inByte == 'd':  # list devices in eeprom order
                # FIXME not implemented
                # openListResponse('d')
                # deviceManager.listDevices(piStream)
                # closeListResponse()
                pass

            elif inByte == 'U':  # update device
                # FIXME not implemented
                # deviceManager.parseDeviceDefinition(piStream)
                pass

            elif inByte == 'h':  # hardware query
                # FIXME not implemented
                # openListResponse('h')
                # deviceManager.enumerateHardwareToStream(piStream)
                # closeListResponse()
                pass

            elif inByte == 'R':  # reset
                # FIXME not implemented
                # handleReset()
                pass

            elif inByte == 'F':  # flash firmware
                print("Flash firmware request.  Not supported.")
                # flashFirmware()

            elif inByte != '':
                # logWarningInt(WARNING_INVALID_COMMAND, inByte);
                print("Received '%s' character" % inByte)
            else:
                print("Got empty string.")

    def printTemperaturesJSON(self, beerAnnotation, fridgeAnnotation):
        temps = {}

        # For reference (COMPACT_SERIAL codes)
        # define JSON_BEER_TEMP  "bt"
        # define JSON_BEER_SET	"bs"
        # define JSON_BEER_ANN	"ba"
        # define JSON_FRIDGE_TEMP "ft"
        # define JSON_FRIDGE_SET  "fs"
        # define JSON_FRIDGE_ANN  "fa"
        # define JSON_STATE		"s"
        # define JSON_TIME		"t"
        # define JSON_ROOM_TEMP  "rt"

        '''COMPACT_SERIAL is not in use
        t = self.tempControl.getBeerTemp()
        if t:
            temps['bt'] = t

        t = self.tempControl.getBeerSetting()
        if t:
            temps['bs'] = t

        if beerAnnotation:
            temps['ba'] = beerAnnotation

        t = self.tempControl.getFridgeTemp()
        if t:
            temps['ft'] = t

        t = self.tempControl.getFridgeSetting()
        if t:
            temps['fs'] = t

        if fridgeAnnotation:
            temps['fa'] = fridgeAnnotation

        t = self.tempControl.getRoomTemp()
        if t:
            temps['rt'] = t

        temps['s'] = self.tempControl.getState()'''

        # These field names are in use
        # define JSON_BEER_TEMP  "BeerTemp"
        # define JSON_BEER_SET   "BeerSet"
        # define JSON_BEER_ANN   "BeerAnn"
        # define JSON_FRIDGE_TEMP "FridgeTemp"
        # define JSON_FRIDGE_SET  "FridgeSet"
        # define JSON_FRIDGE_ANN  "FridgeAnn"
        # define JSON_STATE              "State"
        # define JSON_TIME               "Time"
        # define JSON_ROOM_TEMP  "RoomTemp"

        temps['BeerTemp'] = self.tempControl.temp_convert_to_external(self.tempControl.getBeerTemp())
        temps['BeerSet'] = self.tempControl.temp_convert_to_external(self.tempControl.getBeerSetting())
        temps['BeerAnn'] = beerAnnotation
        temps['FridgeTemp'] = self.tempControl.temp_convert_to_external(self.tempControl.getFridgeTemp())
        temps['FridgeSet'] = self.tempControl.temp_convert_to_external(self.tempControl.getFridgeSetting())
        temps['FridgeAnn'] = fridgeAnnotation

        t = self.tempControl.temp_convert_to_external(self.tempControl.getRoomTemp())  # Room temp sensor may not be present
        if t:
            temps['RoomTemp'] = t

        temps['State'] = self.tempControl.getState()

        self.f.write(bytes('T:' + json.dumps(temps) + '\r\n', 'UTF-8'))

    def printBeerAnnotation(self, annotation):
        self.printTemperaturesJSON(annotation, None)

    def printFridgeAnnotation(self, annotation):
        self.printTemperaturesJSON(None, annotation)

        # def printResponse(type):

    #	pass
    # def openListResponse(type):
    #	pass
    # def closeListResponse():
    #	pass


    def debugMessage(message, *args):
        # FIXME: This probably won't work either
        return 'D' + message % args + '\r\n'

        # def sendJsonClose():

    #	pass


    def printTemperatures(self):
        """Print all temperatures with empty annotations."""
        self.printTemperaturesJSON(None, None)

    # If the JSONKEYs were the same as the variable names, we could do this:
    #	return 'C:'+json.dumps(vars(cc))+'\r\n'
    # Instead we have to do it the hard way

    def sendControlSettings(self, cs):
        d = vars(cs).copy()
        # Fix up the key names that are not the same
        d[JSONKEY_beerSetting] = self.tempControl.temp_convert_to_external(d.pop('beerSetting'))
        d[JSONKEY_fridgeSetting] = self.tempControl.temp_convert_to_external(d.pop('fridgeSetting'))
        d[JSONKEY_heatEstimator] = d.pop('heatEstimator')
        d[JSONKEY_coolEstimator] = d.pop('coolEstimator')

        self.f.write(bytes('S:' + json.dumps(d) + '\r\n', 'UTF-8'))

    def sendControlConstants(self, cc):
        d = vars(cc).copy()
        # Fix up the key names that are not the same
        d[JSONKEY_tempSettingMin] = self.tempControl.temp_convert_to_external(d.pop('tempSettingMin'))
        d[JSONKEY_tempSettingMax] = self.tempControl.temp_convert_to_external(d.pop('tempSettingMax'))
        d[JSONKEY_iMaxError] = self.tempControl.temp_convert_to_external(d.pop('iMaxError'), diff=True)
        d[JSONKEY_idleRangeHigh] = self.tempControl.temp_convert_to_external(d.pop('idleRangeHigh'), diff=True)

        d[JSONKEY_idleRangeLow] = self.tempControl.temp_convert_to_external(d.pop('idleRangeLow'), diff=True)
        d[JSONKEY_heatingTargetUpper] = self.tempControl.temp_convert_to_external(d.pop('heatingTargetUpper'), diff=True)
        d[JSONKEY_heatingTargetLower] = self.tempControl.temp_convert_to_external(d.pop('heatingTargetLower'), diff=True)
        d[JSONKEY_coolingTargetUpper] = self.tempControl.temp_convert_to_external(d.pop('coolingTargetUpper'), diff=True)
        d[JSONKEY_coolingTargetLower] = self.tempControl.temp_convert_to_external(d.pop('coolingTargetLower'), diff=True)
        d[JSONKEY_maxHeatTimeForEstimate] = d.pop('maxHeatTimeForEstimate')
        d[JSONKEY_maxCoolTimeForEstimate] = d.pop('maxCoolTimeForEstimate')
        # TODO - Determine if the filters have units (need to be converted)
        d[JSONKEY_fridgeFastFilter] = d.pop('fridgeFastFilter')
        d[JSONKEY_fridgeSlowFilter] = d.pop('fridgeSlowFilter')
        d[JSONKEY_fridgeSlopeFilter] = d.pop('fridgeSlopeFilter')
        d[JSONKEY_beerFastFilter] = d.pop('beerFastFilter')
        d[JSONKEY_beerSlowFilter] = d.pop('beerSlowFilter')
        d[JSONKEY_beerSlopeFilter] = d.pop('beerSlopeFilter')
        d[JSONKEY_lightAsHeater] = d.pop('lightAsHeater')
        d[JSONKEY_rotaryHalfSteps] = d.pop('rotaryHalfSteps')

        self.f.write(bytes('C:' + json.dumps(d) + '\r\n', 'UTF-8'))

    def sendControlVariables(self, cv):
        d = vars(cv).copy()
        # Fix up the key names that are not the same
        d[JSONKEY_estimatedPeak] = self.tempControl.temp_convert_to_external(d.pop('estimatedPeak'))
        d[JSONKEY_negPeakEstimate] = self.tempControl.temp_convert_to_external(d.pop('negPeakEstimate'))
        d[JSONKEY_posPeakEstimate] = self.tempControl.temp_convert_to_external(d.pop('posPeakEstimate'))

        self.f.write(bytes('V:' + json.dumps(d) + '\r\n', 'UTF-8'))

    def receiveControlConstants():
        # This does not seem to be defined in the original source
        pass

    def receiveJson(self):  # receive settings as JSON key:value pairs
        jsonBuf = ''

        timeout_after = datetime.datetime.now() + datetime.timedelta(seconds=1)  # 1 second timeout for receive

        while 1:
            inByte = self.updateBuffer()
            jsonBuf += inByte
            if inByte == '}':
                break
            if datetime.datetime.now() > timeout_after:  # If this takes longer than a second, something went wrong
                return

        jsonBuf = jsonBuf.replace(':', ': ')  # Fixup hacked JSON so YAML can read it

        newSettings = yaml.load(jsonBuf)

        print("New settings %s" % newSettings)

        # JSON_CONVERT(JSONKEY_mode, NULL, setMode),
        # JSON_CONVERT(JSONKEY_beerSetting, NULL, setBeerSetting),
        # JSON_CONVERT(JSONKEY_fridgeSetting, NULL, setFridgeSetting),

        if JSONKEY_mode in newSettings:
            self.setMode(newSettings[JSONKEY_mode])
        if JSONKEY_beerSetting in newSettings:
            self.setBeerSetting(newSettings[JSONKEY_beerSetting])
        if JSONKEY_fridgeSetting in newSettings:
            self.setFridgeSetting(newSettings[JSONKEY_fridgeSetting])

        # JSON_CONVERT(JSONKEY_heatEstimator, &tempControl.cs.heatEstimator, setStringToFixedPoint),
        # JSON_CONVERT(JSONKEY_coolEstimator, &tempControl.cs.coolEstimator, setStringToFixedPoint),

        if JSONKEY_heatEstimator in newSettings:
            self.tempControl.cs.heatEstimator = float(newSettings[JSONKEY_heatEstimator])

        if JSONKEY_coolEstimator in newSettings:
            self.tempControl.cs.coolEstimator = float(newSettings[JSONKEY_coolEstimator])

            # JSON_CONVERT(JSONKEY_tempFormat, NULL, setTempFormat),

        if JSONKEY_tempFormat in newSettings:
            self.setTempFormat(newSettings[JSONKEY_tempFormat])

        # JSON_CONVERT(JSONKEY_tempSettingMin, &tempControl.cc.tempSettingMin, setStringToTemp),
        # JSON_CONVERT(JSONKEY_tempSettingMax, &tempControl.cc.tempSettingMax, setStringToTemp),
        # JSON_CONVERT(JSONKEY_pidMax, &tempControl.cc.pidMax, setStringToTempDiff),

        # TODO - Check if these need to flip to use convert_to_internal
        if JSONKEY_tempSettingMin in newSettings:
            self.tempControl.cc.tempSettingMin = float(newSettings[JSONKEY_tempSettingMin])

        if JSONKEY_tempSettingMax in newSettings:
            self.tempControl.cc.tempSettingMax = float(newSettings[JSONKEY_tempSettingMax])

        if JSONKEY_pidMax in newSettings:
            # self.tempControl.cc.pidMax = self.tempControl.temp_convert_to_internal(float(newSettings[JSONKEY_pidMax]), diff=True)
            pass  # Not Implemented

        # JSON_CONVERT(JSONKEY_Kp, &tempControl.cc.Kp, setStringToFixedPoint),
        # JSON_CONVERT(JSONKEY_Ki, &tempControl.cc.Ki, setStringToFixedPoint),
        # JSON_CONVERT(JSONKEY_Kd, &tempControl.cc.Kd, setStringToFixedPoint),

        if JSONKEY_Kp in newSettings:
            self.tempControl.cc.Kp = float(newSettings[JSONKEY_Kp])

        if JSONKEY_Ki in newSettings:
            self.tempControl.cc.Ki = float(newSettings[JSONKEY_Ki])

        if JSONKEY_Kd in newSettings:
            self.tempControl.cc.Kd = float(newSettings[JSONKEY_Kd])

        # JSON_CONVERT(JSONKEY_iMaxError, &tempControl.cc.iMaxError, setStringToTempDiff),
        # JSON_CONVERT(JSONKEY_idleRangeHigh, &tempControl.cc.idleRangeHigh, setStringToTempDiff),
        # JSON_CONVERT(JSONKEY_idleRangeLow, &tempControl.cc.idleRangeLow, setStringToTempDiff),
        # JSON_CONVERT(JSONKEY_heatingTargetUpper, &tempControl.cc.heatingTargetUpper, setStringToTempDiff),
        # JSON_CONVERT(JSONKEY_heatingTargetLower, &tempControl.cc.heatingTargetLower, setStringToTempDiff),
        # JSON_CONVERT(JSONKEY_coolingTargetUpper, &tempControl.cc.coolingTargetUpper, setStringToTempDiff),
        # JSON_CONVERT(JSONKEY_coolingTargetLower, &tempControl.cc.coolingTargetLower, setStringToTempDiff),
        # JSON_CONVERT(JSONKEY_maxHeatTimeForEstimate, &tempControl.cc.maxHeatTimeForEstimate, setUint16),
        # JSON_CONVERT(JSONKEY_maxCoolTimeForEstimate, &tempControl.cc.maxCoolTimeForEstimate, setUint16),
        # JSON_CONVERT(JSONKEY_lightAsHeater, &tempControl.cc.lightAsHeater, setBool),
        # JSON_CONVERT(JSONKEY_rotaryHalfSteps, &tempControl.cc.rotaryHalfSteps, setBool),

        if JSONKEY_iMaxError in newSettings:
            self.tempControl.cc.iMaxError = self.tempControl.temp_convert_to_internal(float(newSettings[JSONKEY_iMaxError]), diff=True)

        if JSONKEY_idleRangeHigh in newSettings:
            self.tempControl.cc.idleRangeHigh = self.tempControl.temp_convert_to_internal(float(newSettings[JSONKEY_idleRangeHigh]), diff=True)

        if JSONKEY_idleRangeLow in newSettings:
            self.tempControl.cc.idleRangeLow = self.tempControl.temp_convert_to_internal(float(newSettings[JSONKEY_idleRangeLow]), diff=True)

        if JSONKEY_heatingTargetUpper in newSettings:
            self.tempControl.cc.heatingTargetUpper = self.tempControl.temp_convert_to_internal(float(newSettings[JSONKEY_heatingTargetUpper]), diff=True)

        if JSONKEY_heatingTargetLower in newSettings:
            self.tempControl.cc.heatingTargetLower = self.tempControl.temp_convert_to_internal(float(newSettings[JSONKEY_heatingTargetLower]), diff=True)

        if JSONKEY_coolingTargetUpper in newSettings:
            self.tempControl.cc.coolingTargetUpper = self.tempControl.temp_convert_to_internal(float(newSettings[JSONKEY_coolingTargetUpper]), diff=True)

        if JSONKEY_coolingTargetLower in newSettings:
            self.tempControl.cc.coolingTargetLower = self.tempControl.temp_convert_to_internal(float(newSettings[JSONKEY_coolingTargetLower]), diff=True)

        if JSONKEY_maxHeatTimeForEstimate in newSettings:
            self.tempControl.cc.maxHeatTimeForEstimate = int(newSettings[JSONKEY_maxHeatTimeForEstimate])

        if JSONKEY_maxCoolTimeForEstimate in newSettings:
            self.tempControl.cc.maxCoolTimeForEstimate = int(newSettings[JSONKEY_maxCoolTimeForEstimate])

        if JSONKEY_lightAsHeater in newSettings:
            self.tempControl.cc.lightAsHeater = int(newSettings[JSONKEY_lightAsHeater])

        if JSONKEY_rotaryHalfSteps in newSettings:
            self.tempControl.cc.rotaryHalfSteps = int(newSettings[JSONKEY_rotaryHalfSteps])

        print(vars(self.tempControl.cc))

    # FIXME Still to do
    # JSON_CONVERT(JSONKEY_fridgeFastFilter, MAKE_FILTER_SETTING_TARGET(FAST, FRIDGE), applyFilterSetting),
    # JSON_CONVERT(JSONKEY_fridgeSlowFilter, MAKE_FILTER_SETTING_TARGET(SLOW, FRIDGE), applyFilterSetting),
    # JSON_CONVERT(JSONKEY_fridgeSlopeFilter, MAKE_FILTER_SETTING_TARGET(SLOPE, FRIDGE), applyFilterSetting),
    # JSON_CONVERT(JSONKEY_beerFastFilter, MAKE_FILTER_SETTING_TARGET(FAST, BEER), applyFilterSetting),
    # JSON_CONVERT(JSONKEY_beerSlowFilter, MAKE_FILTER_SETTING_TARGET(SLOW, BEER), applyFilterSetting),
    # JSON_CONVERT(JSONKEY_beerSlopeFilter, MAKE_FILTER_SETTING_TARGET(SLOPE, BEER), applyFilterSetting)


    # FIXME A lot of unneeded code copied from original source should be deleted
    # static void (*ParseJsonCallback)(const char* key, const char* val, void* data);

    # static void parseJson(ParseJsonCallback fn, void* data=NULL);

    #	static void print(char *fmt, ...); // use when format string is stored in RAM
    #	static void print(char c)       // inline for arduino
    # ifdef ARDUINO
    #         { Serial.print(c); }
    # else
    #        ;
    # endif

    #	static void print_P(const char *fmt, ...); // use when format string is stored in PROGMEM with PSTR("string")
    #	static void printNewLine(void);

    def printChamberCount():
        pass

    def soundAlarm(enabled):
        pass

    def printChamberInfo():
        pass

    def sendJsonPair(name, val):  # send one JSON pair with a string value as name:val,
        pass

    #	static void sendJsonPair(const char * name, char val); // send one JSON pair with a char value as name:val,
    #	static void sendJsonPair(const char * name, uint16_t val); // send one JSON pair with a uint16_t value as name:val,
    #	static void sendJsonPair(const char * name, uint8_t val); // send one JSON pair with a uint8_t value as name:val,
    def sendJsonAnnotation(name, annotation):
        pass

    def sendJsonTemp(name, temp):
        pass

    def processJsonPair(key, val, pv):  # process one pair
        pass

    #	/* Prints the name part of a json name/value pair. The name must exist in PROGMEM */
    def printJsonName(name):
        pass

    def printJsonSeparator():
        pass

    #	struct JsonOutput {
    #		const char* key;			// JSON key
    #		uint8_t offset;			// offset into TempControl class
    #		uint8_t handlerOffset;		// handler index
    #	};
    #	typedef void (*JsonOutputHandler)(const char* key, uint8_t offset);
    #	static void sendJsonValues(char responseType, const JsonOutput* /*PROGMEM*/ jsonOutputMap, uint8_t mapCount);


    # handler functions for JSON output
    def jsonOutputUint8(key, offset):
        pass

    def jsonOutputTempToString(key, offset):
        pass

    def jsonOutputFixedPointToString(key, offset):
        pass

    def jsonOutputTempDiffToString(key, offset):
        pass

    def jsonOutputChar(key, offset):
        pass

    def jsonOutputUint16(key, offset):
        pass

    #	static const JsonOutputHandler JsonOutputHandlers[];
    #	static const JsonOutput jsonOutputCCMap[];
    #	static const JsonOutput jsonOutputCVMap[];

    # Json parsing

    def setMode(self, val):
        mode = val[0]
        self.tempControl.setMode(mode)
        self.printFridgeAnnotation(STR_MODE + (STR_FMT_SET_TO % val) + STR_WEB_INTERFACE)

    def setBeerSetting(self, newTemp):
        source = None
        if (self.tempControl.cs.mode == 'p'):
            if (self.tempControl.cs.beerSetting is not None and (abs(
                        newTemp - self.tempControl.cs.beerSetting) > 0.2)):  # this excludes gradual updates under 0.2 degrees
                source = STR_TEMPERATURE_PROFILE
        else:
            source = STR_WEB_INTERFACE

        if (source):
            self.printBeerAnnotation(STR_BEER_TEMP + (STR_FMT_SET_TO % newTemp) + source)

        self.tempControl.setBeerTemp(newTemp)

    def setFridgeSetting(self, newTemp):
        if (self.tempControl.cs.mode == 'f'):
            self.printFridgeAnnotation(STR_FRIDGE_TEMP + (STR_FMT_SET_TO % newTemp) + STR_WEB_INTERFACE)

        self.tempControl.setFridgeTemp(newTemp)

    def setTempFormat(self, val):
        # Only Celsius for now
        # TODO - Implement Fahrenheit
        self.tempControl.setTempFormat(val)
        pass

    #	typedef void (*JsonParserHandlerFn)(const char* val, void* target);

    #	struct JsonParserConvert {
    #		const char* /*PROGMEM*/ key;
    #		void* target;
    #		JsonParserHandlerFn fn;
    #	};

    #	static const JsonParserConvert jsonParserConverters[];
