# README
This is the repository for TurboAnalysis 9001, a heart rate monitoring and HRV analysis device.
Firmware has been written in MicroPython, and can be found in the project-directory
of this repository.

## installation
If you wish to demo the firmware with a suitable device (I won't go into detail on 
what kind of device you'll need), you'll need to flash your Raspberry Pi Pico with a MicroPython firmware. Run the install.sh/install.cmd script in pico-test and add everything in project-directory in the device's root. **Edit the wlan_creds.txt to connect to your own wifi network.**

I shouldve copied the installation script to our project instead of modifying it inside pico-test directory locally, but can't be asked to reconfigure the package.json file again so work things out on your own.

### About the API-key
Every group member is free to publish this for display (For portfolio etc purposes), and we chose not to leak our teachers API key in the internet. If you have a Kubios API key and wish to use it, save it in api-key.txt and flash it in the devices root.

## Project Group Members
Nichakon Itthikun: nichakon.itthikun@metropolia.fi
Andrei Vlassenko: andrei.vlassenko@metropolia.fi
Matias Ruonala: matias.ruonala@metropolia.fi
