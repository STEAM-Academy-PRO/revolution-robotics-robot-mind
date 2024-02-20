import os
from os import path


def find_files(pathname):
    pathname = path.realpath(pathname)
    if path.isfile(pathname):
        yield pathname
    elif path.isdir(pathname):
        for f in os.listdir(pathname):
            if f != "__pycache__":
                for sub in find_files(path.join(pathname, f)):
                    yield sub


def get_version():
    version = os.popen("git rev-list --count HEAD").read()
    # print('version', version)
    version = version.strip()

    branch = os.popen("git rev-parse --abbrev-ref HEAD").read()
    branch = branch.strip()

    return branch, "0.1.{}".format(version)
