#! /usr/bin/env python
# coding=utf-8

"""
checkmyreqs

Parses a requirements file to check what libraries are listed as supported with a given Python version

Uses xmlrpc pypi methods as defined here: http://wiki.python.org/moin/PyPIXmlRpc
"""

from __future__ import print_function

import argparse
import os
import re
import sys
import errno
import csv

from blessings import Terminal

TERMINAL = Terminal()

try:
    # Different location in Python 3
    from xmlrpc.client import ServerProxy
except ImportError:
    from xmlrpclib import ServerProxy


BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CLIENT = ServerProxy('http://pypi.python.org/pypi')

IGNORED_PREFIXES = ['#', 'git+', 'hg+', 'svn+', 'bzr+', '\n', '\r\n']

IS_COMPATIBLE = 'yes'
NOT_COMPATIBLE = 'no'
UNKOWN = 'No Info Available'
NOT_IN_PYPI = 'Not in pypi'

def parse_requirements_file(req_file):
    """
    Parse a requirements file, returning packages with versions in a dictionary
    :param req_file: requirements file to parse

    :return dict of package names and versions
    """
    packages = {}

    for line in req_file:
        line = line.strip()
        for prefix in IGNORED_PREFIXES:
            if not line or line.startswith(prefix):
                line = None
                break
        if line:
            line = line.strip()

            if '==' in line:
                package_name, version = line.split('==')
                packages[package_name] = version
            else:
                print(TERMINAL.yellow('{} not pinned to a version, skipping'.format(line)))

    return packages

def check_packages(packages, python_version):
    """
    Checks a list of packages for compatibility with the given Python version
    Prints warning line if the package is not supported for the given Python version
    If upgrading the package will allow compatibility, the version to upgrade is printed
    If the package is not listed on pypi.python.org, error line is printed

    :param packages: dict of packages names and versions
    :param python_version: python version to be checked for support
    """
    pkg_compatibility_status_list = []
    for package_name, package_version in packages.items():
        print(TERMINAL.bold(package_name))

        package_info = CLIENT.release_data(package_name, package_version)
        package_releases = CLIENT.package_releases(package_name)
        if package_releases:
            latest_release = package_releases[-1]
        else:
            latest_release = ''
        pkg_status = [package_name, package_version, latest_release]
        if package_releases:
            supported_pythons = get_supported_pythons(package_info)
            pkg_status.append(','.join(supported_pythons))

            # Some entries list support of Programming Language :: Python :: 3
            # So we also want to check the major revision number of the version 
            # against the list of supported versions
            major_python_version = python_version.split('.')[0]

            if python_version in supported_pythons:
                print(TERMINAL.green('compatible'))
                pkg_status.append(IS_COMPATIBLE)
            elif major_python_version in supported_pythons:
                print(TERMINAL.green('compatible'))
                pkg_status.append(IS_COMPATIBLE)
            else:
                latest_version = package_releases[0]
                latest_package_info = CLIENT.release_data(package_name, latest_version)
                latest_supported_pythons = get_supported_pythons(latest_package_info)

                upgrade_available = ''


                if supported_pythons:

                    if python_version in latest_supported_pythons:
                        upgrade_available = ' - update to v{} for support'.format(latest_version)

                    print(TERMINAL.red('not compatible{}'.format(upgrade_available)))
                    pkg_status.append(NOT_COMPATIBLE)
                else:
                    # We get here if there was not compatability information for
                    # the package version we requested

                    if python_version in latest_supported_pythons:
                        upgrade_available = ' - update to v{} for explicit support'.format(latest_version)

                    print(TERMINAL.yellow('not specified{}').format(upgrade_available))
                    pkg_status.append(UNKOWN)

        else:
            print(TERMINAL.red('not listed on pypi.python.org'))
            pkg_status.append(NOT_IN_PYPI)
        pkg_compatibility_status_list.append(pkg_status)
        print('-----')
    return pkg_compatibility_status_list


def get_supported_pythons(package_info):
    """
    Returns a list of supported python versions for a specific package version
    :param package_info: package info dictionary, retrieved from pypi.python.org
    :return: Versions of Python supported, may be empty
    """
    versions = []
    classifiers = package_info.get('classifiers', [])

    for c in classifiers:
        if c.startswith('Programming Language :: Python ::'):
            version = c.split(' ')[-1].strip()
            versions.append(version)

    return versions


def main():
    """
    Parses user input for requirements files and python version to check compatibility for
    :return:
    """
    parser = argparse.ArgumentParser('Checks a requirements file for Python version compatibility')

    parser.add_argument(
        '-f', '--files', required=False,
        help='requirements file(s) to check',
        type=argparse.FileType(), nargs="+"
    )
    parser.add_argument(
        '-p', '--python', required=False,
        help='Version of Python to check against. E.g. 2.5',
        default='.'.join(map(str, [sys.version_info.major, sys.version_info.minor]))
    )

    parser.add_argument(
        '-o', '--output', required=False,
        help='Name of file to output with compatibility status. If not provided output will only be shown in the '
             'terminal. Usually a csv filename e.g. pacakges.csv',
        default=False
    )

    args = parser.parse_args()

    # If a file wasn't passed in, check if pip freeze has been piped, then try to read requirements.txt
    if args.files is None:
        if not sys.stdin.isatty():
            args_files = [sys.stdin]
        else:
            try:
                args_files = [open('requirements.txt')]

            except IOError:
                print('Default file requirements.txt not found')
                sys.exit(errno.ENOENT)
    else:
        args_files = args.files

    # Make sure Python version is in X.Y format
    if re.match('^[2-3].[0-9]$', args.python) is None:
        print('Python argument invalid: Must be in X.Y format, where X is 2 or 3 and Y is 0-9')
        sys.exit(errno.EINVAL)

    print('Checking for compatibility with Python {}'.format(args.python))

    compatibility_list = []

    for filepath in args_files:
        print('{0}\r\n*****'.format(filepath.name))

        packages = parse_requirements_file(filepath)
        compatibility_list += check_packages(packages, args.python)
        print('\n')

    if args.output:
        print("Yes")
        print(compatibility_list)
        with open(args.output, "w") as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow(['package_name', 'package_version', 'latest_package_releases', 'python_versions_supported', 'is_compatible'])
            for row in compatibility_list:
                writer.writerow(row)


if __name__ == '__main__':
    main()
