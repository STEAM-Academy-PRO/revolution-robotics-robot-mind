#!/usr/bin/python3

# check whether the current package files are valid according to the manifest
# start using 'python -m tools.check_manifest' from the root directory

from revvy.utils.functions import file_hash, read_json
from revvy.utils.logger import get_logger

log = get_logger("Integrity Checker")


def check_manifest(manifest_file):
    log("[Integrity Checker] Checking manifest file: {}".format(manifest_file))

    manifest = read_json(manifest_file)
    hashes = manifest["files"]

    for file in hashes:
        expected = hashes[file]
        hash_value = file_hash(file)

        if hash_value != expected:
            log("[Integrity Checker] Integrity check failed for {}".format(file))
            return False

    return True


if __name__ == "__main__":
    if check_manifest("manifest.json"):
        log("Valid")
    else:
        log("Invalid")
