#!/usr/bin/env python
# coding=utf-8

import os
import sys
from setuptools import setup, Command, find_packages


APP_NAME = 'checkmyreqs'
VERSION = '0.3.1'

# Grab requirments.
with open('requirements.txt') as f:
    required = f.readlines()

class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        import sys,subprocess
        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)

settings = {}

# Publish Helper.
if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

# Build Helper.
if sys.argv[-1] == 'build':
    try:
        import py2exe
    except ImportError:
        print('py2exe is required to continue.')
        sys.exit(1)

    sys.argv.append('py2exe')

    settings.update(
        zipfile = None,
        options = {
            'py2exe': {
                'compressed': 1,
                'optimize': 0,
                'bundle_files': 1}})

settings.update(
    name=APP_NAME,
    version=VERSION,
    author='Dustin Collins',
    author_email='dustinrcollins@gmail.com',
    packages=find_packages(),
    scripts=['checkmyreqs'],
    url='https://github.com/dustinmm80/checkmyreqs',
    license='MIT',
    description='Check your project requirements for Python version compatibility',
    long_description=open('README.rst').read(),
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4'
    ],
    cmdclass = {'test': PyTest},
    install_requires=required
)

setup(**settings)
