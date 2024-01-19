[![Build Status](https://travis-ci.org/RevolutionRobotics/RevvyFramework.svg?branch=master)](https://travis-ci.org/RevolutionRobotics/RevvyFramework)
[![codecov](https://codecov.io/gh/RevolutionRobotics/RevvyFramework/branch/master/graph/badge.svg)](https://codecov.io/gh/RevolutionRobotics/RevvyFramework)

Some sound effects (bell, duck, lion and engine revving sounds) in the assets directory were downloaded from http://www.freesfx.co.uk

[Documentation](../docs/pi/index.md)

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

# VSCode setup
- Enable auto imports in settings: `"python.analysis.autoImportCompletions": true`
- install recommended extensions!

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