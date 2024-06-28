#!/bin/python3
# type: ignore

# A modified version of `launch_revvy.py` from pi-os, used for development.
# This script adds the `--skip-dependencies` option.

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import hashlib
import time
import traceback
from json import JSONDecodeError
from version import Version


DEFAULT_PACKAGE_DIR = "default/packages"
INSTALLED_PACKAGES_DIR = "user/packages"
TEST_PACKAGE_DIR = "user/test_packages"
DATA_DIRECTORY = "user/ble"

DEV_PACKAGE_NAME = "pi-firmware"
INSTALLED_DEV_PACKAGE_NAME = "dev-pi-firmware"


def read_version(file):
    """Reads version from json formatted manifest file.

    Args:
        file: Path to a json formatted manifest file.

    Returns:
        A Version object containing the version json field of the provided file
        or None on error.
    """
    try:
        with open(file, "r") as mf:
            manifest = json.load(mf)
        return Version(manifest["version"])
    except FileNotFoundError:
        print(f"File not found: {file}")
    except JSONDecodeError:
        print(f"Invalid json file: {file}")
    except KeyError:
        print(f"Json file is valid but there is no version in it: {file}")

    return None


def file_hash(file):
    """Calculates the md5 hash for the file provided.

    Args:
        file: Path to the file.

    Returns:
        The md5 hash string of the file or None on error.
        E.g.: 'd41d8cd98f00b204e9800998ecf8427e'

    Raises:
        IOError: An error occurred during opening/reading the file.
    """
    try:
        hash_fn = hashlib.md5()
        with open(file, "rb") as f:
            hash_fn.update(f.read())
        return hash_fn.hexdigest()
    except IOError:
        print(f"Could not calculate hash for {file}")
        print(traceback.format_exc())
        return None


def subprocess_cmd(command):
    """Executes shell commands

    Args:
        command: Newline separated commands to be executed in the shell

    Returns:
        Return code of execution
    """
    # if we have a list, concatenate lines
    if isinstance(command, list):
        command = "\n".join(command)

    try:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, shell=True, universal_newlines=True
        )
        for line in iter(process.stdout.readline, b""):
            sys.stdout.write(line)
            if process.poll() is not None:
                break
        return process.returncode
    except BrokenPipeError:
        return 0


def cleanup_invalid_installations(directory):
    """Removes incomplete versions of fw installations.

    The presence of the 'installed' file proves that the installation
    completed successfully. For any fw directory without this sentinel,
    we remove the directory.

    Args:
        directory: Base directory, containing installations.
    """
    print("Cleaning up interrupted installations")
    try:
        for fw_dir in os.listdir(directory):
            fw_dir = os.path.join(directory, fw_dir)
            if os.path.isdir(fw_dir):
                marker_file = os.path.join(fw_dir, "installed")
                if not os.path.isfile(marker_file):
                    print(red(f"Removing {fw_dir}: missing 'installed' marker file"))
                    shutil.rmtree(fw_dir)
    except FileNotFoundError:
        print("No user packages exist")


def has_update_package(directory, filename):
    """Checks if a valid fw update package is available.

    The '2.meta' json file contains length and md5 information about the update
    package named '2.data'. The code checks if these values are matching.

    Args:
        directory: (String) Directory path containing update package.

    Returns:
        True if update package is present and valid.
    """
    print(f"Looking for '{filename}.data' update files in {directory}")
    framework_update_file = os.path.join(directory, f"{filename}.data")
    framework_update_meta_file = os.path.join(directory, f"{filename}.meta")
    update_file_valid = False

    if os.path.isfile(framework_update_file) and os.path.isfile(framework_update_meta_file):
        print(f"Found update file {framework_update_file}, validating...")
        try:
            with open(framework_update_meta_file, "r") as fup_mf:
                metadata = json.load(fup_mf)
                if metadata["length"] == os.stat(framework_update_file).st_size:
                    if (
                        metadata["md5"] is not None
                        and file_hash(framework_update_file) == metadata["md5"]
                    ):
                        update_file_valid = True
                    else:
                        print("Update file hash mismatch")
                else:
                    print("Update file length mismatch")
        except IOError:
            print("Failed to read metadata")
        except (JSONDecodeError, KeyError):
            print("Update metadata corrupted, skipping update")

        if not update_file_valid:
            os.unlink(framework_update_file)
            os.unlink(framework_update_meta_file)

    return update_file_valid


