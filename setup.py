#!/usr/bin/env python
# * coding: utf8 *
'''
setup.py

A module that installs the cli tool.

run `pip install ./` from the folder containing this file
'''
from boost import __version__
from setuptools import find_packages
from setuptools import setup

setup(
    name='boost',
    version=__version__,
    description='A broadband speed reporting command line program in Python.',
    long_description='Max Broadband Speed for Address Points, By Submission Period',
    url='https://github.com/agrc/broadband-cli',
    author='AGRC',
    author_email='agrc@utah.gov',
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: MIT',
        'Natural Language :: English',
        'Operating System :: Windows',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='cli',
    packages=find_packages(exclude=['docs', 'tests*']),
    install_requires=['docopt'],
    entry_points={
        'console_scripts': [
            'boost=boost.__main__:main',
        ],
    })
