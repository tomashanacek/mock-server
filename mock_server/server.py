# -*- coding: utf-8 -*-

import os
import re
import datetime

import tornado.web
import tornado.httpclient

from data import SUPPORTED_FORMATS, SUPPORTED_MIMES, DEFAULT_FORMAT
from tornado_flash_message_mixin import FlashMessageMixin
from model import ApplicationData, ResourceMethod, RPCMethod

from methodslisting import ResourcesLoader, RPCMethodsLoader
from validators import validate_url

import model
import rest
import xmlrpc

try:
    import jsonrpc
    jsonrpc_available = True
except ImportError:
    jsonrpc_available = False


class Application(tornado.web.Application):
    def __init__(self, port, address, api_dir, debug, application_data):

        self.data = ApplicationData(os.path.join(api_dir, application_data))
        self.data.load()

        supported_formats = "|".join(
            map(lambda x: ".%s" % x, SUPPORTED_FORMATS.keys()))
        handlers = [
            (r"/__manage/resource/(.*)", ResourceMethodHandler),
            (r"/__manage/rpc/(.*)", RPCMethodHandler),
            (r"/__manage/upstream-server", UpstreamServerHandler),
            (r"/__manage/logs", ResourcesLogsHandler),
            (r"/__manage/create/rpc", CreateRPCMethodHandler),
            (r"/__manage/create", CreateResourceMethodHandler),
            (r"/__manage", ListResourcesHandler),
            (r"/%s" % RPCHandler.PATH, RPCHandler),
            (r"/(.*)(%s)" % supported_formats, MainHandler),
            (r"/(.*)", MainHandler),
        ]
        settings = dict(
            debug=debug,
            port=port,
            address=address,
            dir=api_dir,
            jsonrpc=jsonrpc_available,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            static_url_prefix="/__static/",
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        )
        super(Application, self).__init__(handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):

    def set_content_type(self, content_type, charset="utf-8"):
        self.set_header("Content-Type",
                        "%s; charset=%s" % (content_type, charset))

    def set_headers(self, headers):
        if not headers:
            return
        for name, value in headers:
            self.set_header(name, value)

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

        model.add_to_resources_log(self.log_request_name, data)

    @property
    def log_request_name(self):
        return os.path.join(
            self.settings["dir"], "access-%s.log" %
            datetime.datetime.now().strftime("%Y-%m-%d"))


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
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Max-Age", 21600)

        if "Access-Control-Request-Headers" in self.request.headers:
            self.set_header(
                "Access-Control-Allow-Headers",
                self.request.headers["Access-Control-Request-Headers"])
        else:
            headers = ', '.join(x.upper() for x in self.request.headers)
            self.set_header("Access-Control-Allow-Headers", headers)

        if "Access-Control-Request-Method" in self.request.headers:
            self.set_header(
                "Access-Control-Allow-Methods",
                "OPTIONS, %s" %
                self.request.headers["Access-Control-Request-Method"])

        self.write("")
        self.finish()

    def _handle_request_on_upstream(self):
        if self.request.method in ("POST", "PATCH", "PUT"):
            body = self.request.body
        else:
            body = None

        http = tornado.httpclient.AsyncHTTPClient()
        http.fetch("%s%s" % (self.application.data.upstream_server,
                             self.request.uri),
                   callback=self.on_response, method=self.request.method,
                   body=body, headers=self.request.headers,
                   follow_redirects=True)

    def on_response(self, response):
        if response.error:
            return self._default_response(
                self.request.path, self.request.method,
                self.status_code, self.format)

        for key, value in response.headers.iteritems():
            self.set_header(key, value)

        self.write(response.body)
        self.finish()

    def _resolve_request(self, url_path, format):
        # log request
        self.log_request()
        self.set_header("Access-Control-Allow-Origin", "*")

        # get request data
        self.format = self._get_format(format)
        method = self.request.method
        self.status_code = int(self.get_argument("__statusCode", 200))

        # upstream server
        upstream_server = self.application.data.get_upstream_server(
            "%s-%s-%s" % (method, self.status_code, url_path))

        if self.application.data.upstream_server and upstream_server:
            return self._handle_request_on_upstream()

        # mock
        provider = rest.FilesMockProvider(self.settings["dir"])

        response = rest.resolve_request(
            provider, method, url_path, self.status_code, self.format)

        if provider.error:
            if self.application.data.upstream_server:
                return self._handle_request_on_upstream()

        # response
        self.set_status(response.status_code)
        self.set_content_type(SUPPORTED_FORMATS[self.format][0])
        self.set_headers(response.headers)

        self.write(response.content)
        self.finish()

    def _default_response(self, url_path, method, status_code, format):
        self.set_status(404)
        self.render("api_not_exists.html", url_path=url_path, method=method,
                    status_code=status_code, format=format)

    def _get_format(self, format):
        format = format[1:] if format[0] == "." else format

        if "Accept" in self.request.headers and\
                self.request.headers["Accept"] in SUPPORTED_MIMES:
            format = SUPPORTED_MIMES[self.request.headers["Accept"]]

        return format


