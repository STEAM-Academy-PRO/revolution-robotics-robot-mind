Documentation
=============

Robot architecture
------------------

Brain hardware consists of a Carrier PCBA and a Raspberry Pi Zero. The Carrier PCBA consists of
an ATSAMD51P19A MCU which runs the `mcu-bootloader` and `mcu-firmware` projects, handles low-level
control tasks, and implements sensor and motor port drivers. The Raspberry Pi Zero runs the
`pi-firmware` project which interfaces to the MCU via [i2c](mcu-firmware/i2c.md). The Raspberry Pi
Zero communicates with the User's application, receives a robot configuration, sets up the
required drivers on the MCU and in the `pi-firmware`. The `pi-firmware` reads status data from the
MCU, provides an interface for a manual remote controller, and runs user programs for semi- or fully
autonomous control.

 - [Glossary](glossary.md)
 - [CI](ci.md)
 - [MCU bootloader](mcu-bootloader/index.md)
 - [MCU software](mcu-firmware/index.md)
 - [Pi firmware](pi/index.md)
 - [How to release a new version](release.md)
 - [How to set up a new self-hosted runner](self-hosted-setup.md)
 - [How to flash an OS image](image-flashing.md)

It is recommended to read this documentation on [GitHub](https://github.com/STEAM-Academy-PRO/revolution-robotics-robot-mind/tree/main/docs/index.md)
