Bootloader development
======================

The bootloader comes in two flavours:

- debug
- release

The release bootloader does not allow installing a debug image currently. The installation process
stores the image's hash in the flash memory in a header page. We don't currently have the tools
to write this page using the programmer tools we use, so for firmware development, you'll need to
flash a debug bootloader first.

Building a debug bootloader
---------------------------

```bash
make all config=debug
```

The resulting binary is placed in `mcu-bootloader/Build/Debug/mcu-bootloader`

Building a release bootloader
-----------------------------

```bash
make all config=release
```

The resulting binary is placed in `mcu-bootloader/Build/Release/mcu-bootloader`

Flashing the bootloader
-----------------------

```bash
probe-rs download path/to/rrrc_samd51.elf --chip atsamd51p19a
probe-rs reset --chip atsamd51p19a

# or

probe-rs run path/to/rrrc_samd51.elf --chip atsamd51p19a
# ctrl-c to exit
```

Debugging
---------

VS Code comes with a launch configuration that can flash and connect to a debug bootloader
automatically. Follow the [Setup instructions](../setup.md) to set up your preferred debugger, then press F5.
