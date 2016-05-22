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

import time
import ticks

import displayLCD as display
from tempControl import MODES, STATES

MENU_TIMEOUT = 10
LOOKUP = ("b", "f", "p", "o")


class Menu:
    def __init__(self, encoder, tempControl, piLink):
        self.encoder = encoder
        self.tempControl = tempControl
        self.piLink = piLink

    def pickSettingToChange(self):
        # ensure beer temp is displayed
        oldFlags = display.getDisplayFlags()
        display.setDisplayFlags(oldFlags &
                                ~(display.LCD_FLAG_ALTERNATE_ROOM | display.LCD_FLAG_DISPLAY_ROOM))
        self.pickSettingToChangeLoop()
        display.setDisplayFlags(oldFlags)

    def pickMode(self):
        oldSetting = self.tempControl.getMode()
        startValue = LOOKUP.index(oldSetting)
        # rotaryEncoder.setRange(startValue, 0, 3)	# toggle between beer constant, beer profile, fridge constant

        if not self.blinkLoop(self.changedMode, display.printMode, self.clearMode, self.selectMode):
            self.tempControl.setMode(oldSetting)

    def pickBeerSetting(self):
        self.pickTempSetting(self.tempControl.getBeerSetting, self.tempControl.setBeerTemp,
                             "Beer", self.piLink.printBeerAnnotation, 1)

    def pickFridgeSetting(self):
        self.pickTempSetting(self.tempControl.getFridgeSetting, self.tempControl.setFridgeTemp,
                             "Fridge", self.piLink.printFridgeAnnotation, 2)

    def initRotaryWithTemp(self, oldSetting):
        pass

    def pickSettingToChangeLoop(self):
        # rotaryEncoder.setRange(0, 0, 2)	# mode setting, beer temp, fridge temp
        self.blinkLoop(
            self.settingChanged,
            display.printStationaryText,
            self.clearSettingText,
            self.settingSelected
        )

    def settingChanged(self):
        pass  # no -op - the only change is to update the display which happens already

    def settingSelected(self):
        # switch(rotaryEncoder.read()){
        sel = self.encoder.pos % 3
        if sel == 0:
            self.pickMode()
        elif sel == 1:
            # switch to beer constant, because beer setting will be set through display
            self.tempControl.setMode(MODES['MODE_BEER_CONSTANT'])
            display.printMode()
            self.pickBeerSetting()
        elif sel == 2:
            # switch to fridge constant, because fridge setting will be set through display
            self.tempControl.setMode(MODES['MODE_FRIDGE_CONSTANT'])
            display.printMode()
            self.pickFridgeSetting()

    def changedMode(self):
        self.tempControl.setMode(LOOKUP[self.encoder.pos % (len(LOOKUP))])

    def clearMode(self):
        display.printAt(7, 0, " " * 13)  # print 13 spaces

    def selectMode(self):
        mode = self.tempControl.getMode()
        if (mode == MODES['MODE_BEER_CONSTANT']):
            self.pickBeerSetting()
        elif (mode == MODES['MODE_FRIDGE_CONSTANT']):
            self.pickFridgeSetting()
        elif (mode == MODES['MODE_BEER_PROFILE']):
            self.piLink.printBeerAnnotation("Changed to profile mode in menu.")
        elif (mode == MODES['MODE_OFF']):
            self.piLink.printBeerAnnotation("Temp control turned off in menu.")

    def blinkLoop(self,
                  changed,  # function called to update the value
                  show,  # function called to show the current value
                  hide,  # function called to blank out the current value
                  pushed):  # function to handle selection

        # @return {@code true} if a value was selected. {@code false} on timeout.
        lastChangeTime = ticks.seconds()
        blinkTimer = 0

        while (ticks.timeSince(lastChangeTime) < MENU_TIMEOUT):  # time out at 10 seconds
            if (self.encoder.changed):
                lastChangeTime = ticks.seconds()
                blinkTimer = 0
                changed()
                display.update()

            if (blinkTimer == 0):
                show()
                display.update()

            elif (blinkTimer == 128):
                hide()
                display.update()

            if (self.encoder.pushed):
                # rotaryEncoder.resetPushed()
                show()
                display.update()
                while self.encoder.pushed:
                    pass
                pushed()
                return True

            blinkTimer += 1
            blinkTimer &= 0xff  # blink timer is an 8-bit value
            time.sleep(0.003)  # wait.millis(3)	# delay for blinking

        return False

    def clearSettingText(self):
        # display.printAt_P(0, rotaryEncoder.read(), STR_6SPACES)
        display.printAt(0, self.encoder.pos % 3, " " * 6)

    def pickTempSetting(self, readTemp, writeTemp, tempName, printAnnotation, row):

        # Handle temperatures as integers internally, with a resolution of 0.1C
        # i.e. divide by 10
        oldSetting = readTemp()
        startVal = oldSetting
        minVal = int(self.tempControl.cc.tempSettingMin * 10)
        maxVal = int(self.tempControl.cc.tempSettingMax * 10)
        if oldSetting is None:  # previous temperature was not defined, start at 20C
            startVal = 20.0

        startVal *= 10
        t = float(startVal) / 10

        startPos = self.encoder.pos  # The encoder is free-running, so establish zero point

        # rotaryEncoder.setRange(startVal, minVal, maxVal)

        blinkTimer = 0
        lastChangeTime = ticks.seconds()

        while (ticks.timeSince(lastChangeTime) < MENU_TIMEOUT):  # time out at 10 seconds
            if (self.encoder.changed):
                lastChangeTime = ticks.seconds()
                blinkTimer = 0
                # startVal = tenthsToFixed(encoder.read())
                t = startVal + (self.encoder.pos - startPos)
                t = max(minVal, min(t, maxVal))
                t = float(t) / 10

                display.printTemperatureAt(12, row, t)
                display.update()

            if (self.encoder.pushed):
                # rotaryEncoder.resetPushed()
                writeTemp(t)
                printAnnotation("%s temp set to %s in Menu." % (tempName, t))
                while self.encoder.pushed:
                    pass
                return True

            if (blinkTimer == 0):
                display.printTemperatureAt(12, row, t)
                display.update()

            elif (blinkTimer == 128):
                display.printAt(12, row, " " * 5)
                display.update()

            blinkTimer += 1
            blinkTimer &= 0xff  # Blink timer is an 8-bit value
            time.sleep(0.003)  # delay for blinking

        # Time Out. Setting is not written
        return False  # FIXME: Do something if the encoder is not pushed
