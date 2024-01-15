#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-only

# check whether the current package files are valid according to the manifest
# start using 'python -m tools.check_manifest' from the root directory

from revvy.utils.functions import file_hash, read_json


def check_manifest(manifest_file):
    print('[Integrity Checker] Checking manifest file: {}'.format(manifest_file))

    manifest = read_json(manifest_file)
    hashes = manifest['files']

    for file in hashes:
        expected = hashes[file]
        hash_value = file_hash(file)

        if hash_value != expected:
            print('[Integrity Checker] Integrity check failed for {}'.format(file))
            return False

    return True


if __name__ == "__main__":
    if check_manifest('manifest.json'):
        print('Valid')
    else:
        print('Invalid')
