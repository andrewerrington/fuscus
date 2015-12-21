## Getting fuscus running
1. Download and install latest Raspbian image.
2. Use *sudo raspi-config* to expand the filesystem and enable Device Tree and SPI (and anything else you like, such as setting the timezone).  Optionally change the hostname to "brewpi".
3. Use *sudo apt-get update* and *sudo apt-get upgrade* to bring the OS up to date.
4. *sudo adduser fuscus* (to make a new user for fuscus code)
5. *sudo adduser fuscus sudo* (because fuscus needs to write to GPIO)
6. Edit **/boot/config.txt** and add **dtoverlay=w1-gpio** to support the 1-wire bus
7. Use *sudo apt-get install python3-pip* and then *sudo pip-3.2 install spidev* (spi is needed by the pcd8544 LCD module)
8. Optionally configure wifi using:
https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md
9. Optionally check/configure temperature sensors using this code:
https://www.raspberrypi.org/forums/viewtopic.php?f=37&t=77611
10. Install brewpi software using these instructions:
http://docs.brewpi.com/automated-brewpi-install/automated-brewpi-install.html
11. Use *sudo visudo* to add this line to allow fuscus to run the python file without needing a password
**fuscus ALL = NOPASSWD: /home/fuscus/fuscus.py**
12. Edit **~brewpi/settings/config.cfg** to change the port setting to **/dev/pts/0** (or whatever fuscus reports when it runs)
13. Install YAML: sudo pip-3.2 install pyyaml
14. Run fuscus with *sudo ./fuscus.py*

## Later development
Change the line in BrewPiUtil.py around line 130:
ser = serial.Serial(port, baudrate=baud_rate, timeout=time_out)
to
ser = serial.serial_for_url(port, baudrate=baud_rate, timeout=time_out)
This will allow brewpi to connect to a serial port *or* a socket

Change the port variable in the config.cfg file from this:
port = /dev/ttyACM0
to
port = socket://localhost:25518


