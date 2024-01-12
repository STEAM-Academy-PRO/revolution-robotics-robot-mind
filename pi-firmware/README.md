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
    - If the device list flashes, but you don't see the `USB Ethernet/RNDIS Gadget`, you'll need to install drivers from https://www.catalog.update.microsoft.com/Search.aspx?q=USB%20RNDIS%20Gadget. Make sure to select `	Acer Incorporated. - Other hardware - USB Ethernet/RNDIS Gadget	Windows 7,Windows 8,Windows 8.1 and later drivers`.

 - Download and install putty
 - In the host field, enter `pi@raspberrypi.local`. Make sure port is 22 and that SSH is selected.
 - Save the connection for later use. Enter a name under Saved Sessions and press Save.
 - Press Open to connect.
 - If asked, accept the fingerprint.
 - Enter `123` when prompted for password.
 - To access the filesystem, use WinSCP or the SecureFTP TotalCommander plugin.

## Linux
### Cable
- figure out the IP address (TODO: fix auto dhcp IP address or document enable Bonjour service for linux)
- `ssh pi@some.ip`
### Wifi
- remove SD card from brain, insert to laptop
- edit `wpa_supplicant.conf` on the boot partition with the following content with your wifi router data:
```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=GB

network={
     ssid="your_network_name"
     psk="your_wifi_password"
     key_mgmt=WPA-PSK
}
```
- place back SD card to brain, start the brain
- find the Pi on the network:
- `arp | grep -v incomplete` or `nmap -sn $(ip route | awk '/default/ {print $3}')/24 -p 22`
- `ssh pi@found-ip` use `123` as password
- mount the file system to your local drive!
- ease your way in with `ssh-copy-id pi@found-ip` so you do not need a password.


# How to start/stop/restart the framework service.
After startup, the framework service is already running. If you want to modify it, or run a tool script or other scripts that work with the framework, you'll need to stop the service before starting your script, or restart it after a modification.

To control the framework service, use these commands:
 - Stop: `sudo systemctl stop revvy` or `stop`
 - Start: `sudo systemctl start revvy` or `start`
 - Restart: `sudo systemctl restart revvy`
 - Debug: `debug`

If you want to start the framework, but not the service (for example, you want to observe console output), enter the framework directory by running `cd RevvyFramework` and start by executing `python3 launch_revvy.py`. To exit, press Enter. (`debug`)

# About the integrity protection and modifications
After startup the framework scans for unintended modifications in the source code. This is done by comparing the checksum of the individual files to those contained in the `manifest.json` file. If a file is not listed in the manifest, it is ignored. If a checksum does not match, the framework exits and if possible, an older one is then started.

Because of this, if you intend to modify a file, you need to either update the manifest with the new MD5 checksum, or remove the modified file from the manifest.

Only the packages located under `~/RevvyFramework/user/packages` can be modified, other parts of the filesystem are read-only.

# Preparing the environment for framework development
 - Check out the sources in a directory of your choice.
 - Create a python virtual environment in the source directory by running `python -m venv venv`
 - Active the virtual environment by running
   - Windows: `.\venv\Scripts\activate`
   - Linux: `source ./venv/bin/activate`
 - To run unit tests:
   - Install the required packages by running `pip install -r install/requirements_test.txt`
   - Run `nose2 -B` to see if the included tests pass.

# Creating and installing an update package
To package the framework for installation, do the following:
 - Activate the virutal environment
 - Run `python -m dev_tools.create_package`
 - The resulting files can be found in `install`
 - Copy the `framework.meta` and `framework.data` files into the `~/RevvyFramework/user/data/ble` folder on the robot as `2.meta` and `2.data`.
 - `framework-<version>.tar.gz` is the update package that can be uploaded using the mobile app.
 - To install the new package, restart the framework service, or stop it and start the framework manually as described above.
 - Please note that the installation process can take up to about 5 minutes.

# Recommended Dev Env

Use VSCode, open this folder.
Create a `target` file and add the IP address of the brain. (bonjour: `raspberrypi.local` or e.g. `192.168.0.123` for wifi)

# Debugging
- from this dir, run `./debug`
- for attaching debugger, run `./debug 1`
- When says: Waiting for debugger, run 
- configure your `launch.json` to the proper IP

```json
{
  "name": "Attach PI Debugger",
  "type": "python",
  "request": "attach",
  "connect": {
    "host": "192.168.0.X",
    "port": 5678
  }
}
```