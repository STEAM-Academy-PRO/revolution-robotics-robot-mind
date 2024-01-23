#!/usr/bin/python3

# create manifest file containing the version and individual file checksum values
# start using 'python -m tools.generate_manifest' from the root directory
import json
from datetime import datetime
from os import path

from revvy.utils.functions import file_hash
from tools.common import find_files, get_version


def gen_manifest(sources, output):
    print('Creating manifest file: {}'.format(output))
    prefix = path.join(path.dirname(path.realpath(path.join(__file__, '..'))), '')

    hashes = {}
    extensions = ['.py', '.mp3', '.data', '.meta', '.txt', '.tar.gz', '.bin', '.json']

    for source in sources:
        for file in find_files(source):
            if file.startswith(prefix) and any(file.endswith(ext) for ext in extensions):
                filename = file[len(prefix):].replace(path.sep, '/')
                checksum = file_hash(file)
                # print('Add file to manifest: {} (checksum: {})'.format(filename, checksum))
                hashes[filename] = checksum

    branch, version = get_version()

    manifest = {
        'version': version,
        'branch': branch,
        'manifest-version': 1.1,
        'generated': datetime.now().isoformat(),
        'files': hashes
    }

    with open(output, "w") as mf:
        json.dump(manifest, mf, indent=4)


if __name__ == "__main__":
    manifest_source = [
        'data/',
        'install/requirements.txt',
        'install/packages/',
        'revvy/',
        'revvy.py'
    ]
    gen_manifest(manifest_source, 'manifest.json')
