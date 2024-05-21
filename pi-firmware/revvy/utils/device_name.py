from revvy.utils.directories import WRITEABLE_DATA_DIR
from revvy.utils.file_storage import FileStorage
from revvy.utils.functions import get_serial


# Serial is coming from the CPU info.
serial = get_serial()
device_storage = FileStorage(WRITEABLE_DATA_DIR)

# By default, the device's name is its serial number.
device_name = serial
try:
    # Overwrite it, if we have something set in the device-name file.
    custom_device_name = device_storage.read("device-name").decode("ascii")

    if 0 < len(custom_device_name) <= 15:
        device_name = custom_device_name
except Exception:
    pass


def get_device_name() -> str:
    """Returns device name observable value."""
    global device_name
    return device_name


def set_device_name(new_name: str):
    """Set and persist device name"""
    global device_name
    device_storage.write("device-name", new_name.encode("utf-8"))
    device_name = new_name
