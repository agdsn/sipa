#!/usr/bin/env python
import sys

import pip


DEFAULT_REQUIREMENTS = 'requirements.txt'


def main():
    files_to_install = {DEFAULT_REQUIREMENTS, *sys.argv[1:]}
    for file in files_to_install:
        print("Installing requirements from", file)
        pip.main(['install', '-r', file])

if __name__ == '__main__':
    main()
