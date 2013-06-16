#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from mock_server.tests.all import suite

if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())
