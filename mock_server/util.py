# -*- coding: utf-8 -*-

import os
import logging
import string
from random import choice


def read_file(filename):
    if os.path.isfile(filename):
        try:
            with open(filename) as f:
                content = f.read()
                return content
        except IOError:
            logging.exception("Error in reading file: %s" % filename)
            return None


def generate_password(length=8):
    chars = string.letters + string.digits

    return ''.join(choice(chars) for _ in xrange(length))
