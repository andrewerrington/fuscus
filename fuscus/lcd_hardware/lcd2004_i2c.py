'''
Copyright (C) 2012 Matthew Skolaut

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Copyright (C) 2012-2106 John Beeler
Original source:

'''

import smbus
from time import *

PYLCD_LOWER_COMMANDS = 0
PYLCD_LCD2004 = 1
PYLCD_LCD2004_BL = 3



CMD_CLEAR 			= 0x01
CMD_HOME 			= 0x02
CMD_ENTRY_L 		= 0x04
CMD_ENTRY_LS	 	= 0x05
CMD_ENTRY_R 		= 0x06
CMD_ENTRY_RS 		= 0x07
CMD_DISP_OFF 		= 0x08
CMD_DISP_ON 		= 0x0C
CMD_CURS_OFF 		= 0x0C
CMD_CURS_SLD 		= 0x0E
CMD_CURS_BLINK 		= 0x0F
CMD_SHIFT_CURS_L1 	= 0x10
CMD_SHIFT_CURS_R1 	= 0x14
CMD_SHIFT_DISP_L1 	= 0x18
CMD_SHIFT_DISP_R1 	= 0x1C
CMD_4BIT_1L 		= 0x20
CMD_FUNCTIONSET = CMD_4BIT_1L
CMD_4BIT_2L 		= 0x28
CMD_8BIT_1L 		= 0x30
CMD_8BIT_2L 		= 0x38

ADDR_L1				= 0x80
ADDR_L2				= 0x80 + 0x40
ADDR_L3				= 0x80 + 0x20
ADDR_L4				= 0x80 + 0x60
ADDR_FNT			= 0x40


# General i2c device class so that other devices can be added easily
class i2c_device:
    def __init__(self, addr, port):
        self.addr = addr
        self.bus = smbus.SMBus(port)

    def write(self, byte):
        self.bus.write_byte(self.addr, byte)

    def read(self):
        return self.bus.read_byte(self.addr)

    def read_nbytes_data(self, data, n): # For sequential reads > 1 byte
        return self.bus.read_i2c_block_data(self.addr, data, n)




