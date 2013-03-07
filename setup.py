#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup

root_dir = os.path.dirname(__file__)


def read(fname):
    with open(os.path.join(root_dir, fname)) as f:
        return f.read()

with open(os.path.join(root_dir, "requirements.txt")) as f:
    install_requires = [r.strip() for r in f if "#egg=" not in r]

setup(
    name="mock-server",
    version="0.1.0",
    description=("Simple mock server for REST API"),
    long_description=read("README.md"),
    author="Tomas Hanacek",
    author_email="tomas.hanacek1@gmail.com",
    url="https://github.com/tomashanacek/mock-server",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    packages=["mock_server"],
    scripts=["bin/mock-server"],
    install_requires=install_requires,
    include_package_data=True
)
