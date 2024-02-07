MCU firmware
============

[Documentation root](../index.md)

The MCU firmware is the code that controls the low level brain functions.

The MCU is a Microchip ATSAMD51P19A.

This repository contains the application code running on the ATSAMD51P19A microcontroller on the Revolution Robotics Challenge Kit's control board.

- [Setting up the development environment](setup.md)
- [Software architecture](architecture.md)
- [Development guide](development.md)
- [Working with error logs](error-logs.md)
- [Clock tree configuration](clock-tree.md)

Project folders
---------------

- `.vscode`: IDE configuration. When setting up your environment, make sure to create a copy of the example configuration and tailor them to your system.
- `Build`: compiler output.
- `Config`: various SDK, OS and project configuration options.
  - `Config/atmel_start_pins.h` contains the various board signal assignments.
  - `Config/fw_version.h` is a generated file that contains the current version. Do not modify by hand.
- `rrrc`: the main part of the firmware source code
- `third_party`: external libraries that are not shared with the bootloader (FreeRTOS)
- `tools`: python scripts to simplify working with the source code. Call them as `python -m tools.<script name>`
  - `tools.gen_version`: generates `Config/fw_version.h`
  - `tools.gen_component_diagram`: generates an overview of the component structure. Requires graphviz to be installed.
  - `tools.generate_makefile`: generates `Makefile`
  - `tools.prepare`: call after compilation. The script creates metadata for a firmware binary and places it into `Build/output`
  - `requirements.txt`: python packages to be installed with `pip install -r`
- `project.json`: component connections and other system configuration