def dir_for_version(version):
    """Generates directory name for a framework version.

    Args:
        version: A Version object.

    Returns:
        Directory name as a string.
    """
    return f"revvy-{version}"


def ansi_colored(s, color):
    return f"\033[{color}m{s}\033[0m"


def red(s):
    return ansi_colored(s, "91")


def green(s):
    return ansi_colored(s, "92")


def yellow(s):
    return ansi_colored(s, "93")


def install_update_package(
    install_directory,
    filename,
    is_dev_package: bool,
    dependencies: bool,
    remove_source: bool = True,
):
    """Install update package.

    Extracts, validates and installs the update package. If any step of this
    process fails tries to clean up, and remove the corrupt update package.
    Installation creates a virtualenv, installs required packages via pip from
    a local repository, and places the 'installed' marker file into the
    directory, as the final step, to prove that installation finished
    successfully.

    Args:
        data_directory: Directory path containing the fw update.
        install_directory: Directory path with the fw installations.
    """
    framework_update_file = os.path.join(DATA_DIRECTORY, f"{filename}.data")
    # We have already validated the file, in this function we just clean up the meta file
    # along with the update archive
    framework_update_meta_file = os.path.join(DATA_DIRECTORY, f"{filename}.meta")
    tmp_dir = os.path.join(install_directory, "tmp")

    if os.path.isdir(tmp_dir):
        print(yellow(f"Removing stuck tmp dir: {tmp_dir}"))
        shutil.rmtree(tmp_dir)  # probably failed update?

    # try to extract package
    try:
        with tarfile.open(framework_update_file, "r:gz") as tar:
            print(f"Extracting update package to: {tmp_dir}")
            tar.extractall(path=tmp_dir)
    except (ValueError, tarfile.TarError):
        print("Failed to extract package")
        if remove_source:
            os.unlink(framework_update_file)
            os.unlink(framework_update_meta_file)
        return

    # try to read package version
    # integrity check done by installed package, now only get the version
    version_to_install = read_version(os.path.join(tmp_dir, "manifest.json"))

    if version_to_install is None:
        print("Failed to read package version")
        shutil.rmtree(tmp_dir)
        if remove_source:
            os.unlink(framework_update_file)
            os.unlink(framework_update_meta_file)
        return

    if is_dev_package:
        package_folder_name = INSTALLED_DEV_PACKAGE_NAME
    else:
        package_folder_name = dir_for_version(version_to_install)

    target_dir = os.path.join(install_directory, package_folder_name)

    if os.path.isdir(target_dir):
        if is_dev_package:
            print(yellow("Dev package, overwriting existing version"))
            shutil.rmtree(target_dir)
        else:
            log(yellow(f"{version_to_install} is already installed, skipping"))
            # we don't want to install this package, remove sources
            shutil.rmtree(tmp_dir)
            if remove_source:
                os.unlink(framework_update_file)
                os.unlink(framework_update_meta_file)
            return

    print(f"Installing version: {version_to_install}")
    print(f"Renaming {tmp_dir} to {target_dir}")
    shutil.move(tmp_dir, target_dir)

    print("Running setup")
    install_folder = os.path.join(target_dir, "install")
    lines = []

    if dependencies:
        lines.extend(
            [
                'echo "Setting up venv"',
                f"python3 -m venv {target_dir}/install/venv",
                #
                'echo "Activating venv"',
                f"sh {target_dir}/install/venv/bin/activate",
                #
                'echo "Installing dependencies"',
                f"python3 -m pip install --no-cache-dir -r {install_folder}/requirements.txt --no-index --find-links file:///{install_folder}/packages",
            ]
        )

    lines.extend(
        [
            'echo "Creating marker file"',
            f"touch {target_dir}/installed",
        ]
    )
    subprocess_cmd(lines)

    print("Removing update package")
    if remove_source:
        os.unlink(framework_update_file)
        os.unlink(framework_update_meta_file)


