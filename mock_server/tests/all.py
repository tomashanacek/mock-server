# -*- coding: utf-8 -*-

import unittest
from test_restapi import TestRestApi
from test_xmlrpc import TestXMLRPC


def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestRestApi))
    test_suite.addTest(unittest.makeSuite(TestXMLRPC))
    return test_suite
