#!/usr/bin/python3

import argparse
import json
import os
import shutil

from tools.generate_makefile import generate_makefile


# logging helpers


def colored(text: str, color: str) -> str:
    return f"\033[{color}m{text}\033[0m"


def green(text: str) -> str:
    return colored(text, "32")


def red(text: str) -> str:
    return colored(text, "31")


def blue(text: str) -> str:
    return colored(text, "34")


# utils


def shell(command: str) -> None:
    print(f"{green('Running')} {command}")
    exit_code = os.system(command)
    if exit_code != 0:
        print(f"{red('Error')} {blue(command)} failed with exit code {exit_code}")
        exit(exit_code)


def load_project_settings(in_ci: bool) -> dict:
    if in_ci:
        return json.load(open(".vscode/settings.ci.json"))
    else:
        if not os.path.exists(".vscode/settings.json"):
            print("Looks like first run, copied vscode settings.example to settings!")
            shutil.copy(".vscode/settings.example.json", ".vscode/settings.json")

        return json.load(open(".vscode/settings.json"))


# Command implementations


def generate_files(in_ci: bool) -> bool:
    print(f"{green('Updating')} Version file")
    shell("python -m tools.gen_version")

    print(f"{green('Generating')} Makefile")
    makefile_changed = generate_makefile(in_ci=in_ci, clean_up=True)

    print(f"{green('Generating')} CGlue runtime")
    shell("cglue --generate")

    return makefile_changed


def build(config: str, in_ci: bool, rebuild: bool) -> None:
    makefile_changed = generate_files(in_ci)

    if rebuild or makefile_changed:
        shell("make clean")

    print(f"{green('Building')} Firmware")
    settings = load_project_settings(in_ci)
    ci = "ci=1" if in_ci else ""
    shell(f"make all config={config} {ci} -j{settings.get('maxParallelBuilds', 4)}")

    # tools.prepare moves the built firmware into the output folder and generates metadata
    if config == "debug":
        shell("python -m tools.prepare --debug")
    else:
        shell("python -m tools.prepare")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="./x", description="MCU firmware build tool")
    parser.add_argument(
        "action",
        help="Action to execute",
        choices=[
            # list commands here
            "build",
            "generate",
            "erase",
            "run",
            "attach",
        ],
    )
    parser.add_argument("--release", help="Build in release mode", action="store_true")
    parser.add_argument("--rebuild", help="Clean before building", action="store_true")
    parser.add_argument("--ci", help="Build runs in CI", action="store_true")
    args = parser.parse_args()

    config = "release" if args.release else "debug"

    # handle commands here
    if args.action == "build":
        build(config, in_ci=args.ci, rebuild=args.rebuild)

    elif args.action == "generate":
        generate_files(in_ci=args.ci)

    elif args.action == "erase":
        shell(f"probe-rs erase --chip atsamd51p19a")

    elif args.action == "run":
        build(config, in_ci=args.ci, rebuild=args.rebuild)
        dir = "Release" if args.release else "Debug"
        shell(
            f"probe-rs run --chip atsamd51p19a --speed 15000 Build/{dir}/mcu-firmware/rrrc_samd51.elf"
        )

    elif args.action == "attach":
        dir = "Release" if args.release else "Debug"
        shell(
            f"probe-rs attach --chip atsamd51p19a --speed 15000 Build/{dir}/mcu-firmware/rrrc_samd51.elf"
        )
