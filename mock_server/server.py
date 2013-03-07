#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
import xmlrpclib
import datetime
from email.parser import Parser

import tornado.web
from tornado.escape import json_encode, json_decode, utf8
from tornado.options import options

from data import SUPPORTED_FORMATS, SUPPORTED_MIMES, DEFAULT_FORMAT
from tornado_flash_message_mixin import FlashMessageMixin


class Application(tornado.web.Application):
    def __init__(self):
        supported_formats = "|".join(
            map(lambda x: ".%s" % x, SUPPORTED_FORMATS.keys()))
        handlers = [
            (r"/__manage/logs", ResourcesLogsHandler),
            (r"/__manage/create/xml-rpc", CreateXMLRPCMethodHandler),
            (r"/__manage/create", CreateResourceHandler),
            (r"/__manage", ListResourcesHandler),
            (r"/%s" % XMLRPCHandler.PATH, XMLRPCHandler),
            (r"/(.*)(%s)" % supported_formats, MainHandler),
            (r"/(.*)", MainHandler),
        ]
        settings = dict(
            debug=options.debug,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            static_url_prefix="/__static/",
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):

    def set_content_type(self, content_type, charset="utf-8"):
        self.set_header("Content-Type",
                        "%s; charset=%s" % (content_type, charset))

    def read_file(self, filename):
        if os.path.isfile(filename):
            try:
                with open(filename) as f:
                    content = f.read()
                    return content
            except IOError, e:
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

        with open(self.log_request_name, "a") as f:
            f.write("%s\n" % json.dumps(data))

    @property
    def log_request_name(self):
        return os.path.join(
            options.dir, "access-%s.log" %
            datetime.datetime.now().strftime("%Y-%m-%d"))


class MainHandler(BaseHandler):

    def head(self, path, format=DEFAULT_FORMAT):
        self._resolve_request(path, format)

    def get(self, path, format=DEFAULT_FORMAT):
        self._resolve_request(path, format)

    def post(self, path, format=DEFAULT_FORMAT):
        self._resolve_request(path, format)

    def delete(self, path, format=DEFAULT_FORMAT):
        self._resolve_request(path, format)

    def patch(self, path, format=DEFAULT_FORMAT):
        self._resolve_request(path, format)

    def put(self, path, format=DEFAULT_FORMAT):
        self._resolve_request(path, format)

    def options(self, path, format=DEFAULT_FORMAT):
        self._resolve_request(path, format)

    def _resolve_request(self, url_path, format):
        format = self._get_format(format)
        method = self.request.method
        status_code = self.get_argument("__statusCode", 200)
        url_path = self._parse_url_path(url_path)

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
        self.set_content_type(content_type)
        self.set_header("Access-Control-Allow-Origin", "*")

        headers_path = os.path.join(
            options.dir, url_path,
            "%s_H_%s.%s" % (method, status_code, format))
        self._set_headers(self._get_headers(headers_path))

        # log request
        self.log_request()

        # write to response
        self.write(content)

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
                with open(filename) as f:
                    strip = lambda s: s if len(s) == 0 \
                        else s[0] + s[1:].strip()
                    headers = "\r\n".join(map(strip, f.readlines()))
                    return Parser().parsestr(headers).items()
            except IOError, e:
                return None

    def _parse_url_path(self, url_path):
        url_path = re.sub("/{2,}", "/", url_path, count=1)
        if os.path.sep != "/":
            url_path = url_path.replace("/", os.path.sep)
        return url_path


class XMLRPCHandler(BaseHandler):
    PATH = "RPC2"
    LIST_METHODS = "system.listMethods"
    PERSE_ERROR = (-32700, "parse_error")
    METHOD_NOT_FOUND = (-32601, "method_not_found")

    def post(self):

        # log request
        self.log_request()

        # get method name
        try:
            method_name = xmlrpclib.loads(self.request.body)[1]
        except:
            return self.write(
                xmlrpclib.dumps(
                    xmlrpclib.Fault(*XMLRPCHandler.PARSE_ERROR),
                    methodresponse=True))

        # list available methods
        methods_dir = os.path.join(options.dir, XMLRPCHandler.PATH)
        available_methods = os.listdir(methods_dir)
        available_methods.append(XMLRPCHandler.LIST_METHODS)

        # get response method
        params = None

        if method_name == XMLRPCHandler.LIST_METHODS:
            params = (available_methods, )
        elif method_name in available_methods:
            content = self.read_file(os.path.join(
                methods_dir, method_name))
            if content is not None:
                try:
                    data = json.loads(content)
                except ValueError:
                    data = content

                params = (data, )

        if params is None:
            params = xmlrpclib.Fault(*XMLRPCHandler.METHOD_NOT_FOUND)

        self.set_header("Content-Type", "text/xml")
        self.write(xmlrpclib.dumps(params, methodresponse=True))


