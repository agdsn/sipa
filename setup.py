#!/usr/bin/env python2
from setuptools import setup, find_packages

from codecs import open
from os import path

from pip.req import parse_requirements

here = path.abspath(path.dirname(__file__))

install_reqs = parse_requirements('requirements.txt')

reqs = [str(ir.req) for ir in install_reqs]

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
      long_description = f.read()

with open(path.join(here, 'AUTHORS'), encoding='utf-8') as f:
      author = f.read()
      
setup(name='sipa',
      version='0.1',
      description='The Webfrontend for the AGDSN',
      long_description=long_description,
      author=author,
      author_email='softeware@wh2.tu-dresden.de',
      url='https://github.com/agdsn/sipa',
      license='MIT',
      packages=['sipa'],
      include_package_data=True,
      zip_safe=False,
      install_requires=reqs
)
