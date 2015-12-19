# Fuscus

Fuscus is the Latin name for the Brown Water-Python.  It is also the name
chosen for this native Python implementation of the BrewPi fermentation
controller.

BrewPi (http://www.brewpi.com) is an Open Source temperature controller
for brewing beer or wine, designed and developed by Elco Jacobs.  It
initially comprised of a Raspberry Pi and Arduino, but in 2015 the Arduino
was retired and replaced with a Particle Photon.  In both of these
implementations the Raspberry Pi handles data logging and the web interface
for the system.  The Arduino or Photon handles the temperature sensing and
PID control of a heater or cooler.  A serial link joins the two parts of
the system together.

There are very good reasons for allocating a microcontroller to the
task of heating and cooling control.  The primary one being that they
are very reliable.  If the Raspberry Pi should crash the microcontroller
will continue to monitor and maintain the last set temperature.  If
the control is done by the Pi then it could crash and leave the heater
or cooler stuck on, which will ruin the fermentation.

Despite the possible risks of failure and loss this project re-implements
the Arduino control code (v0.2.11) in Python so that it can run natively on
the Pi.  The other BrewPi components (brewpi-www and brewpi-script) will
talk to this Python code as if it were an Arduino, so they can be be used
unchanged.  Hardware that was connected to the Arduino, such as 1-wire
temperature sensors, an LCD, and relays for the heater and cooler are
connected to the Pi GPIO pins.
