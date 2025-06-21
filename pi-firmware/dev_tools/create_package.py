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
import glob


def copy_blockly_if_exists():
    print("Copying Blockly files if they exist...")
    vscode_settings_path = ".vscode/settings.json"
    blockly_path = None
    if path.exists(vscode_settings_path):
        with open(vscode_settings_path, "r") as f:
            try:
                settings = json.load(f)
                blockly_path = settings.get("blockly")
            except Exception as e:
                pass
    if blockly_path is not None:
        if (path.exists(blockly_path) and path.isdir(blockly_path)):
            blockly_static_path = "static/blockly"
            os.makedirs(blockly_static_path, exist_ok=True)
            for filename in [
                "interface.html",
                "blockly_compressed.js",
                "blocks_compressed.js",
                "python_compressed.js",
                "prism.css",
                "prism.js",
                "toolbox/toolboxes.js",
                "toolbox/tabs.js",
                "style.css",
                "msg/js/en.js",
                "media/*"
            ]:
                # Handle globs and directories
                src_pattern = path.join(blockly_path, filename)
                matches = glob.glob(src_pattern, recursive=True)
                for src in matches:
                    # Compute relative path from blockly_path
                    rel_path = path.relpath(src, blockly_path)
                    dst = path.join(blockly_static_path, rel_path)
                    dst_dir = path.dirname(dst)
                    os.makedirs(dst_dir, exist_ok=True)
                    if path.isdir(src):
                        # Copy directory recursively
                        if not path.exists(dst):
                            shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)




def create_package(sources, output):
    print("Creating framework package: {}".format(output))

    if args.dev:
        copy_blockly_if_exists()

    prefix = path.join(path.dirname(path.realpath(path.join(__file__, ".."))), "")

    with tarfile.open(output, "w:gz") as tar:
        for source in sources:
            for file in find_files(source):
                if file.startswith(prefix):
                    filename = file[len(prefix) :].replace(path.sep, "/")
                    # print('Add file to package archive: {}'.format(filename))
                    tar.add(file, arcname=filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev", help="Create package for development", action="store_true")

    args = parser.parse_args()

    package_sources = [
        "revvy/",
        "static/",
        "install/requirements.txt",
        "install/requirements_pi_dev.txt",
        "data/",
        "revvy.py",
        "__init__.py",
        "tools/",
        "manifest.json",
    ]

    if args.dev:
        # Generate empty manifest to allow editing files, do not install requirements at every packing.
        manifest_source = []
        package_sources.extend(["tests/", "dev_tools/"])
    else:
        manifest_source = ["data/", "install/requirements.txt", "revvy/", "revvy.py"]

    gen_manifest(manifest_source, "manifest.json")
    manifest = read_json("manifest.json")

    version = manifest["version"].replace("/", "-")
    minor_version = version.split(".")[2]

    package_path = "install/framework-{}.tar.gz".format(version)
    data_path = "install/pi-firmware.data"
    meta_file = "install/pi-firmware.meta"
    create_package(package_sources, package_path)

    shutil.copy(package_path, data_path)

    file_hash = file_hash(package_path)
    file_size = os.stat(package_path).st_size

    with open(meta_file, "w") as mf:
        json.dump({"length": file_size, "md5": file_hash}, mf)

    print("Package created: {}".format(package_path))
    print("Package checksum: {}".format(file_hash))