class lcd2004_i2c:
    #initializes objects and lcd
    '''
    Reverse Codes:
    0: lower 4 bits of expander are commands bits
    1: top 4 bits of expander are commands bits AND P0-4 P1-5 P2-6 (Use for "LCD2004" board)
    2: top 4 bits of expander are commands bits AND P0-6 P1-5 P2-4
    3: "LCD2004" board where lower 4 are commands, but backlight is pin 3
    '''
    def __init__(self, addr, port=1, reverse=0, backlight_pin=-1, en_pin=-1, rw_pin=-1, rs_pin=-1, d4_pin=-1, d5_pin=-1, d6_pin=-1, d7_pin=-1):
        self.reverse = reverse
        self.lcd_device = i2c_device(addr, port)

        self.pins=[i for i in range(8)] # Initialize the list
        self.backlight_status=1<<7 # Initialize with backlight as on (Change self.backlight to 0 to turn off backlight pin)

        if d7_pin != -1: # Manually set pins, in case we have a different backpack pinout
            self.pins[0]=d4_pin
            self.pins[1]=d5_pin
            self.pins[2]=d6_pin
            self.pins[3]=d7_pin
            self.pins[4]=rs_pin
            self.pins[5]=rw_pin
            self.pins[6]=en_pin
            self.pins[7]=backlight_pin

        elif self.reverse==1: # 1: top 4 bits of expander are commands bits AND P0-4 P1-5 P2-6 (Use for "LCD2004" board)
            self.pins[0]=4	 	# D4 Pin
            self.pins[1]=5 		# D5 Pin
            self.pins[2]=6 		# D6 Pin
            self.pins[3]=7 		# D7 Pin
            self.pins[4]=0 		# RS Pin
            self.pins[5]=1 		# RW Pin
            self.pins[6]=2 		# EN Pin
            self.pins[7]=3 		# Backlight Pin

        elif self.reverse==2: # 2: top 4 bits of expander are commands bits AND P0-6 P1-5 P2-4
            self.pins[0]=4	 	# D4 Pin
            self.pins[1]=5 		# D5 Pin
            self.pins[2]=6 		# D6 Pin
            self.pins[3]=7 		# D7 Pin
            self.pins[4]=0 		# RS Pin
            self.pins[5]=1 		# RW Pin
            self.pins[6]=2 		# EN Pin
            self.pins[7]=3 		# Backlight Pin

        elif self.reverse==3:
            self.pins[0]=0	 	# D4 Pin
            self.pins[1]=1 		# D5 Pin
            self.pins[2]=2 		# D6 Pin
            self.pins[3]=3 		# D7 Pin
            self.pins[4]=4 		# RS Pin
            self.pins[5]=5 		# RW Pin
            self.pins[6]=7 		# EN Pin
            self.pins[7]=6 		# Backlight Pin

        else:
            # self.pins is already initialized to this, but broken out here for clarity
            self.pins[0]=0	 	# D4 Pin
            self.pins[1]=1 		# D5 Pin
            self.pins[2]=2 		# D6 Pin
            self.pins[3]=3 		# D7 Pin
            self.pins[4]=4 		# RS Pin
            self.pins[5]=5 		# RW Pin
            self.pins[6]=6 		# EN Pin
            self.pins[7]=7 		# Backlight Pin


        # This begins the actual initialization sequence
        self.lcd_device_write(0x03) # Prepare to switch to 4 bit mode
        self.lcd_strobe()
        sleep(0.0005)
        self.lcd_strobe()
        sleep(0.0005)
        self.lcd_strobe()
        sleep(0.0005)

        self.lcd_device_write(0x02) # Set 4 bit mode
        self.lcd_strobe()
        sleep(0.0005)


        # Initialize
        self.lcd_write(CMD_4BIT_2L)  # Set 4 bit, 2 line mode (Multi-line)
        self.lcd_write(CMD_DISP_OFF)  # Hide cursor, don't blink
        self.lcd_write(CMD_CLEAR)  # Clear display, move cursor home
        self.lcd_write(CMD_ENTRY_R)
        # self.lcd_write(CMD_CURS_BLINK)
        self.lcd_write(CMD_DISP_ON)  # Turn on display

        self.lcd_write(0x03)
        self.lcd_write(0x03)
        self.lcd_write(0x03)
        self.lcd_write(0x02)

        # self.lcd_write(CMD_FUNCTIONSET | LCD_2LINE | LCD_5x8DOTS | LCD_4BITMODE)
        # self.lcd_write(LCD_DISPLAYCONTROL | LCD_DISPLAYON)
        # self.lcd_write(LCD_CLEARDISPLAY)
        # self.lcd_write(LCD_ENTRYMODESET | LCD_ENTRYLEFT)


    # clocks EN to latch command
    def lcd_strobe(self):
        self.lcd_device_write(self.lastcomm | (1<<6), 1) # 1<<6 is the enable pin
        self.lcd_device_write(self.lastcomm,1)  # Technically not needed, but included so we can read from the display

    # write a command to lcd
    def lcd_write(self, cmd):
        self.lcd_device_write((cmd >> 4)) # Write the first 4 bits (nibble) of the command
        self.lcd_strobe()
        self.lcd_device_write((cmd & 0x0F)) # Write the second nibble of the command
        self.lcd_strobe()
        self.lcd_device_write(0x0) # Technically not needed

    # write a character to lcd (or character rom)
    def lcd_write_char(self, charvalue):
        self.lcd_device_write(((1<<4) | (charvalue >> 4))) # Originally this was 0x40
        self.lcd_strobe()
        self.lcd_device_write(((1<<4) | (charvalue & 0x0F))) # Originally this was 0x40
        self.lcd_strobe()
        self.lcd_device_write(0x0)

    # put char function
    def lcd_putc(self, char):
        self.lcd_write_char(ord(char))


    # Do clunky bitshifting to account for strangely wired boards
    # I guarantee there is an easier way of doing this.
    def lcd_device_write(self, commvalue, isstrobe=0):
        tempcomm=commvalue | self.backlight_status
        outcomm=[0 for i in range(8)]

        for a in range(0,8):
            outcomm[self.pins[a]]=(tempcomm & 1)
            tempcomm=tempcomm>>1

        tempcomm=0
        a=7
        while (a >= 0):
            tempcomm=(tempcomm<<1)|outcomm[a]
            a=a-1;

        self.lcd_device.write(tempcomm)
        # sleep(0.0005) # May be unnecessary, but including to guarantee we don't push data out too fast

        # Since we can't trust what we read from the display, we store the last
        # executed command in a property inside the object. This way strobe
        # can add the enable bit & resend it
        if isstrobe==0: #
            self.lastcomm=commvalue




    # put string function
    def lcd_puts(self, string, line):
        if line == 1:
            self.lcd_write(0x80)
        if line == 2:
            self.lcd_write(0xC0)
        if line == 3:
            self.lcd_write(0x94)
        if line == 4:
            self.lcd_write(0xD4)

        for char in string:
            self.lcd_putc(char)

    # clear lcd and set to home
    def lcd_clear(self):
        self.lcd_write(0x1)
        sleep(0.005) # This command takes awhile.
        self.lcd_write(0x2)
        sleep(0.005) # This command takes awhile.

    # add custom characters (0 - 7)
    def lcd_load_custon_chars(self, fontdata):
        self.lcd_device.bus.write(0x40);
        for char in fontdata:
            for line in char:
                self.lcd_write_char(line)


    # Necessary for Fuscus
    def copy_to_display(self, buffer):
        """Copy lines from buffer to display.
        Limit rows and columns to what is physically available."""
        # TODO - Change this from magic numbers to configurable options
        COLUMNS = 20
        ROWS = 4

        # Disabling the initial lcd_clear due to flickering
        # self.lcd_clear()
        r = 0
        for line in buffer:
            # self.gotoxy(0, r)
            self.lcd_puts(line[:COLUMNS], r+1)
            r += 1
            if r == ROWS:
                break

    # Necessary for Fuscus
    def backlight(self, percent):
        if percent > 0:
            self.backlight_status = 1 << 7
        else:
            self.backlight_status = 0

        # TODO - Implement
        pass

