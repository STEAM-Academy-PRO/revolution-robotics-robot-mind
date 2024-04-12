#!/usr/bin/python3

import argparse
import os
import shutil
from contextlib import contextmanager


@contextmanager
def in_folder(folder: str):
    cwd = os.getcwd()
    os.chdir(folder)
    try:
        yield
    finally:
        os.chdir(cwd)


def build_firmware(config: str) -> None:
    with in_folder("../mcu-firmware"):
        # TOOD: this should probably call a similar x-like script in the firmware folder
        os.system("python -m tools.gen_version")
        os.system("python -m tools.generate_makefile --cleanup")
        os.system("cglue --generate")
        os.system(f"make all config={config} -j12")  # TODO: configurable job count

        # tools.prepare moves the built firmware into the output folder and generates metadata
        if config == "debug":
            os.system("python -m tools.prepare --debug")
        else:
            os.system("python -m tools.prepare")


def copy_firmware_into_place() -> None:
    with in_folder("data/firmware"):
        # remove old files
        for root, dirs, files in os.walk("."):
            for file in files:
                if file != ".nodelete":
                    os.unlink(file)

        # copy new files
        shutil.copytree("../../../mcu-firmware/Build/output", ".", dirs_exist_ok=True)


def create_package() -> None:
    os.system("python -m dev_tools.create_package")


def build(config: str):
    build_firmware(config)
    copy_firmware_into_place()
    create_package()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", help="Action to execute", choices=["build"])
    parser.add_argument("--release", help="Build in release mode", action="store_true")
    args = parser.parse_args()

    config = "release" if args.release else "debug"

    if args.action == "build":
        build(config)
