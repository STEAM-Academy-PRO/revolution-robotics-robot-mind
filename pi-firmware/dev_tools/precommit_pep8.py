#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-only
import argparse
import re
import subprocess
import sys


def system(*args, **kwargs):
    kwargs.setdefault('stdout', subprocess.PIPE)
    proc = subprocess.Popen(args, **kwargs)
    out, err = proc.communicate()
    return out.decode("utf-8") if out else None


def main(check_all):
    if check_all:
        files = ['.']
    else:
        modified = re.compile('^[AM]+\\s+(?P<name>.*\\.py)', re.MULTILINE)
        files = system('git', 'status', '--porcelain')
        files = modified.findall(files)

    output = system('pycodestyle', '--max-line-length=120', *files)

    if output:
        print(output)
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-all', help='Run code style check on whole project', action='store_true')

    input_args = parser.parse_args()

    main(input_args.check_all)
