##So you want to add support for new LCD hardware?

All LCD hardware modules MUST support two methods implemented as follows:
    `def copy_to_display(self, buffer):`
    `def backlight(self, percent):`

`copy_to_display` must accept `buffer` which is a multi-dimensional array containing the contents of the LCD screen, and must print the full buffer to the screen.

`backlight` must accept `percent` which is an integer (0-100) containing the backlight percentage. Anything greater than 0 should, at a minumum, enable the backlight, while zero should ideally disable the backlight.

Once this method is implemented, update *fuscus.sample.ini* to add an example configuration for the LCD screen type, and update *constants.py* to load the configuration & initialize the appropriate module

With this method implemented, update *constants.py* to add support for the configuration
(and update fuscus.sample.ini to add an example configuration file)
