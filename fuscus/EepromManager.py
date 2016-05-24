#!/usr/bin/env python3

# /*
#  * Copyright 2013 BrewPi/Elco Jacobs.
#  * Copyright 2013 Matthew McGowan
#  *
#  * This file is part of BrewPi.
#  *
#  * BrewPi is free software: you can redistribute it and/or modify
#  * it under the terms of the GNU General Public License as published by
#  * the Free Software Foundation, either version 3 of the License, or
#  * (at your option) any later version.
#  *
#  * BrewPi is distributed in the hope that it will be useful,
#  * but WITHOUT ANY WARRANTY; without even the implied warranty of
#  * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  * GNU General Public License for more details.
#  *
#  * You should have received a copy of the GNU General Public License
#  * along with BrewPi.  If not, see <http://www.gnu.org/licenses/>.
#  */



class eepromManager:
    def __init__(self, tempControl):
        self.settings_are_loaded = False
        self.tempControl = tempControl
        self.tempControl.eepromManager = self  # This is bad practice, but it accomplishes what the firmware needs

    def hasSettings(self):
        # In the arduino version, this works by reading a "version" number which is saved to the eeprom and returning
        # that. Instead, we'll test if the 'settings' files exist - and return True or False based on that.
        # That check, however, lives in the tempControl class (because that's where the eeprom settings load/save
        # functionality exists)
        return self.tempControl.hasStoredSettings()

    def zapEeprom(self):
        # In the arduino version, this is implmented by writing over the eeprom with 0xFF. Instead, we're going to
        # just delete the two files. Since those files are created/managed in tempControl, I've moved the code there.
        self.tempControl.zapStoredSettings()

    def initializeEeprom(self):
        # Fundamentally, the arduino version of this does the following:
        # 1. Zap the eeprom
        self.zapEeprom()
        # TODO - 2. Set up unconfigured devices
        #     deviceManager.setupUnconfiguredDevices();
        # 3. Load default constants
        self.tempControl.loadDefaultConstants()
        # 4. Load default settings
        self.tempControl.loadDefaultSettings()
        # 5. Save constants / 6. Save settings
        self.storeTempConstantsAndSettings()
        # 7. Store the version flag - Note - this is deprecated in Fuscus by tempControl.hasStoredSettings
        # 8. Save devices
        self.saveDefaultDevices()  # This doesn't do anything.
        # 9. Initialize temperature control
        self.tempControl.initFilters()


    def saveDefaultDevices(self):
        return False  # Appears to be unimplemented in the original file


    def applySettings(self):
        # If there aren't any settings saved, load the defaults & then write them out to a file.
        if not self.hasSettings():
            self.tempControl.loadDefaultConstants()
            self.tempControl.loadDefaultSettings()
            # TODO - Implement deviceManager.setupUnconfiguredDevices()
            self.storeTempConstantsAndSettings()  # NOTE - This isn't actually called in the Arduino version
            return True

        #
        # 	// start from a clean state
        # 	deviceManager.setupUnconfiguredDevices();
        #
        # 	logDebug("Applying settings");
        #
        # 	// load the one chamber and one beer for now
        self.tempControl.loadConstants()
        self.tempControl.loadSettings()
        # 	logDebug("Applied settings");

        # TODO - Implement device configuration

        # 	DeviceConfig deviceConfig;
        # 	for (uint8_t index = 0; fetchDevice(deviceConfig, index); index++)
        # 	{
        # 		if (deviceManager.isDeviceValid(deviceConfig, deviceConfig, index))
        # 			deviceManager.installDevice(deviceConfig);
        # 		else {
        # 			clear((uint8_t*)&deviceConfig, sizeof(deviceConfig));
        # 			eepromManager.storeDevice(deviceConfig, index);
        # 		}
        # 	}
        # 	return true;
        # }
        return True


    def storeTempSettings(self):
        self.tempControl.storeSettings()

    def storeTempConstantsAndSettings(self):
        self.tempControl.storeConstants()
        self.storeTempSettings()


    def fetchDevice(self):
        # TODO - Implement
        # bool EepromManager::fetchDevice(DeviceConfig& config, uint8_t deviceIndex)
        # {
        #     bool ok = (hasSettings() && deviceIndex<EepromFormat::MAX_DEVICES);
        #     if (ok)
        #         eepromAccess.readBlock(&config, pointerOffset(devices)+sizeof(DeviceConfig)*deviceIndex, sizeof(DeviceConfig));
        #     return ok;
        # }
        pass

    def storeDevice(self):
        # TODO - Implement
        # bool EepromManager::storeDevice(const DeviceConfig& config, uint8_t deviceIndex)
        # {
        #     bool ok = (hasSettings() && deviceIndex<EepromFormat::MAX_DEVICES);
        #     if (ok)
        #         eepromAccess.writeBlock(pointerOffset(devices)+sizeof(DeviceConfig)*deviceIndex, &config, sizeof(DeviceConfig));
        #     return ok;
        # }
        pass

