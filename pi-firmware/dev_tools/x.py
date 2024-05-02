#!/usr/bin/python3

import argparse
import os
import shutil
import json
from typing import Optional
from contextlib import contextmanager

from paramiko import AutoAddPolicy, SSHClient

# logging helpers


def colored(text: str, color: str) -> str:
    return f"\033[{color}m{text}\033[0m"


def green(text: str) -> str:
    return colored(text, "32")


def red(text: str) -> str:
    return colored(text, "31")


def blue(text: str) -> str:
    return colored(text, "34")


# utilities


@contextmanager
def in_folder(folder: str):
    cwd = os.getcwd()
    os.chdir(folder)
    try:
        yield
    finally:
        os.chdir(cwd)


def shell(command: str) -> None:
    print(f"{green('Running')} {command}")
    exit_code = os.system(command)
    if exit_code != 0:
        print(f"{red('Error')} {blue(command)} failed with exit code {exit_code}")
        exit(exit_code)


cached_host: Optional[str] = None
ssh_connection: Optional[SSHClient] = None


def load_host_from_json() -> str:
    if not os.path.exists(".vscode/settings.json"):
        print("Looks like first run, copied vscode settings.example to settings!")
        shutil.copy(".vscode/settings.example.json", ".vscode/settings.json")

    return json.load(open(".vscode/settings.json"))["target"]


def robot_host() -> str:
    global cached_host

    if cached_host is None:
        set_robot_host(load_host_from_json())

    assert cached_host is not None
    return cached_host


def set_robot_host(host: str):
    global cached_host
    cached_host = host


def ensure_connected() -> SSHClient:
    global ssh_connection

    if ssh_connection is None:
        host = robot_host()
        ssh_connection = SSHClient()
        ssh_connection.set_missing_host_key_policy(AutoAddPolicy())
        ssh_connection.connect(host, username="pi", password="123")

    assert ssh_connection is not None
    return ssh_connection


def upload_file(src: str, dst: str):
    client = ensure_connected()
    print(f"{green('Uploading')} {src} to {dst}")
    sftp = client.open_sftp()
    sftp.put(src, dst)
    sftp.close()


def ssh(command: str) -> int:
    """Executes a command on the robot and prints the output as it comes in. Returns the exit code."""

    client = ensure_connected()
    print(f"{green('Executing')} {command}")
    stdin, stdout, stderr = client.exec_command(command)

    stdout.channel.set_combine_stderr(True)

    # Unfortunately, due to maybe https://github.com/paramiko/paramiko/issues/1801, this does not
    # work well on Windows and all the output if dumped after the command is finished.
    while not stdout.channel.exit_status_ready():
        print(stdout.channel.recv(32).decode(), end="")

    return stdout.channel.recv_exit_status()


# Command implementations


def build_firmware(config: str) -> None:
    with in_folder("../mcu-firmware"):
        if config == "debug":
            shell("python -m tools.x build")
        else:
            shell("python -m tools.x build --release")


def copy_firmware_into_place() -> None:
    with in_folder("data/firmware"):
        # remove old files
        for root, dirs, files in os.walk("."):
            for file in files:
                if file != ".nodelete":
                    os.unlink(file)

        # copy new files
        shutil.copytree("../../../mcu-firmware/Build/output", ".", dirs_exist_ok=True)


def create_py_package(dev_package: bool):
    if dev_package:
        shell("python -m dev_tools.create_package --dev")
    else:
        shell("python -m dev_tools.create_package")


def unlock_pi() -> None:
    ssh("sudo mount -o rw,remount /")


def upload_debug_launcher() -> None:
    unlock_pi()
    ssh("sudo chmod +777 /home/pi/RevvyFramework")
    ssh("sudo chmod +777 /home/pi/RevvyFramework/launch_revvy.py")
    upload_file("install/debug_launch_revvy.py", "/home/pi/RevvyFramework/launch_revvy.py")


def upload_package_to_robot(dev_package: bool) -> None:
    # 2.data/meta triggers an install into a per-version target folder and it does NOT overwrite
    # a package of the same version.
    # pi-firmware.data/meta triggers an install into the dev target folder and it DOES overwrite
    dst_name = "pi-firmware" if dev_package else "2"

    upload_file("install/pi-firmware.data", f"/home/pi/RevvyFramework/user/ble/{dst_name}.data")
    upload_file("install/pi-firmware.meta", f"/home/pi/RevvyFramework/user/ble/{dst_name}.meta")


def build(config: str, dev_package: bool = False):
    build_firmware(config)
    copy_firmware_into_place()
    create_py_package(dev_package)


def stop_service():
    # only one of these will actually do something
    ssh("sudo systemctl stop revvy")
    ssh("sudo systemctl stop revvy-early")


def start_service():
    # only one of these will actually do something
    ssh("sudo systemctl start revvy-early")
    ssh("sudo systemctl start revvy")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="./x", description="Revvy build and deploy tool")
    parser.add_argument(
        "action",
        help="Action to execute",
        choices=[
            # list commands here
            "build",
            "deploy",
            "full-deploy",  # Slow. Installs to versioned folder and installs dependencies.
            "test",
            "hil-test",
            "run",
            "reboot",
        ],
    )
    parser.add_argument("--release", help="Build in release mode", action="store_true")
    parser.add_argument("--no-start", help="Do not start the deployed package", action="store_true")
    args = parser.parse_args()

    config = "release" if args.release else "debug"

    # handle commands here
    if args.action == "build":
        build(config)

    elif args.action == "deploy":
        build(config)
        upload_debug_launcher()
        upload_package_to_robot(dev_package=True)
        stop_service()
        ssh("~/RevvyFramework/launch_revvy.py --install-only --skip-dependencies")
        if not args.no_start:
            start_service()

    elif args.action == "run":
        build(config)
        upload_debug_launcher()
        upload_package_to_robot(dev_package=True)
        stop_service()
        ssh("~/RevvyFramework/launch_revvy.py --skip-dependencies")

    elif args.action == "full-deploy":
        build(config)
        upload_package_to_robot(dev_package=False)
        stop_service()
        ssh("~/RevvyFramework/launch_revvy.py --install-only")
        if not args.no_start:
            start_service()

    elif args.action == "hil-test":
        build(config, dev_package=True)
        upload_debug_launcher()
        upload_package_to_robot(dev_package=True)
        stop_service()
        ssh("~/RevvyFramework/launch_revvy.py --install-only --skip-dependencies")
        ssh(
            "cd ~/RevvyFramework/user/packages/dev-pi-firmware/ && python3 -u -m tests.hil_tests.tests"
        )

    elif args.action == "test":
        print(green("Running unit tests"))
        shell("cd tests && nose2 -B")
        print(green("Running doctests"))
        shell("cd revvy && nose2 -B")

    elif args.action == "reboot":
        ssh("sudo reboot")
