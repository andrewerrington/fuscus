## Usage
1. Download and install Raspbian, and set up the Raspberry Pi to support SPI, 1-Wire, etc.
2. Log in as **pi** and install brewpi software using these instructions:
http://docs.brewpi.com/automated-brewpi-install/automated-brewpi-install.html
3. Download this script into the home directory for **pi** and run setup.sh:
`git clone https://github.com/thorrak/fuscus_tools`
`sudo ~/fuscus_tools/setup.sh`
4. Follow the prompts to install Fuscus
5. Configure Fuscus & BrewPi
6. Launch Fuscus:
**As user Fuscus:** `sudo ~fuscus/fuscus/fuscus.py`
7. *(Optional, but recommended)* Set up crontab to launch Fuscus at reboot
8. *(Optional)* Calibrate the temperature sensors

## Fuscus Configuration
Following installation, Fuscus still requires configuration. **Please note** - this is an important step. If you attach hardware to your Raspberry Pi without customizing and completing setup, Fuscus may do bad things. Think: turn on your heater instead of your cooler and leave it on, freeze your beer, etc.
1. Change to the 'fuscus' user and change to the install directory
`sudo su fuscus`
`cd ~fuscus/fuscus/`
2. Open the sample configuration file in your editor:
`nano ~fuscus/fuscus/fuscus.sample.ini`
3. Update the configuration to match your installation.
4. Close & save the file, then rename it to 'fuscus.ini':
`mv fuscus.sample.ini fuscus.ini`
5. Edit **~brewpi/settings/config.cfg** to change the port setting to
**port = /dev/fuscus** (or whatever you specify in **fuscus.ini**)


## Set up crontab to launch Fuscus at reboot

*Coming soon.*



## Troubleshooting
If you see an error *[Errno 22] Invalid argument* from BrewPi then
edit BrewPiUtil.py.  Add **dsrdtr=True** and **rtscts=True** to the
*ser = serial.Serial* line, around line 132:
**ser = serial.Serial(port, baudrate=baud_rate, timeout=time_out, write_timeout=0, dsrdtr=True, rtscts=True)**

The background of this bug is here:
https://github.com/bewest/decoding-carelink/pull/171


