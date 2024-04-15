#!/usr/bin/python3

import argparse
import json
import os
import shutil


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


def load_project_settings() -> str:
    if not os.path.exists(".vscode/settings.json"):
        print("Looks like first run, copied vscode settings.example to settings!")
        shutil.copy(".vscode/settings.example.json", ".vscode/settings.json")

    return json.load(open(".vscode/settings.json"))


# Command implementations


def generate_files() -> None:
    print(f"{green('Updating')} Version file")
    shell("python -m tools.gen_version")

    print(f"{green('Generating')} Makefile")
    shell("python -m tools.generate_makefile --cleanup")

    print(f"{green('Generating')} CGlue runtime")
    shell("cglue --generate")


def build(config: str) -> None:
    generate_files()

    print(f"{green('Building')} Firmware")
    settings = load_project_settings()
    shell(f"make all config={config} -j{settings.get('maxParallelBuilds', 4)}")

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
        ],
    )
    parser.add_argument("--release", help="Build in release mode", action="store_true")
    args = parser.parse_args()

    config = "release" if args.release else "debug"

    # handle commands here
    if args.action == "build":
        build(config)

    elif args.action == "generate":
        generate_files()
