# fuscus setup - A Fuscus installer

## Overview
This implements a brief installation script streamlining the installation of Fuscus - a Python implementation of a temperature controller for BrewPi. This attempts to implement most of the procedure documented in [notes.md](../../master/docs/notes.md)., with the exceptions noted below.

**Implemented:**
* Download the latest version of the code from the repo on GitHub
* Add the 'fuscus' user
* Add 'fuscus' to sudoers
* Set up the appropriate visudo line

**Not part of script - bust be done manually:**
* Setup of Raspberry Pi, installation of BrewPi, etc.
* Configure Fuscus (Update/create fuscus.ini)
* Launch Fuscus
* Set up a crontab entry to launch Fuscus




## Usage
The full Fuscus installation notes are located at [notes.md](../docs/notes.md) and are a highly recommended read.

Once you've read through them, follow the instructions in [usage.md](usage.md)


