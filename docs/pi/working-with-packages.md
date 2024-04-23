Pi firmware packages
====================

Creating and installing an update package
-----------------------------------------

To package the framework for installation, do the following:

- Run `./x build [--release]`. This will build the C firmware and creates a python package with it.

How to build and install a package to your robot
------------------------------------------------

- Run `./x deploy [--release]`. This will build, upload and install everything.
