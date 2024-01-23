# Mind of the Robot

[Documentation](docs/index.md)

## mcu-common

Common hardware abstraction˛code used by mcu-bootloader and mcu-firmware

## mcu-bootloader

Starts the mcu-firmware and provides an update interface to the carrier board.

## mcu-firmware

Code that runs on the carrier board, moves the motors, reads the sensors. Provides the interface for the pi-firmware.

## pi-firmware

Manages bluetooth interface and different app states, runs programs, controls high level robot behavior.