def select_newest_package(directory, skipped_versions):
    """Finds latest, non blacklisted framework version.

    Checks all subdirectories in directory, reads the version information from
    the manifest.json files.

    Args:
        directory: Base directory of installed frameworks.
        skipped_versions: List of path names of framework versions to be
            skipped.

    Returns:
        String path for the newest version.
    """
    newest = Version("0.0")
    newest_path = None

    # find newest framework
    try:
        for fw_dir_name in os.listdir(directory):
            fw_dir = os.path.join(directory, fw_dir_name)
            if fw_dir in skipped_versions:
                continue

            manifest_file = os.path.join(fw_dir, "manifest.json")
            if not os.path.isfile(manifest_file):
                print(f"Manifest file not found: {manifest_file}")
                continue

            version = read_version(manifest_file)
            if version is None:
                print(f"Failed to read version from {manifest_file}")
                continue

            print(f"Found version {version}")
            if fw_dir_name == INSTALLED_DEV_PACKAGE_NAME:
                print(green("Found dev package, stopping search"))
                return fw_dir

            if newest < version:
                newest = version
                newest_path = fw_dir
            else:
                print(f"Skipping {version} - older than {newest}")
    except FileNotFoundError:
        print("Failed to select newest package")
        print(traceback.format_exc())

    return newest_path


# Manual exit. The loader will exit, too. Exiting with OK only makes sense if the package is
# not managed by the revvy.service.
FIRMWARE_RETURN_VALUE_OK = 0

# An error has occurred. The loader is allowed to reload this package
FIRMWARE_RETURN_VALUE_ERROR = 1

# The loader should try to load a previous package
FIRMWARE_RETURN_VALUE_INTEGRITY_ERROR = 2

# The loader should try to install and load a new package
FIRMWARE_RETURN_VALUE_UPDATE_REQUEST = 3


def run_pi_firmware(path: str):
    """Runs revvy framework in its virtualenv.

    Args:
        path: (String) Path to directory containing the revvy code.

    Returns:
        Integer error code.
        See revvy/utils.py's RevvyStatusCode for actual codes.
        0 - OK
        other - ERROR, INTEGRITY_ERROR, UPDATE_REQUEST, etc...
    """

    venv_exists = os.path.isdir(f"{path}/install/venv")

    while True:
        print(green(f"Starting {path}"))
        lines = []

        if venv_exists:
            lines.extend(
                [
                    # activate venv
                    f"sh {path}/install/venv/bin/activate",
                ]
            )

        lines.extend(
            [
                # start script
                f"python3 -u {path}/revvy.py",
            ]
        )

        try:
            return_value = subprocess_cmd(lines)
        except KeyboardInterrupt:
            return_value = FIRMWARE_RETURN_VALUE_OK

        print(f"Script exited with {return_value}")
        if return_value == FIRMWARE_RETURN_VALUE_ERROR:
            # if script dies with error, restart
            # TODO: maybe measure runtime and if shorter than X then disable the package
            print(yellow("Firmware exited with error, restarting"))
            continue

        return return_value


def wait_for_board_powered():
    # We use the AMP_EN pin as input to detect if the control board is on. The AMP_EN line
    # has a pullup resistor, so it's high if the board is connected and powered.
    # Due to some wiringpi weirdness, we use the header pin number for gpio mode and the
    # wiringpi pin number for reading the value. Use `gpio readall` to see the pin numbers.
    AMP_EN_HEADER_PIN = "22"
    AMP_EN_WIRINGPI_PIN = "3"

    # configure AMP_EN to input
    subprocess_cmd(f"gpio -g mode {AMP_EN_HEADER_PIN} in")

    # read AMP_EN to detect if Revvy is ON
    amp_en = subprocess.check_output(["gpio", "read", AMP_EN_WIRINGPI_PIN])
    while amp_en != b"1\n":
        print("Device is off... waiting")
        time.sleep(1)
        amp_en = subprocess.check_output(["gpio", "read", AMP_EN_WIRINGPI_PIN])


