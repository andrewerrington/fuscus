## Getting fuscus running with Jessie Lite.
1. Download and install latest Raspbian image.  Log in as **pi**.
2. Use *sudo raspi-config* to expand the filesystem and enable Device Tree and SPI (and anything else you like, such as setting the timezone).  Optionally change the hostname to "brewpi".
3. Use *sudo apt-get update* and *sudo apt-get upgrade* to bring the OS up to date.
4. Edit **/boot/config.txt** and add **dtoverlay=w1-gpio** to support the 1-wire bus
5. Install required packages:  
*sudo apt-get install python3 python3-pip git-core*
6. Install Python packages:  
*sudo pip3 install spidev RPi.GPIO pyyaml* (spi is needed by the pcd8544 LCD module)
7. *sudo adduser fuscus* (to make a new user for fuscus code)
8. *sudo adduser fuscus sudo* (because fuscus needs to write to GPIO)
9. Use *sudo visudo* to add this line to allow fuscus to run the python file without needing a password  
**fuscus ALL = NOPASSWD: /home/fuscus/fuscus/fuscus.py**
10. Optionally configure wifi using:  
https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md
11. Optionally check/configure temperature sensors using this code:  
https://www.raspberrypi.org/forums/viewtopic.php?f=37&t=77611
12. Copy fuscus code from github  
We are going to copy the fuscus source code from the fuscus subdirectory in the git repository into the fuscus home directory, and ignore the other files.  
login as **fuscus**  
*git init*  
*git remote add -f origin https://github.com/andrewerrington/fuscus.git*  
*git config core.sparseCheckout true*  
*echo "fuscus/" >> .git/info/sparse-checkout*  
*git pull origin master*  
Now the source is in /fuscus, with no docs or other files.
13. Change to the fuscus directory and edit the **fuscus.ini** to enter
your temperature sensor IDs and other settings. A sample fuscus.ini is
saved as **fuscus.sample.ini.**  
*cd fuscus*  
*cp fuscus.sample.ini fuscus.ini*  
*nano fuscus.ini*  
14. Run fuscus  
*sudo ./fuscus.py*
15. Log in as **pi** and install brewpi software using these instructions:  
http://docs.brewpi.com/automated-brewpi-install/automated-brewpi-install.html
16. Edit **~brewpi/settings/config.cfg** to change the port setting to **port = /dev/fuscus** (or whatever you specify in fuscus.ini)
17. If you see an error *[Errno 22] Invalid argument* from BrewPi then edit BrewPiUtil.py.  Add **dsrdtr=True** and **rtscts=True** to the *ser = serial.Serial* line, around line 132:  
**ser = serial.Serial(port, baudrate=baud_rate, timeout=time_out, write_timeout=0, dsrdtr=True, rtscts=True)**  
The background of this bug is here:  
https://github.com/bewest/decoding-carelink/pull/171  

Note that you can run fuscus in a *screen* session for experimenting, or
you can add the command to start fuscus to the fuscus user's crontab in
a *@reboot* entry.  An example @reboot entry which discards normal output and logs everything sent to stderr is:
*@reboot sudo /<path to fuscus>/fuscus.py -c /<path to fuscus>/fuscus.ini 1>/dev/null 2>>/home/fuscus/stderr.txt &*

When fuscus is running it will listen on /dev/fuscus for a connection
from BrewPi.  BrewPi will attempt to connect every minute.  This means
you may have to wait for up to one minute for BrewPi to connect to fuscus
and start getting data.

## Optional - Sensor Calibration
Fuscus provides a feature to adjust each measurement from your sensors if
they read a little high or low.  To use it, do the following:  
1. Calibrate your sensors by measuring the temperature they report, and
determining the offset from a known temperature reading.  
2. Create the calibration file and open for editing in your favorite editor:  
*cp calibrate.sample.ini calibrate.ini*  
*sudo nano calibrate.ini*  
3. Add the device ID for your sensor along with the offset in degrees
Celsius to be added to each reading. For example:  
*28-031590ed07ff = 0.4*  
would result in sensor 28-031590ed07ff having 0.4 degrees Celsius added
to each reading. Please note - The offsets must always be in degrees 
Celsius, even when running in Fahrenheit mode.


## Notes for later development
Change the line in BrewPiUtil.py around line 130:
ser = serial.Serial(port, baudrate=baud_rate, timeout=time_out)
to
ser = serial.serial_for_url(port, baudrate=baud_rate, timeout=time_out)
This will allow brewpi to connect to a serial port *or* a socket

Change the port variable in the config.cfg file from this:
port = /dev/ttyACM0
to
port = socket://localhost:25518

Fully test the Fahrenheit conversion code to ensure that it works properly with beer profiles

