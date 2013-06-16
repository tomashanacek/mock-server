# -*- coding: utf-8 -*-

import os

import tornado.testing
from mock_server.application import Application


class TestXMLRPC(tornado.testing.AsyncHTTPTestCase):

    def get_app(self):
        return Application(7777, "localhost",
                           os.path.join(os.path.dirname(__file__), "api/"),
                           False, "application.json")

    def test_list_users(self):
        response = self.fetch(
            "/RPC2", method="POST",
            body="<?xml version='1.0'?><methodCall><methodName>user.list"
            "</methodName><params></params></methodCall>")

        self.assertFalse(response.error)
        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.body,
            "<?xml version='1.0'?>\n<methodResponse>\n<params>\n<param>\n"
            "<value><array><data>\n<value><string>john</string></value>\n"
            "<value><string>tom</string></value>\n</data></array></value>"
            "\n</param>\n</params>\n</methodResponse>\n")
