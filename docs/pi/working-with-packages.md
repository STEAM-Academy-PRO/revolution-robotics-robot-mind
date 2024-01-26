Pi firmware packages
====================

Creating and installing an update package
-----------------------------------------

To package the framework for installation, do the following:

- If you want to include a mcu-firmware in the package:
 - [build one](../mcu-firmware/development.md#preparing-for-package) and run the `prepare` script for packaging
 - Copy the `revvy_firmware-<version>.bin` and `catalog.json` files from `mcu-firmware/Build/output` into `pi-firmware/data/firmware`
- Run `python -m dev_tools.create_package`
- The resulting files can be found in `install`:
  - `framework.data` and `framework.meta`
  - `framework-<version>.tar.gz` is the update package that can be uploaded using the mobile app.

How to install a package from `*.data` and `*.meta` files
---------------------------------------------------------

- Rename to `2.data` and `2.meta`
- Copy to `~/RevvyFramework/user/data/ble` on the robot
- Restart the revvy service [as described](start-stop.md)
- Please note that the installation process can take up to about 5 minutes
