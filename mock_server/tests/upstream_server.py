#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wsgiref.simple_server import make_server
from wsgiref.util import setup_testing_defaults


def simple_app(env, start_response):
    setup_testing_defaults(env)

    if env["PATH_INFO"] == "/hello":
        start_response("200 OK", [("Content-Type", "application/json")])
        return ["Hello from upstream server"]
    else:
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return []


if __name__ == "__main__":
    httpd = make_server("", 8089, simple_app).serve_forever()
