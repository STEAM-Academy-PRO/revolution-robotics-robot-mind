Firmware development
====================

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

Building a debug firmware
-------------------------

```bash
python -m tools.gen_version
python -m tools.generate_makefile
# currently the generated runtime is checked in, so this is not needed
# cglue --generate --cglue-output=rrrc/generated_runtime
make all config=debug

# if you want to include the firmware in a pi-firmware package
python -m tools.prepare --debug
```

The resulting binary is placed in `mcu-firmware/Build/Debug/mcu-firmware`.
The result of the `prepare` script is placed in `mcu-firmware/Build/output`.

Building a release bootloader
-----------------------------

```bash
python -m tools.gen_version
python -m tools.generate_makefile
# currently the generated runtime is checked in, so this is not needed
# cglue --generate --cglue-output=rrrc/generated_runtime
make all config=release

# if you want to include the firmware in a pi-firmware package
python -m tools.prepare
```

The resulting binary is placed in `mcu-firmware/Build/Release/mcu-firmware`.
The result of the `prepare` script is placed in `mcu-firmware/Build/output`.

Flashing the firmware
---------------------

```bash
probe-rs download path/to/rrrc_samd51.elf --chip atsamd51p19a
probe-rs reset --chip atsamd51p19a

# or

probe-rs run path/to/rrrc_samd51.elf --chip atsamd51p19a
# ctrl-c to exit
```

Debugging
---------

VS Code comes with a launch configuration that can flash and connect to a debug firmware
automatically. To start this, open the `mcu-firmware` folder in a new window and press F5.

Troubleshooting
---------------

- After flashing and restarting, if you see that the four status leds are magenta, reflash
the bootloader with a debug image.
