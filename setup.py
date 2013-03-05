#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# AUTHOR
# Tomas Hanacek <tomas.hanacek1@gmail.com>

import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="mock-server",
    version="0.1.0",
    author="Tomas Hanacek",
    author_email="tomas.hanacek1@gmail.com",
    description=("Mock server"),
    packages=find_packages(),
    long_description=read("README.md"),
    test_suite = "mock_server.test.all"
)
