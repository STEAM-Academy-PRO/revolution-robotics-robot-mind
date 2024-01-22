#!/usr/bin/python3
# start using 'python -m dev_tools.create_package' from the root directory
import argparse
import json
import tarfile
import os
import shutil
from os import path

from revvy.utils.functions import file_hash, read_json
from tools.common import find_files
from dev_tools.generate_manifest import gen_manifest


def create_package(sources, output):
    print('Creating framework package: {}'.format(output))
    prefix = path.join(path.dirname(path.realpath(path.join(__file__, '..'))), '')

    with tarfile.open(output, "w:gz") as tar:
        for source in sources:
            for file in find_files(source):
                if file.startswith(prefix):
                    filename = file[len(prefix):].replace(path.sep, '/')
                    # print('Add file to package archive: {}'.format(filename))
                    tar.add(file, arcname=filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--dev', help='Create package for development', action='store_true')

    args = parser.parse_args()

    if args.dev:
        # Generate empty manifest to allow editing files, do not install requirements at every packing.
        manifest_source = []
    else:
        # Only download python packages on prod build
        print('Downloading requirements')
        os.popen('pip3 download -r install/requirements.txt -d install/packages --platform arm --no-deps').read()

        manifest_source = [
            'data/',
            'install/requirements.txt',
            'install/packages/',
            'revvy/',
            'revvy.py'
        ]

    gen_manifest(manifest_source, 'manifest.json')
    manifest = read_json('manifest.json')

    package_sources = [
        'revvy/',
        'install/requirements.txt',
        'install/packages/',
        'data/',
        'revvy.py',
        '__init__.py',
        'tools/',
        'manifest.json'
    ]

    version = manifest['version'].replace('/', '-')
    minor_version = version.split(".")[2]

    package_path = 'install/pi-firmware-{}.tar.gz'.format(version)
    data_path = 'install/pi-firmware.data'
    meta_file = 'install/pi-firmware.meta'
    create_package(package_sources, package_path)

    shutil.copy(package_path, data_path)

    if not args.dev:
        print('Remove downloaded packages')
        shutil.rmtree('install/packages')

    file_hash = file_hash(package_path)
    file_size = os.stat(package_path).st_size

    with open(meta_file, "w") as mf:
        json.dump({'length': file_size, 'md5': file_hash}, mf)

    print('Package created: {}'.format(package_path))
    print('Package checksum: {}'.format(file_hash))