class RPCHandler(BaseHandler):
    PATH = "RPC2"
    PARSE_ERROR = (-32700, "parse_error")

    @tornado.web.asynchronous
    def post(self):
        # log request
        self.log_request()
        self.set_header("Access-Control-Allow-Origin", "*")

        # get content type
        if "Content-Type" in self.request.headers and \
                self.settings["jsonrpc"] and \
                self.request.headers["Content-Type"] == "application/json":
            self.content_type = "application/json"
            self.rpclib = jsonrpc
        else:
            self.content_type = "text/xml"
            self.rpclib = xmlrpc

        self.process()

    def _handle_request_on_upstream(self):
        http = tornado.httpclient.AsyncHTTPClient()
        headers = self.request.headers
        headers["Accept"] = self.content_type

        http.fetch("%s%s" % (self.application.data.upstream_server,
                             self.request.uri),
                   callback=self.on_response, method=self.request.method,
                   body=self.request.body, headers=headers,
                   follow_redirects=True)

    def on_response(self, response):
        if response.error:
            self.write(
                self.rpclib.dumps(
                    self.rpclib.Fault(*RPCHandler.PARSE_ERROR),
                    methodresponse=True))
            return self.finish()

        for key, value in response.headers.iteritems():
            self.set_header(key, value)

        self.write(response.body)
        self.finish()

    def process(self):
        method_name = self.rpclib.FilesMockProvider.get_method_name(
            self.request.body)

        # upstream server
        upstream_server = self.application.data.get_upstream_server(
            "RPC-%s" % method_name)

        if self.application.data.upstream_server and upstream_server:
            return self._handle_request_on_upstream()

        # mock
        provider = self.rpclib.FilesMockProvider(self.settings["dir"])
        response = provider(method_name=method_name)

        if provider.error and self.application.data.upstream_server:
            return self._handle_request_on_upstream()

        self.set_headers(response.headers)

        self.write(response.content)
        self.finish()


class ResourcesLogsHandler(BaseHandler):
    def get(self):
        self.render("resources_logs.html",
                    data=model.load_resources_log(self.log_request_name))


class ListResourcesHandler(BaseHandler, FlashMessageMixin):
    def get(self):
        # load categories
        categories, methods_with_category = \
            self.application.data.list_categories()

        # load resources
        resources_loader = ResourcesLoader(
            self.settings["dir"], self.application.data,
            self.SUPPORTED_METHODS)
        paths = resources_loader.load()

        # load rpc methods
        rpc_methods_loader = RPCMethodsLoader(
            self.settings["dir"], self.application.data,
            self.settings["jsonrpc"])
        rpc_methods = rpc_methods_loader.load(RPCHandler.PATH)

        # add resources to category
        for path in paths:
            for resource in path.resources.itervalues():
                if resource.id in methods_with_category:
                    category = methods_with_category[resource.id]["category"]
                else:
                    category = "__default"

                if path not in categories[category]:
                    categories[category].append(("rest", path))
                    break

        # add rpc methods to category
        for method in rpc_methods:
            name = "RPC-%s" % method["name"]
            if name in methods_with_category:
                category = methods_with_category[name]["category"]
            else:
                category = "__default"

            categories[category].append(("rpc", method))

        # render to response
        self.render("list_resources.html", categories=categories,
                    application_data=self.application.data,
                    number_of_methods=len(methods_with_category),
                    some_method=bool(paths or rpc_methods),
                    flash_messages=self.get_flash_messages(
                        ("success", "error")))


class CreateResourceMethodHandler(BaseHandler, FlashMessageMixin):
    def get(self):
        url_path = self.get_argument("url_path", "")
        method = self.get_argument("method", "GET")
        status_code = self.get_argument("status_code", 200)
        format = self.get_argument("format", DEFAULT_FORMAT)

        method_file = ResourceMethod(
            self.settings["dir"], url_path, method, status_code)
        method_file.load_format(format)
        method_file.load_description()

        category = self.application.data.get_category(
            method_file.id)

        self.render(
            "create_resource.html",
            protocol="rest", category=category, method_file=method_file,
            SUPPORTED_FORMATS=SUPPORTED_FORMATS.keys(),
            jsonrpc=self.settings["jsonrpc"])

    def post(self):
        self.check_xsrf_cookie()

        url_path = self.get_argument("url_path")
        method = self.get_argument("method")
        status_code = self.get_argument("status_code")
        format = self.get_argument("format")
        response_body = self.get_argument("response_body")
        response_headers = self.get_argument("response_headers", "")
        category = self.get_argument("category", "")
        resource_description = self.get_argument("resource_description", "")

        # save resource
        method_file = ResourceMethod(
            self.settings["dir"], url_path, method, status_code)
        method_file.description = resource_description
        method_file.add_format(format, response_body, response_headers)
        method_file.save()

        # add resource to category
        self.application.data.save_category(method_file.id, category)

        self.set_flash_message(
            "success",
            "Resource '%s' has been successfully created." % url_path)
        self.redirect("/__manage")


