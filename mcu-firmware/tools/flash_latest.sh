#!/bin/bash

# Manually flashes the latest built MCU firmware to the chip with probe-rs

output_folder=$(dirname "$0")/../Build/output
last_bin_file=$(find "$output_folder" -type f -name "*.bin" | sort | tail -n 1)

# Check if a .bin file was found
if [ -n "$last_bin_file" ]; then
    echo "Last .bin file found: $last_bin_file"
    probe-rs download $output_folder/revvy_firmware-0.2.1235-main.bin --format bin --chip atsamd51p19a --base-address 0x40000
else
    echo "No .bin files found in $output_folder. Not flashing."
fi