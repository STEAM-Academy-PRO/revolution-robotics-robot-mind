[![Build Status](https://travis-ci.org/RevolutionRobotics/RevvyFramework.svg?branch=master)](https://travis-ci.org/RevolutionRobotics/RevvyFramework)
[![codecov](https://codecov.io/gh/RevolutionRobotics/RevvyFramework/branch/master/graph/badge.svg)](https://codecov.io/gh/RevolutionRobotics/RevvyFramework)

Some sound effects (bell, duck, lion and engine revving sounds) in the assets directory were downloaded from http://www.freesfx.co.uk

# How to connect to the robot using SSH

## Windows
 - Make sure the robot is turned on
 - Connect the robot to your computer via a USB cable.
 - Open Device Manager and make sure it shows up under Network Interfaces as `USB Ethernet/RNDIS Gadget`
    - If not, unplug the robot and observe that the device list flashes once.
    - If the device list does not flash, your computer does not see the robot. Replace the USB cable with a new one and try again.
    - If the device list flashes, but you don't see the `USB Ethernet/RNDIS Gadget`, you'll need to install drivers from <TODO>. This should not be necessary on recent Windows versions.

 - Download and install putty
 - In the host field, enter `pi@raspberrypi.local`. Make sure port is 22 and that SSH is selected.
 - Save the connection for later use. Enter a name under Saved Sessions and press Save.
 - Press Open to connect.
 - If asked, accept the fingerprint.
 - Enter 123 when prompted for password.
 - To access the filesystem, use WinSCP or the SecureFTP TotalCommander plugin.

# How to start/stop/restart the framework service.
After startup, the framework service is already running. If you want to modify it, or run a tool script or other scripts that work with the framework, you'll need to stop the service before starting your script, or restart it after a modification.

To control the framework service, use these commands:
 - Stop: `sudo systemctl stop revvy`
 - Start: `sudo systemctl start revvy`
 - Restart: `sudo systemctl restart revvy`

If you want to start the framework, but not the service (for example, you want to observe console output), enter the framework directory by running `cd RevvyFramework` and start by executing `python3 launch_revvy.py`. To exit, press Enter.

# About the integrity protection and modifications
After startup the framework scans for unintended modifications in the source code. This is done by comparing the checksum of the individual files to those contained in the `manifest.json` file. If a file is not listed in the manifest, it is ignored. If a checksum does not match, the framework exits and if possible, an older one is then started.

Because of this, if you intend to modify a file, you need to either update the manifest with the new MD5 checksum, or remove the modified file from the manifest.

Only the packages located under `~/RevvyFramework/user/packages` can be modified, other parts of the filesystem are read-only.

# Preparing the environment for framework development
 - Check out the sources in a directory of your choice.
 - Create a python virtual environment in the source directory by running `python -m venv venv`
 - Active the virtual environment by running `.\venv\Scripts\activate`
 - Install the required packages by running `pip install -r install/requirements.txt` and `pip install -r install/requirements_test.txt`
 - Run `nose2 -B` to see if the included tests pass.

# Creating and installing an update package
To package the framework for installation, do the following:
 - Activate the virutal environment
 - Run `python -m dev_tools.create_package`
 - The resulting files can be found in `install`
 - Copy the `framework.meta` and `framework.data` files into the `~/RevvyFramework/user/data/ble` folder on the robot as `2.meta` and `2.data`.
 - To install the new package, restart the framework service, or stop it and start the framework manually as described above.
 - Please note that the installation process can take up to about 5 minutes.
