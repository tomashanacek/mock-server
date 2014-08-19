# -*- coding: utf-8 -*-

import os
import re
import bcrypt
import datetime
import tornado.web

from crypt import crypt
from tornado import gen
from data import SUPPORTED_FORMATS, SUPPORTED_MIMES, DEFAULT_FORMAT
from data import SUPPORTED_METHODS
from tornado_flash_message_mixin import FlashMessageMixin
from tornado_http_auth_basic_mixin import HttpAuthBasicMixin
from model import ResourceMethod, RPCMethod, gencryptsalt

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

try:
    import fastrpcapi
    fastrpc_available = True
except ImportError:
    fastrpc_available = False


class BaseHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        if self.api_data.password:
            return self.get_secure_cookie("user")
        else:
            return "Password is not required"

    def prepare(self):
        api_settings = self.application.api_settings_class(
            self.settings, self.request)

        self.api_dir = api_settings.api_dir
        self.api_data = api_settings.api_data

    def set_headers(self, headers):
        if not headers:
            return
        for name, value in headers:
            self.set_header(name, value)

    def log_request(self, response=None):
        data = {
            "method": self.request.method,
            "uri": self.request.uri,
            "url_path": self.request.path,
            "status": self.get_status(),
            "remote_ip": self.request.remote_ip,
            "request_time": 1000.0 * self.request.request_time(),
            "headers": self.request.headers,
            "body": unicode(self.request.body),
            "time": datetime.datetime.now().isoformat()
        }

        if response is not None:
            data["response"] = response

        model.add_to_resources_log(self.log_request_name, data)

    @property
    def log_request_name(self):
        return os.path.join(
            self.api_dir, "access-%s.log" %
            datetime.datetime.now().strftime("%Y-%m-%d"))

    def _upstream_server_callback(self, response):
        self.set_headers(response.headers)
        self.write(response.content)
        self.set_status(response.status_code)
        self.finish()


