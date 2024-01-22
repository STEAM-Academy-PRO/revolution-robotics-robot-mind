Firmware development
====================

Developing with CGlue
--------------------

* Create a new software component: `cglue --new-component ComponentName`
* Update generated component code based on modification of the component model: `cglue --update-component ComponentName [--cleanup]`
* Generate runtime based on the project.json configuration: `cglue --generate --cglue-output=rrrc/generated_runtime [--cleanup]`
  The generated files are: `rrrc/generated_runtime.h` and `rrrc/generated_runtime.c`
* Generate makefile for compilation: `python -m tools.generate_makefile [--cleanup]`

When using the provided VS Code tasks, runtime and makefile generation is done automatically during the build process.

Install the firmware on a working robot
---------------------------------------

- In VS Code, select `Terminal > Run Task... > prepare release binary`
- If successful, you should see the name, version, size and checksum of the resulting binary.
  You will find the binary in `Build/output`. Example:

  ```
  Changes made to catalog file:
    Deleted old firmware: revvy_firmware-0.2.1142.bin
    Added: revvy_firmware-0.2.1151-develop.bin - HW: 2.0.0, FW: 0.2.1151-develop, size: 70228, md5: dfc5298fb025e7edafb4bf6374962552
  ```

- Connect to the robot. Consult the framework documentation for more information on this.
- Copy the resulting binary and catalog.json to the `~/RevvyFramework/user/packages/<newest>/data/firmware/` folder
    > In case there are no folders in `~/RevvyFramework/user/packages/`, you need to copy an installation from `~/RevvyFramework/default/packages/`.
    > To do this, run the `cp -R ~/RevvyFramework/default/packages/ ~/RevvyFramework/user/packages/` command.
- Delete the corresponding lines from the `manifest.json` file in the `~/RevvyFramework/user/packages/<newest>/` folder
- Restart the framework to install the firmware

Debugging
---------

- Make sure the **debug** bootloader is installed on the MCU. You can find the compiled bootloaders
  in the ProductionFiles repository, or the sources in the `mcu-bootloader` folder.
- Select the Run icon in the left toolbar
- Select the `Debug (J-Link)` configuration
- Press `F5` to start
- If prompted, accept the licence agreement

Programming the robot directly
------------------------------

- upload MCU bootloader with `probe-rs download path/to/rrrc_bootloader.bin --chip atsamd51p19a --format bin`
- upload MCU firmware with `probe-rs download path/to/revvy_firmware.bin --format bin --chip atsamd51p19a --base-address 0x40000`
