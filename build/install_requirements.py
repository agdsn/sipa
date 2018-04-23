#!/usr/bin/env python
import sys
from os.path import join
import subprocess

DEFAULT_REQUIREMENTS = 'requirements.txt'
# this script expect to be started from `sipa/`
PATH = './build/requirements/'


def main():
    files_to_install = {DEFAULT_REQUIREMENTS, *sys.argv[1:]}
    for filename in files_to_install:
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', '-r', join(PATH, filename)])


if __name__ == '__main__':
    main()
