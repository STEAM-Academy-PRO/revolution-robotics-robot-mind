""" Keep our folders organized here. """

import os
from os.path import dirname, join


# Get the current directory
current_directory = os.path.realpath(__file__)

# Get the folder two levels up
CURRENT_INSTALLATION_PATH = dirname(dirname(dirname(current_directory)))

os.chdir(CURRENT_INSTALLATION_PATH)

WRITEABLE_DIR_ROOT = os.path.realpath(join(CURRENT_INSTALLATION_PATH, "..", "..", "..", "user"))

WRITEABLE_DATA_DIR = os.path.realpath(join(WRITEABLE_DIR_ROOT, "data"))

WRITEABLE_ASSETS_DIR = os.path.realpath(join(WRITEABLE_DIR_ROOT, "assets"))

BLE_STORAGE_DIR = os.path.realpath(join(WRITEABLE_DIR_ROOT, "ble"))

PACKAGE_ASSETS_DIR = os.path.realpath(join(CURRENT_INSTALLATION_PATH, "data", "assets"))
