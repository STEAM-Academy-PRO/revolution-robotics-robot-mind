#!/usr/bin/python3
import os
import shutil
import json
import argparse
from hashlib import md5


def file_hash(file):
    hash_fn = md5()
    with open(file, "rb") as f:
        hash_fn.update(f.read())
    return hash_fn.hexdigest()


# parameters
version_major = 0
version_minor = 2
hardware_versions = ["2.0.0"]
firmware_filename = "rrrc_samd51.bin"

if __name__ == "__main__":
    # prepare
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='Build/output', help='Directory where the output shall be placed')
    parser.add_argument('--debug', help='Use the debug binary instead of release', action='store_true')

    args = parser.parse_args()

    if args.debug:
        build_dir = 'Build/Debug/mcu-firmware'
    else:
        build_dir = 'Build/Release/mcu-firmware'

    firmware_file = f"{build_dir}/{firmware_filename}"

    with open('Config/fw_version.h') as fw_version:
        contents = fw_version.readlines()
        version_patch = contents[3].replace('#define FW_VERSION ', '').replace('"', '').strip()

    os.makedirs(args.out, exist_ok=True)

    version_str = f"{version_major}.{version_minor}.{version_patch}"
    catalog_file = os.path.join(args.out, "catalog.json")

    # noinspection PyBroadException
    try:
        with open(catalog_file, "r") as cf:
            catalog = json.load(cf)
    except Exception:
        catalog = {}

    # copy firmware file
    filename = f"revvy_firmware-{version_str}.bin"
    destination_file = os.path.join(args.out, filename)
    shutil.copy(firmware_file, destination_file)

    print("Changes made to catalog file:")
    for hwv in hardware_versions:
        try:
            # delete old file
            old = catalog[hwv]
            if old['filename'] != filename:
                os.unlink(os.path.join(args.out, old['filename']))
                print('\tDeleted old firmware: ' + old['filename'])
        except KeyError:
            pass
        except FileNotFoundError:
            pass

        # update catalog file
        size = os.stat(destination_file).st_size
        checksum = file_hash(destination_file)
        catalog[hwv] = {
            "version":  version_str,
            "filename": filename,
            "length":   size,
            "md5":      checksum
        }

        print(f"\tAdded: {filename} - HW: {hwv}, FW: {version_str}, size: {size}, md5: {checksum}")

    with open(catalog_file, "w") as cf:
        json.dump(catalog, cf, indent=4)
