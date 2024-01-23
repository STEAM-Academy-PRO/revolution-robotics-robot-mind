Pi firmware packages
====================

Creating and installing an update package
-----------------------------------------

To package the framework for installation, do the following:

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
