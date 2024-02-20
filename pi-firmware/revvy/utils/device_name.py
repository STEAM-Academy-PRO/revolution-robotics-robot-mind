
from revvy.utils.directories import WRITEABLE_DATA_DIR
from revvy.utils.file_storage import FileStorage
from revvy.utils.functions import get_serial


# Serial is coming from the CPU info.
serial = get_serial()
device_storage = FileStorage(WRITEABLE_DATA_DIR)

try:
    # Overwrite it, if we have something set in the device-name file.
    device_name = device_storage.read('device-name').decode("ascii")

    if 0 == len(device_name) or len(device_name) > 15:
        device_name = f'Revvy_{serial}'
except Exception:
    device_name = f'Revvy_{serial}'


def get_device_name():
    """ Returns device name observable value. """
    global device_name
    return device_name

def set_device_name(new_name):
    """ Set and persist device name """
    global device_name
    device_storage.write('device-name', new_name.encode("utf-8"))
    device_name = new_name