def start_newest_framework(skipped_versions: list[str]):
    """Starts the newest framework version.

    Returns True if the script should terminate, False if it should continue.
    """

    wait_for_board_powered()

    print("Looking for firmware packages")
    path = select_newest_package(INSTALLED_PACKAGES_DIR, skipped_versions)
    if not path:
        # if there is no such package, start the built in one
        print("No user package found, trying default")
        path = select_newest_package(DEFAULT_PACKAGE_DIR, [])

    if not path:
        # if, for some reason there is no built-in package, stop
        print("There are no more packages to try - exit")
        return True

    return_value = run_pi_firmware(path)
    if return_value == FIRMWARE_RETURN_VALUE_OK:
        print("Manual exit, exiting loader")
        return True

    if return_value == FIRMWARE_RETURN_VALUE_INTEGRITY_ERROR:
        # if script dies with integrity error, mark the package as unstartable
        # and try the next one
        print(f"Integrity error or otherwise unstartable package - add {path} to skipped list")
        skipped_versions.append(path)

    return False


def install_updates(install_directory, dependencies: bool):
    sources = [
        (DEV_PACKAGE_NAME, True),
        ("2", False),
    ]

    for package, is_dev in sources:
        if has_update_package(DATA_DIRECTORY, package):
            cleanup_invalid_installations(install_directory)
            install_update_package(install_directory, package, is_dev, dependencies)


def install_test_package(test_package: str):
    """Sets up the test environment.

    Args:
        test_package: Path to the test package.
    """
    print(f"Setting up test environment for {test_package}")

    # Remove previous test package, if any
    try:
        shutil.rmtree(TEST_PACKAGE_DIR)
    except FileNotFoundError:
        pass

    os.makedirs(TEST_PACKAGE_DIR, exist_ok=True)

    # Install the test package
    install_update_package(TEST_PACKAGE_DIR, test_package, is_dev_package=True, remove_source=False)


def run_tests() -> int:
    print(green(f"Running tests"))

    lines = [
        # activate venv
        f"sh install/venv/bin/activate",
        # start script
        f"python3 -m tests.hil_tests.tests",
    ]
    try:
        return subprocess_cmd(lines)
    except KeyboardInterrupt:
        return -1


def main():
    """Runs revvy from directory.

    Handles the command line arguments of the script.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--install-only",
        help="Install updates but do not start framework",
        action="store_true",
    )
    parser.add_argument(
        "--skip-dependencies",
        help="Do not set up a virtual env",
        action="store_true",
    )
    parser.add_argument(
        "--install-default",
        help="Install the default package. Requires --install-only"
        " and the filesystem must be writeable.",
        action="store_true",
    )
    parser.add_argument(
        "--setup",
        help="Set up the given package as software under test",
        action="store_true",
    )
    parser.add_argument(
        "--service",
        help="The script has been started by a systemd service.",
        action="store_true",
    )
    parser.add_argument(
        "--test",
        help="Run test scripts",
        action="store_true",
    )

    args = parser.parse_args()

    if args.service:
        # ignore logs when running as a service
        log = lambda msg: ...

    if args.test:
        if args.setup:
            install_test_package(DEV_PACKAGE_NAME)

        print(f"Running tests")
        old_path = os.getcwd()
        try:
            os.chdir(os.path.join(TEST_PACKAGE_DIR, INSTALLED_DEV_PACKAGE_NAME))
            return run_tests()
        finally:
            os.chdir(old_path)

    if args.install_only:
        if args.install_default:
            install_directory = DEFAULT_PACKAGE_DIR
        else:
            install_directory = INSTALLED_PACKAGES_DIR

        print(f"Install directory: {install_directory}")
        print(f"Data directory: {DATA_DIRECTORY}")
        install_updates(install_directory, not args.skip_dependencies)
        print("--install-only flag is set, will not start framework")
        return 0

    # Entering "normal" operation
    # Steps:
    # - Cleanup failed installations
    # - Search for fw update and install it
    # - Execute latest version
    # - If execution terminates normally, exit launcher
    # - If execution terminates with integrity_error, mark version as ignored and retry
    # - Otherwise restart the same version

    skipped_versions = []
    while True:
        cleanup_invalid_installations(INSTALLED_PACKAGES_DIR)
        install_updates(INSTALLED_PACKAGES_DIR, not args.skip_dependencies)

        if start_newest_framework(skipped_versions):
            print("Exiting launcher")
            return 0


if __name__ == "__main__":
    current_directory = os.path.dirname(__file__)
    current_directory = os.path.abspath(current_directory)
    os.chdir(current_directory)
    exit_code = main()
    sys.exit(exit_code)