class MainHandler(BaseHandler, HttpAuthBasicMixin):

    def check_auth(self, http_username, http_password):
        username = self.api_data.http_username
        password = self.api_data.http_password

        if username:
            return (username == http_username and
                    password == crypt(http_password, password))

        return True

    def authorize(self):
        credentials = self.authorization()

        if not credentials or not self.check_auth(*credentials):
            self.authenticate()

    def prepare(self):
        super(MainHandler, self).prepare()

        if self.api_data.http_username:
            self.authorize()

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
            headers = ", ".join(x.upper() for x in self.request.headers)
            self.set_header("Access-Control-Allow-Headers", headers)

        if "Access-Control-Request-Method" in self.request.headers:
            self.set_header(
                "Access-Control-Allow-Methods",
                "OPTIONS, %s" %
                self.request.headers["Access-Control-Request-Method"])

        self.write("")
        self.finish()

    def _handle_request_on_upstream(self):
        provider = rest.UpstreamServerProvider(
            self.api_data.upstream_server)

        provider({
            "uri": self.request.uri,
            "method": self.request.method,
            "body": self.request.body,
            "headers": self.request.headers,
            "status_code": self.status_code,
            "format": self.format
        }, self._upstream_server_callback)

    def _resolve_request(self, url_path, format):
        # get request data
        self.format = self._get_format(format)
        method = self.request.method
        self.status_code = int(self.get_argument("__statusCode", 200))

        # upstream server
        upstream_server = self.api_data.get_upstream_server(
            "%s-%s" % (method, url_path))

        if self.api_data.upstream_server and upstream_server:
            return self._handle_request_on_upstream()

        # mock
        provider = rest.FilesMockProvider(self.api_dir)

        response = rest.resolve_request(
            provider, method, url_path, self.status_code, self.format)

        if provider.error:
            if self.api_data.upstream_server:
                return self._handle_request_on_upstream()

        # set content type
        already_content_type = [
            item[0] for item in response.headers
            if item[0] == 'Content-Type']
        if not already_content_type:
            content_type = SUPPORTED_FORMATS[self.format][0]
            response.headers.append(
                ("Content-Type", "%s; charset=utf-8" % content_type))
        response.headers.append(
            ("Access-Control-Allow-Origin", "*"))

        # log request
        self.log_request(response)

        # response
        try:
            self.set_status(response.status_code)
        except ValueError:
            self._reason = 'Custom status code'

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

        if not "Content-Length" in self.request.headers and \
                self.request.headers.get(
                    "Transfer-Encoding", None) == "chunked":
            self.chunks = ""
            self._stream = self.request.connection.stream
            self._stream.read_until("\r\n", self._on_chunk_length)
        else:
            self._resolve_rpclib()
            self._process(self.request.body)

    def _on_chunks(self, all_chunks):
        self._resolve_rpclib()
        self._process(all_chunks)

    def _on_chunk_length(self, data):
        assert data[-2:] == "\r\n", "chunk size ends with CRLF"
        chunk_length = int(data[:-2], 16)

        if chunk_length:
            self._stream.read_bytes(chunk_length + 2, self._on_chunk_data)
        else:
            self._on_chunks(self.chunks)

    def _on_chunk_data(self, data):
        assert data[-2:] == "\r\n", "chunk data ends with CRLF"
        self.chunks += data[:-2]

        self._stream.read_until("\r\n", self._on_chunk_length)

    def _is_jsonrpc(self, content_type):
        if jsonrpc_available and content_type == "application/json":
            return True
        else:
            return False

    def _is_fastrpc(self, content_type):
        if fastrpc_available and content_type == "application/x-frpc":
            return True
        else:
            return False

    def _resolve_rpclib(self):
        if "Content-Type" in self.request.headers:
            if self._is_jsonrpc(self.request.headers["Content-Type"]):
                self.content_type = "application/json"
                self.rpclib = jsonrpc
            elif self._is_fastrpc(self.request.headers["Content-Type"]):
                self.rpclib = fastrpcapi
                self.content_type = "application/x-frpc"
            else:
                self.content_type = "text/xml"
                self.rpclib = xmlrpc
        else:
            self.content_type = "text/xml"
            self.rpclib = xmlrpc

    def _handle_request_on_upstream(self, request_data):
        provider = self.rpclib.UpstreamServerProvider(
            self.api_data.upstream_server)

        if isinstance(provider, fastrpcapi.UpstreamServerProvider):
            provider(request_data, self._upstream_server_callback)
        else:
            headers = self.request.headers
            headers["Accept"] = self.content_type

            provider({
                "uri": self.request.uri,
                "method": self.request.method,
                "body": request_data,
                "headers": headers
            }, self._upstream_server_callback)

    def _process(self, request_data):
        method_name = self.rpclib.FilesMockProvider.get_method_name(
            request_data)
        self.method_name = method_name

        # upstream server
        upstream_server = self.api_data.get_rpc_upstream_server(
            method_name)

        if self.api_data.upstream_server and upstream_server:
            return self._handle_request_on_upstream(request_data)

        # mock
        provider = self.rpclib.FilesMockProvider(self.api_dir)
        response = provider(method_name=method_name)

        if provider.error and self.api_data.upstream_server:
            return self._handle_request_on_upstream(request_data)

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
            self.api_data.list_categories()

        # load resources
        resources_loader = ResourcesLoader(
            self.api_dir, self.api_data,
            SUPPORTED_METHODS)
        paths = resources_loader.load()

        # load rpc methods
        rpc_methods_loader = RPCMethodsLoader(
            self.api_dir, self.api_data,
            jsonrpc_available)
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
                    number_of_methods=len(methods_with_category),
                    some_method=bool(paths or rpc_methods),
                    flash_messages=self.get_flash_messages(
                        ("success", "error")))


