#!/usr/bin/env python

import sys

from setuptools import setup, find_packages

if not sys.version_info[0] == 3:
    print("only python3 supported!")
    sys.exit(1)

setup(
    name="actionSHARK",
    version="1.0.0",
    author="Ahmad Hatahet",
    author_email="ahmad.hatahet@hotmail.com",
    description="Collect data from GitHub actions (workflows, runs, jobs, artifacts)",
    install_requires=[
        "mongoengine",
        "pymongo",
        "requests>=2.10.0",
        "oauthlib>=3.0.0",
        "pycoshark>=1.3.2",
    ],
    url="https://github.com/smartshark/actionSHARK",
    download_url="https://github.com/smartshark/actionSHARK/archive/refs/heads/main.zip",
    packages=find_packages(),
    test_suite="tests",
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 2 - Under Development",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache2.0 License",
        "Operating System :: POSIX :: Linux",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
