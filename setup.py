#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name='yardc',
    version='1.0',
    description='Yet another remote desktop client',
    install_requires=['libvirt-python', 'paramiko', 'click', 'defusedxml', 'pygpgme', 'pyyaml'],
    packages=['yardc'],
    entry_points={
        'console_scripts': [
            'yardc = yardc.cli:cli'
        ]
    }
)