class CreateResourceMethodHandler(BaseHandler, FlashMessageMixin):

    @tornado.web.authenticated
    def get(self, flash_messages=None):
        url_path = self.get_argument("url_path", "")
        method = self.get_argument("method", None)

        method_file = ResourceMethod(
            self.api_dir, url_path, method)
        method_file.load_responses()
        method_file.load_description()

        if method is None:
            category = ""
        else:
            category = self.api_data.get_category(method_file.id)

        self.render(
            "create_resource.html",
            protocol="rest", category=category, method_file=method_file,
            SUPPORTED_FORMATS=SUPPORTED_FORMATS.keys(),
            jsonrpc=jsonrpc_available,
            flash_messages=flash_messages)

    @tornado.web.authenticated
    def post(self):
        # check xsrf cookie
        self.check_xsrf_cookie()

        # get data from request body
        data = tornado.escape.json_decode(self.request.body)

        # save resource
        for response in data["responses"]:
            # save resource
            method_file = ResourceMethod(
                self.api_dir, data["url_path"], data["method"])
            method_file.description = data["description"]
            method_file.add_response(
                response["status_code"], response["format"],
                response["body"], response["headers"])
            method_file.save()

            # add resource to category
            self.api_data.save_category(
                method_file.id, data["category"])

        self.set_flash_message(
            "success",
            "Resource '%s' has been successfully created." % data["url_path"])
        self.set_header("Content-Type", "application/json")
        self.write("OK")


class CreateRPCMethodHandler(BaseHandler, FlashMessageMixin):

    @tornado.web.authenticated
    def get(self, flash_messages=None):
        method_name = self.get_argument("method_name", "")

        method_file = RPCMethod(
            os.path.join(self.api_dir, RPCHandler.PATH), method_name)
        method_file.load()
        method_file.load_description()

        category = self.api_data.get_rpc_category(method_name)

        self.render(
            "create_resource.html",
            protocol="rpc", category=category, method_file=method_file,
            SUPPORTED_FORMATS=SUPPORTED_FORMATS.keys(),
            jsonrpc=jsonrpc_available,
            flash_messages=flash_messages)

    @tornado.web.authenticated
    def post(self):
        # check xsrf cookie
        self.check_xsrf_cookie()

        # get data from request
        method_name = self.get_argument("method_name")
        method_response = self.get_argument("method_response")
        category = self.get_argument("category", "")
        description = self.get_argument("description", "")

        # save method
        rpc_file = RPCMethod(
            os.path.join(self.api_dir, RPCHandler.PATH), method_name)
        rpc_file.description = description
        rpc_file.save(method_response)

        # add method to category
        self.api_data.save_category(
            "RPC-%s" % method_name, category)

        self.set_flash_message(
            "success",
            "RPC method '%s' has been successfully created." % method_name)
        self.redirect("/__manage")


class ResourceMethodHandler(BaseHandler, FlashMessageMixin):

    @tornado.web.authenticated
    def get(self, resource):
        _method = self.get_argument("_method", "get")
        if _method == "delete":
            return self.delete(resource)

        raise tornado.web.HTTPError(405)

    @tornado.web.authenticated
    def post(self, resource):
        self.check_xsrf_cookie()

        upstream_server = bool(self.get_argument("upstream_server", None))

        self.api_data.save_method_upstream_server(
            resource, upstream_server)

        self.set_flash_message(
            "success",
            "Upstream server for resource method has been successfully %s." %
            ("active" if upstream_server else "deactivate"))

        self.redirect("/__manage")

    @tornado.web.authenticated
    def delete(self, resource):
        # get http method, status and url path
        c = re.compile(r"(%s)-(.*)" %
                       ("|".join(SUPPORTED_METHODS)))
        m = c.match(resource)
        method, url_path = m.groups()

        # delete resource method
        method_file = ResourceMethod(self.api_dir, url_path, method)
        method_file.delete()

        self.api_data.delete_resource(resource)

        # redirect
        self.set_flash_message(
            "success",
            "Resource method has been successfully deleted.")

        self.redirect("/__manage")


