#!/usr/bin/env python3
import DS18B20
import sys
import time
import os
import datetime

# Get a list of temperature sensors and report their values every second.
# The W1 driver must be working.

sensors = []

devices = os.listdir("/sys/bus/w1/devices/")

for device in devices:
    if device[:2] == "28":
        print("Found device: %s" % device)
        sensors.append(DS18B20.DS18B20(device))

if not sensors:
    print("No sensors found in /sys/bus/w1/devices")
    sys.exit()
else:
    print("Found %s temperature sensors." % len(sensors))
    print()

try:
    print("Starting threads for %s sensors." % len(sensors))
    for sensor in sensors:
        print("Starting %s" % sensor.deviceID)
        sensor.start()

    while (True):
        time.sleep(1)  # You can read the sensor as often as you like,
        # but it only changes every samplePeriod seconds.
        print()
        print("%s Ctrl-C to stop." % datetime.datetime.utcnow())
        for sensor in sensors:
            print(sensor.deviceID, sensor.temperature)  # Result is float in degrees C,
        # or None for error

except KeyboardInterrupt:
    print()
    print("Ctrl-C detected.  Stopping.")

except:
    print("Temperature sensor error:", sys.exc_info()[0])
    raise

finally:
    print("Stopping threads for %s sensors." % len(sensors))
    for sensor in sensors:
        print("Stopping %s." % sensor.deviceID)
        sensor.stop()
        print("Waiting for %s to finish." % sensor.deviceID)
        sensor.join()

print("Done.")
