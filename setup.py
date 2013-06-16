# -*- coding: utf-8 -*-

import os
from setuptools import setup
from mock_server import __version__

root_dir = os.path.dirname(__file__)


def read(fname):
    with open(os.path.join(root_dir, fname)) as f:
        return f.read()

with open(os.path.join(root_dir, "requirements.txt")) as f:
    install_requires = [r.strip() for r in f if "#egg=" not in r]

description = "%s\n\n%s" % (read("README.rst"), read("CHANGES.rst"))

classifiers = ["Programming Language :: Python",
               "License :: OSI Approved :: Apache Software License",
               "Intended Audience :: Developers",
               "Topic :: Internet",
               "Topic :: Software Development :: Documentation"]


setup(
    name="mock-server",
    version=__version__,
    description=("Simple mock server for REST API"),
    long_description=description,
    author="Tomas Hanacek",
    author_email="tomas.hanacek1@gmail.com",
    url="https://github.com/tomashanacek/mock-server",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    packages=["mock_server"],
    scripts=["bin/mock-server"],
    install_requires=install_requires,
    include_package_data=True,
    classifiers=classifiers,
    test_suite="mock_server.tests.all.suite"
)
