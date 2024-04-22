#!/usr/bin/python3
import os
import shutil
import argparse
from hashlib import md5


def file_hash(file):
    hash_fn = md5()
    with open(file, "rb") as f:
        hash_fn.update(f.read())
    return hash_fn.hexdigest()


# parameters
firmware_filename = "rrrc_samd51.bin"

if __name__ == "__main__":
    # prepare
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default="Build/output",
        help="Directory where the output shall be placed",
    )
    parser.add_argument(
        "--debug", help="Use the debug binary instead of release", action="store_true"
    )

    args = parser.parse_args()

    if args.debug:
        build_dir = "Build/Debug/mcu-bootloader"
    else:
        build_dir = "Build/Release/mcu-bootloader"

    firmware_file = f"{build_dir}/{firmware_filename}"

    os.makedirs(args.out, exist_ok=True)

    # copy firmware file
    filename = f"revvy_bootloader.bin"
    destination_file = os.path.join(args.out, filename)
    shutil.copy(firmware_file, destination_file)

    print(f"Generated {destination_file}")