class ResourcesLogsHandler(BaseHandler):
    def get(self):

        if os.path.isfile(self.log_request_name):
            with open(self.log_request_name) as f:
                data = [json.loads(line) for line in f.readlines()]
        else:
            data = []

        self.render("resources_logs.html", data=data)


class ListResourcesHandler(BaseHandler, FlashMessageMixin):
    def get(self):
        paths = [self._complete_resource(item)
                 for item in os.walk(options.dir) if self._check_folder(item)]

        xmlrpc_methods = self._list_xmlrpc_methods()

        self.render("list_resources.html", paths=paths,
                    port=options.port, address=options.address,
                    xmlrpc_methods=xmlrpc_methods,
                    flash_message=self.get_flash_message("success"))

    @classmethod
    def create_id_from_url_path(cls, url_path):
        return url_path.replace("/", "__")

    def _list_xmlrpc_methods(self):
        xmlrpc_methods = []
        methods_dir = os.path.join(options.dir, XMLRPCHandler.PATH)

        if not os.path.exists(methods_dir):
            return xmlrpc_methods

        for method in os.listdir(methods_dir):
            json_data = self._load_file(os.path.join(methods_dir, method))
            try:
                data = json.loads(json_data)
            except ValueError:
                data = json_data

            method_response = xmlrpclib.dumps(
                (data, ), methodresponse=True)
            xmlrpc_methods.append((method, method_response))

        return xmlrpc_methods

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
                     [(format, self._load_file(
                        "%s/%s" % (item[0], current_file)))]

        resource = {
            "url_path": item[0][len(options.dir):],
            "files": files
        }

        resource["id"] = self.create_id_from_url_path(resource["url_path"])

        return resource

    def _load_file(self, path):
        with open(path) as f:
            data = f.read()
            return data

    def _check_folder(self, item):
        if not item[2]:
            return False

        c = re.compile(r"(%s)_\d+\..*" % ("|".join(self.SUPPORTED_METHODS)))

        for current_file in item[2]:
            if c.search(current_file):
                return True

        return False


class CreateResourceHandler(BaseHandler, FlashMessageMixin):
    def get(self):
        protocol = self.get_argument("protocol", "rest")

        # rest
        url_path = self.get_argument("url_path", "")
        method = self.get_argument("method", "GET")
        status_code = self.get_argument("status_code", 200)
        format = self.get_argument("format", DEFAULT_FORMAT)

        # xmlrpc
        method_name = self.get_argument("method_name", "")

        if protocol == "rest":
            response_body = self.read_file(
                os.path.join(options.dir, url_path,
                             "%s_%s.%s" % (method, status_code, format)))
            response_headers = self.read_file(
                os.path.join(options.dir, url_path,
                             "%s_H_%s.%s" % (method, status_code, format)))
            method_response = None
        elif protocol == "xml-rpc":
            method_response = self.read_file(
                os.path.join(options.dir, XMLRPCHandler.PATH, method_name))
            response_body = None
            response_headers = None

        self.render(
            "create_resource.html",
            protocol=protocol, url_path=url_path, method=method,
            status_code=status_code, format=format,
            edit=True if response_body is not None else False,
            response_body=response_body,
            response_headers=response_headers,
            method_name=method_name,
            method_response=method_response,
            SUPPORTED_FORMATS=SUPPORTED_FORMATS.keys())

    def post(self):

        self.check_xsrf_cookie()

        url_path = self.get_argument("url_path")
        method = self.get_argument("method")
        status_code = self.get_argument("status_code")
        format = self.get_argument("format")
        response_body = self.get_argument("response_body")
        response_headers = self.get_argument("response_headers", "")

        resource_dir = os.path.join(options.dir, url_path)
        if not os.path.exists(resource_dir):
            os.makedirs(resource_dir)

        content_path = os.path.join(
            resource_dir, "%s_%s.%s" % (method, status_code, format))
        headers_path = os.path.join(
            resource_dir, "%s_H_%s.%s" % (method, status_code, format))

        # write content
        with open(content_path, "w") as f:
            f.write(utf8(response_body))

        # write headers
        with open(headers_path, "w") as f:
            f.write(utf8(response_headers))

        self.set_flash_message(
            "success",
            "Resource '%s' has been successfully created" % url_path)
        self.redirect("/__manage")


class CreateXMLRPCMethodHandler(BaseHandler, FlashMessageMixin):
    def post(self):

        self.check_xsrf_cookie()

        method_name = self.get_argument("method_name")
        method_response = self.get_argument("method_response")

        methods_dir = os.path.join(options.dir, XMLRPCHandler.PATH)
        if not os.path.exists(methods_dir):
            os.makedirs(methods_dir)

        method_path = os.path.join(methods_dir, method_name)

        with open(method_path, "w") as f:
            f.write(utf8(method_response))

        self.set_flash_message(
            "success",
            "XML-RPC method '%s' has been successfully created" % method_name)
        self.redirect("/__manage")