class RPCMethodHandler(BaseHandler, FlashMessageMixin):

    @tornado.web.authenticated
    def get(self, method_name):
        _method = self.get_argument("_method", "get")
        if _method == "delete":
            return self.delete(method_name)

        raise tornado.web.HTTPError(405)

    @tornado.web.authenticated
    def post(self, method_name):
        self.check_xsrf_cookie()

        upstream_server = bool(self.get_argument("upstream_server", None))

        self.api_data.save_method_upstream_server(
            "RPC-%s" % method_name, upstream_server)

        self.set_flash_message(
            "success",
            "Upstream server for RPC method has been successfully %s." %
            ("active" if upstream_server else "deactivate"))

        self.redirect("/__manage")

    @tornado.web.authenticated
    def delete(self, method_name):
        rpc_file = RPCMethod(
            os.path.join(self.api_dir, RPCHandler.PATH), method_name)
        rpc_file.delete()

        self.api_data.delete_resource("RPC-%s" % method_name)

        self.set_flash_message(
            "success",
            "RPC method has been successfully deleted.")

        self.redirect("/__manage")


class LoginHandler(BaseHandler, FlashMessageMixin):
    def get(self):
        self.render("login.html",
                    flash_messages=self.get_flash_messages(
                        ("success", "error")))

    @gen.coroutine
    def post(self):
        self.check_xsrf_cookie()

        password = self.get_argument("password")

        password_hash = yield self.application.pool.submit(
            bcrypt.hashpw, password, self.api_data.password)

        if password_hash == self.api_data.password:
            self.set_secure_cookie("user", self.api_dir)
            self.redirect(self.get_argument("next", "/__manage"))
        else:
            self.set_flash_message("error", "Password is not valid.")
            self.redirect("/__manage/login?next=%s" %
                          self.get_argument("next", "/__manage"))


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", "/"))


class SettingsHandler(BaseHandler, FlashMessageMixin):

    @tornado.web.authenticated
    def get(self):
        self.render("settings.html",
                    flash_messages=self.get_flash_messages(
                        ("success", "error")))

    @tornado.web.authenticated
    @gen.coroutine
    def post(self):
        self.check_xsrf_cookie()

        upstream_server = self.get_argument("upstream_server", "")
        password = self.get_argument("password", "")
        http_username = self.get_argument("http_username", "")
        http_password = self.get_argument("http_password", "")

        if upstream_server and not validate_url(upstream_server):
            self.set_flash_message(
                "error",
                "Url is not valid.")
            self.redirect("/__manage")
        else:
            self.api_data.upstream_server = upstream_server
            self.api_data.http_username = http_username

            if password:
                password_hash = yield self.application.pool.submit(
                    bcrypt.hashpw, password, bcrypt.gensalt())

                self.api_data.password = password_hash

            if not http_username:
                self.api_data.http_password = ""
            elif http_password:
                http_password_hash = yield self.application.pool.submit(
                    crypt, http_password, gencryptsalt())

                self.api_data.http_password = http_password_hash

            self.api_data.save()

            self.set_flash_message(
                "success",
                "Settings has been successfully saved.")
            self.redirect("/__manage/settings")


class TodoHandler(BaseHandler):

    @tornado.web.authenticated
    def post(self):
        # check xsrf cookie
        self.check_xsrf_cookie()

        # get data from request body
        data = tornado.escape.json_decode(self.request.body)

        if data["protocol"] == "rest":
            method, url_path = data["id"].split("-")
            method_file = ResourceMethod(self.api_dir, url_path, method)
        elif data["protocol"] == "rpc":
            method_file = RPCMethod(
                os.path.join(self.api_dir, RPCHandler.PATH), data["id"])

        # load description
        method_file.load_description()

        # set todo
        value = " %s" % data["value"].strip()
        todo = "%s%s" % ("[x]" if data["checked"] else "[ ]", value)
        method_file.description = re.sub(
            r"\[( |x)\]%s" % re.escape(value), todo, method_file.description)

        # save description
        method_file.save_description()

        self.set_header("Content-Type", "application/json")
        self.write("OK")