class CreateRPCMethodHandler(BaseHandler, FlashMessageMixin):
    def get(self):
        method_name = self.get_argument("method_name", "")

        method_file = RPCMethod(
            os.path.join(self.settings["dir"], RPCHandler.PATH))
        method_file.load(method_name)
        method_file.load_description()

        category = self.application.data.get_category(
            "RPC-%s" % method_name)

        self.render(
            "create_resource.html",
            protocol="rpc", category=category, method_file=method_file,
            SUPPORTED_FORMATS=SUPPORTED_FORMATS.keys(),
            jsonrpc=self.settings["jsonrpc"])

    def post(self):

        self.check_xsrf_cookie()

        method_name = self.get_argument("method_name")
        method_response = self.get_argument("method_response")
        category = self.get_argument("category", "")
        description = self.get_argument("description", "")

        # save method
        rpc_file = RPCMethod(
            os.path.join(self.settings["dir"], RPCHandler.PATH))
        rpc_file.description = description
        rpc_file.save(method_name, method_response)

        # add method to category
        self.application.data.save_category(
            "RPC-%s" % method_name, category)

        self.set_flash_message(
            "success",
            "RPC method '%s' has been successfully created." % method_name)
        self.redirect("/__manage")


class UpstreamServerHandler(BaseHandler, FlashMessageMixin):
    def post(self):
        self.check_xsrf_cookie()

        upstream_server = self.get_argument("upstream_server", "")

        if upstream_server and not validate_url(upstream_server):
            self.set_flash_message(
                "error",
                "Url is not valid.")
            return self.redirect("/__manage")

        self.application.data.upstream_server = upstream_server
        self.application.data.save()

        self.set_flash_message(
            "success",
            "Upstream server has been successfully saved.")
        self.redirect("/__manage")


class ResourceMethodHandler(BaseHandler, FlashMessageMixin):
    def get(self, resource):
        _method = self.get_argument("_method", "get")
        if _method == "delete":
            return self.delete(resource)

        raise tornado.web.HTTPError(405)

    def post(self, resource):
        self.check_xsrf_cookie()

        upstream_server = bool(self.get_argument("upstream_server", None))

        self.application.data.save_method_upstream_server(
            resource, upstream_server)

        self.set_flash_message(
            "success",
            "Upstream server for resource method has been successfully %s." %
            ("active" if upstream_server else "deactivate"))

        self.redirect("/__manage")

    def delete(self, resource):
        # get http method, status and url path
        c = re.compile(r"(%s)-(\d+)-(.+)" %
                       ("|".join(self.SUPPORTED_METHODS)))
        m = c.match(resource)
        method, status_code, url_path = m.groups()

        # delete resource method
        method_file = ResourceMethod(
            self.settings["dir"], url_path, method, status_code)
        method_file.delete()

        self.application.data.delete_resource(resource)

        # redirect
        self.set_flash_message(
            "success",
            "Resource method has been successfully deleted.")

        self.redirect("/__manage")


class RPCMethodHandler(BaseHandler, FlashMessageMixin):
    def get(self, method_name):
        _method = self.get_argument("_method", "get")
        if _method == "delete":
            return self.delete(method_name)

        raise tornado.web.HTTPError(405)

    def post(self, method_name):
        self.check_xsrf_cookie()

        upstream_server = bool(self.get_argument("upstream_server", None))

        self.application.data.save_method_upstream_server(
            "RPC-%s" % method_name, upstream_server)

        self.set_flash_message(
            "success",
            "Upstream server for RPC method has been successfully %s." %
            ("active" if upstream_server else "deactivate"))

        self.redirect("/__manage")

    def delete(self, method_name):
        rpc_file = RPCMethod(
            os.path.join(self.settings["dir"], RPCHandler.PATH))
        rpc_file.delete(method_name)

        self.application.data.delete_resource("RPC-%s" % method_name)

        self.set_flash_message(
            "success",
            "RPC method has been successfully deleted.")

        self.redirect("/__manage")
