#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# AUTHOR
# Tomas Hanacek <tomas.hanacek1@gmail.com>

import os
import logging
import re
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.escape import json_encode, json_decode
from tornado.options import define, options

import json
import datetime

from email.parser import Parser
from data import SUPPORTED_FORMATS, SUPPORTED_MIMES, DEFAULT_FORMAT

define("address", default="localhost", help="run on the given address")
define("port", default=8888, help="run on the given port", type=int)
define("dir", help="dir with api definitions")


class Application(tornado.web.Application):
    def __init__(self):
        supported_formats = "|".join(
            map(lambda x: ".%s" % x, SUPPORTED_FORMATS.keys()))
        handlers = [
            (r"/__manage/logs", ResourcesLogsHandler),
            (r"/__manage/create", CreateResourceHandler),
            (r"/__manage", ListResourcesHandler),
            (r"/(.*)(%s)" % supported_formats, MainHandler),
            (r"/(.*)", MainHandler),
        ]
        settings = dict(
            debug=True,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            static_url_prefix="/__static/"
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def create_id_from_url_path(self, url_path):
        return url_path.replace("/", "__")

    def read_file(self, filename):
        if os.path.isfile(filename):
            try:
                f = open(filename, "r")
                content = f.read()
                return content
            except IOError, e:
                logging.warn(e)
                return None

    def log_request(self):
        data = {
            "method": self.request.method,
            "uri": self.request.uri,
            "url_path": self.request.path,
            "status": self.get_status(),
            "remote_ip": self.request.remote_ip,
            "request_time": 1000.0 * self.request.request_time(),
            "headers": self.request.headers,
            "body": self.request.body,
            "arguments": self.request.arguments,
            "cookies": self.request.cookies,
            "time": datetime.datetime.now().isoformat()
        }

        f = open(self.log_request_name, "a")
        f.write("%s\n" % json.dumps(data))
        f.close()

    @property
    def log_request_name(self):
        return os.path.join(options.dir, "access.log")


class ResourcesLogsHandler(BaseHandler):
    def get(self):

        if os.path.exists(self.log_request_name):
            f = open(self.log_request_name)
            data = [json.loads(line) for line in f.readlines()]
            f.close()
        else:
            data = []

        self.render("resources_logs.html", data=data)


class ListResourcesHandler(BaseHandler):
    def get(self):
        paths = [self._complete_resource(item)
                 for item in os.walk(options.dir) if self._check_folder(item)]

        self.render("list_resources.html", paths=paths,
                    port=options.port, address=options.address)

    def _complete_resource(self, item):
        files = {}

        c = re.compile(r"(%s)_(\d+)\.(\w+)" %
                       ("|".join(self.SUPPORTED_METHODS)))

        for current_file in item[2]:
            m = c.match(current_file)
            if m is None:
                continue
            method, status_code, format = m.groups()
            if (method, status_code) in files:
                files[(method, status_code)].append(
                    (format, self._load_file(
                        "%s/%s" % (item[0], current_file))))
            else:
                files[(method, status_code)] = \
                    ([(format, self._load_file(
                        "%s/%s" % (item[0], current_file)))])

        resource = {
            "url_path": item[0][len(options.dir):],
            "files": files
        }

        resource["id"] = self.create_id_from_url_path(resource["url_path"])

        return resource

    def _load_file(self, path):
        f = open(path)
        data = f.read()
        f.close()
        return data

    def _check_folder(self, item):
        if not item[2]:
            return False

        c = re.compile(r"(%s)_\d+\..*" % ("|".join(self.SUPPORTED_METHODS)))

        for current_file in item[2]:
            if c.search(current_file):
                return True

        return False


class CreateResourceHandler(BaseHandler):
    def get(self):
        url_path = self.get_argument("url_path", "")
        method = self.get_argument("method", "GET")
        status_code = self.get_argument("status_code", 200)
        format = self.get_argument("format", DEFAULT_FORMAT)

        response_body = self.read_file(
            os.path.join(options.dir, url_path,
                         "%s_%s.%s" % (method, status_code, format)))
        response_headers = self.read_file(
            os.path.join(options.dir, url_path,
                         "%s_H_%s.%s" % (method, status_code, format)))

        self.render(
            "create_resource.html",
            url_path=url_path, method=method,
            status_code=status_code, format=format,
            edit=True if response_body is not None else False,
            response_body=response_body,
            response_headers=response_headers,
            SUPPORTED_FORMATS=SUPPORTED_FORMATS.keys())

    def post(self):
        url_path = self.get_argument("url_path")
        method = self.get_argument("method")
        status_code = self.get_argument("status_code")
        format = self.get_argument("format")
        response_body = self.get_argument("response_body")
        response_headers = self.get_argument("response_headers", "")

        folder = os.path.join(options.dir, url_path)
        if not os.path.exists(folder):
            os.makedirs(folder)

        content_path = os.path.join(
            folder, "%s_%s.%s" % (method, status_code, format))
        headers_path = os.path.join(
            folder, "%s_H_%s.%s" % (method, status_code, format))

        # write content
        f = file(content_path, "w")
        f.write(response_body)
        f.close()

        # write headers
        f = file(headers_path, "w")
        f.write(response_headers)
        f.close()

        self.redirect("/%s.%s" % (url_path, format))


class MainHandler(BaseHandler):

    @tornado.web.asynchronous
    def head(self, path, format=DEFAULT_FORMAT):
        self._resolve_request(path, format)

    @tornado.web.asynchronous
    def get(self, path, format=DEFAULT_FORMAT):
        self._resolve_request(path, format)

    @tornado.web.asynchronous
    def post(self, path, format=DEFAULT_FORMAT):
        self._resolve_request(path, format)

    @tornado.web.asynchronous
    def delete(self, path, format=DEFAULT_FORMAT):
        self._resolve_request(path, format)

    @tornado.web.asynchronous
    def patch(self, path, format=DEFAULT_FORMAT):
        self._resolve_request(path, format)

    @tornado.web.asynchronous
    def put(self, path, format=DEFAULT_FORMAT):
        self._resolve_request(path, format)

    @tornado.web.asynchronous
    def options(self, path, format=DEFAULT_FORMAT):
        self._resolve_request(path, format)

    def _resolve_request(self, url_path, format):
        format = self._get_format(format)
        method = self.request.method
        status_code = self.get_argument("__statusCode", 200)

        content_path = os.path.join(
            options.dir, url_path, "%s_%s.%s" % (method, status_code, format))

        content = self.read_file(content_path)

        if not content:
            return self._default_response(
                url_path, method, status_code, format)

        # set status
        self.set_status(int(status_code))

        # set headers
        content_type = SUPPORTED_FORMATS[format][0]
        self.set_header("Content-Type", content_type)
        self.set_header("Access-Control-Allow-Origin", "*")

        headers_path = os.path.join(
            options.dir, url_path,
            "%s_H_%s.%s" % (method, status_code, format))
        headers = self._get_headers(headers_path)
        self._set_headers(headers)

        self.log_request()

        # write to response
        self.write(content)

        self.finish()

    def _default_response(self, url_path, method, status_code, format):
        self.set_status(404)
        self.render("api_not_exists.html", url_path=url_path, method=method,
                    status_code=status_code, format=format)

    def _get_format(self, format):
        format = format[1:] if format[0] == "." else format

        if self.request.headers["Accept"] in SUPPORTED_MIMES:
            format = SUPPORTED_MIMES[self.request.headers["Accept"]]

        return format

    def _set_headers(self, headers):
        if not headers:
            return
        for (name, value) in headers:
            self.set_header(name, value)

    def _get_headers(self, filename):
        if os.path.isfile(filename):
            try:
                f = open(filename, "r")
                strip = lambda s: s if len(s) == 0 else s[0] + s[1:].strip()
                headers = "\r\n".join(map(strip, f.readlines()))
                f.close()
                return Parser().parsestr(headers).items()
            except IOError, e:
                logging.warn(e)
                return None

    def _parse_url_path(self, url_path):
        url_path = re.sub("/{2,}", "/", url_path, count=1)
        if os.path.sep != "/":
            url_path = url_path.replace("/", os.path.sep)
        return url_path


def command_line_options():
    tornado.options.parse_command_line()

    if options.dir is None:
        tornado.options.print_help()
        return False

    if not os.path.exists(options.dir):
        print "Error: Directory: '%s' doesn't exists" % options.dir
        return False

    return True


def main():

    if not command_line_options():
        return

    app = Application()
    app.listen(options.port, options.address)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
