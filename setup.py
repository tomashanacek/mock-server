#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from distutils.core import setup


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

with open(path.join(base, 'requirements.txt')) as f:
    install_requires = [r.strip() for r in f if '#egg=' not in r]

setup(
    name="mock-server",
    version="0.1.0",
    description=("Simple mock server for REST API"),
    long_description=read("README.md"),
    author="Tomas Hanacek",
    author_email="tomas.hanacek1@gmail.com",
    url="https://github.com/tomashanacek/mock-server",
    license="http://www.apache.org/licenses/LICENSE-2.0"
    packages=["mock_server"],
    scripts=["bin/mock-server.py"],
    install_requires=install_requires
)
