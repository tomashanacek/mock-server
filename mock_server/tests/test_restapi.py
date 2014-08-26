# -*- coding: utf-8 -*-

import os
import subprocess
import time

import tornado.testing
from mock_server.application import Application


class TestRestApi(tornado.testing.AsyncHTTPTestCase):

    def setUp(self):
        super(TestRestApi, self).setUp()
        self._upstream_server = subprocess.Popen(
            "mock_server/tests/upstream_server.py")
        time.sleep(2 / 10.0)

    def tearDown(self):
        super(TestRestApi, self).tearDown()
        self._upstream_server.terminate()

    def get_app(self):
        dirname = os.path.dirname(__file__)

        return Application(
            7777, "localhost", os.path.join(dirname, "api/"),
            False, "application.json", os.path.join(dirname, "provider.py"))

    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()

    def test_list_users(self):
        response = self.fetch("/user")

        self.assertFalse(response.error)
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, '["john", "tom"]\n')

    def test_user_doesnt_exists_with_custom_header(self):
        response = self.fetch("/user/tom?__statusCode=404")

        self.assertEqual(response.code, 404)
        self.assertEqual(response.body,
                         '{"message": "User doesn\'t exists"}\n')
        self.assertEqual(response.headers["MyCustomHeader"], "test")

    def test_noexists_method(self):
        response = self.fetch("/user/john/data")

        self.assertEqual(response.code, 404)
        self.assertEqual(
            response.body,
            'Api does\'t exists, '
            '<a href="/__manage/create?url_path=/user/'
            'john/data&method=GET&status_code=200&format=json">'
            'create resource method</a>')

    def test_url_with_variables(self):
        response = self.fetch("/user/lisa/family/bart")

        self.assertEqual(response.code, 200)
        self.assertTrue("bart" in response.body)

    def test_hello_on_upstream_server(self):
        response = self.fetch("/hello")

        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, "Hello from upstream server")

    def test_custom_provider(self):
        response = self.fetch("/abc")

        self.assertEqual(response.code, 200)
        self.assertEqual(
            response.body,
            '{"surname": "Hanacek", "name": "Tomas"}')
        self.assertEqual(
            response.headers["Content-Type"],
            "application/json; charset=utf-8")
