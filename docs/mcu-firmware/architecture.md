Software architecture
=====================

The MCU firmware runs on the Carrier PCBA, on an ATSAMD51P19A microcontroller. The PCBA contains
ports for external sensors and motors, as well as a 6-degree of freedom [Inertial Measurement Unit](gyro.md)
to keep track of the Brain's orientation in 3D space. The firmware running on the MCU controls
the IMU, and can be set up in runtime to interface with the configurable motor and sensor ports.
The MCU is connected to a higher level host via [I2C](i2c.md), and implements a number of commands
which can be used to configure and control the robot. Firmware components may expose can expose data
using a notification mechanism called status slots **TODO write docs**.

The firmware is broken up into smaller software components. The software component architecture is
managed by CGlue, an in-house developed firmware architecture and toolkit. CGlue
generates component boilerplate code using component descriptor `json` files, checks component
compatibility, and ties the whole firmware together using a `project.json` that specifies how each
software component is connected together. From this information, CGlue is capable of generating
a software runtime that actually implements the connections between the components (sometimes
referred to as the software bus).

> Because CGlue is missing some features, some of the software components contain manual modifications to the generated component structure or runtime layer.
> An example for this is the communication layer: currently, it is not possible to describe, which command IDs belong to which command handler functions, so these connections are done in a manually written source file.

> This needs to be expanded. CGlue is complicated. It has it's own [documentation](https://github.com/STEAM-Academy-PRO/revolution-robotics-CGlue?tab=readme-ov-file#cglue--).

Developing with CGlue
---------------------

* Create a new software component: `cglue --new-component ComponentName`
* Update generated component code based on modification of the component model: `cglue --update-component ComponentName [--cleanup]`
* Generate runtime based on the project.json configuration: `cglue --generate --cglue-output=rrrc/generated_runtime [--cleanup]`
  The generated files are: `rrrc/generated_runtime.h` and `rrrc/generated_runtime.c`
* Generate makefile for compilation: `python -m tools.generate_makefile [--cleanup]`

General concepts
----------------

### Ports, port drivers

Due to hardware design details, ports are grouped by functionality into **motor ports** and **sensor ports**.
The C implementation has three distinct parts:
- A `CommWrapper` component, which is responsible for processing commands from the python firmware
- A `PortHandler` component, which implements the actual port drivers, reacts to commands coming
  from the associated `CommWrapper` and exposes status information via a status slot
- The `McuStatusSlots` component which takes the exposed status information and makes it available
  for the python firmware to read back. This status information is read by the python firmware
  periodically. Once read, the associated status slot is cleared to avoid wasting bandwidth.