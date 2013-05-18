# -*- coding: utf-8 -*-

import os
import json
import util
import api
import tornado.httpclient

from abc import abstractmethod


class FilesMockProvider(api.FilesMockProvider):

    PATH = "RPC2"
    LIST_METHODS = "system.listMethods"
    PARSE_ERROR = (-32700, "parse_error")
    METHOD_NOT_FOUND = (-32601, "method_not_found")
    CONTENT_TYPE = ("Content-Type", "text/plain")

    def __init__(self, api_dir):
        self._api_dir = api_dir
        self.error = 0

    def __call__(self, request=None, method_name=""):

        methods_dir = os.path.join(self._api_dir, self.PATH)

        if not method_name and request is not None:
            method_name = self.get_method_name(request.body)

        if not method_name:
            return self._error(self.PARSE_ERROR)

        content = self._get_content(methods_dir, method_name)

        if content:
            return self._response(content)
        else:
            return self._error(self.METHOD_NOT_FOUND)

    @abstractmethod
    def _fault(self, error):
        pass

    @abstractmethod
    def _dump(self, data, rpcid=1):
        pass

    @abstractmethod
    def get_method_name(request_body):
        """Subclasses must implement this as a @staticmethod"""
        pass

    def _error(self, error):
        self.error = error[0]
        return self._response(self._fault(error))

    def _response(self, content):
        return api.Response(self._dump(content), [self.CONTENT_TYPE])

    def _get_content(self, methods_dir, method_name):
        # list available methods
        available_methods = self._list_available_methods(methods_dir)

        if method_name == self.LIST_METHODS:
            return available_methods
        elif method_name in available_methods:
            content = util.read_file(os.path.join(
                methods_dir, method_name))
            if content is not None:
                try:
                    data = json.loads(content)
                except ValueError:
                    data = content

                return data

    def _list_available_methods(self, methods_dir):
        if os.path.isdir(methods_dir):
            available_methods = os.listdir(methods_dir)
        else:
            available_methods = []
        available_methods.append(self.LIST_METHODS)
        return available_methods


class UpstreamServerProvider(api.UpstreamServerProvider):

    def __init__(self, upstream_server):
        super(UpstreamServerProvider, self).__init__(upstream_server)

        self._http_client = None
        self._request_handler_callback = None

    @property
    def http_client(self):
        if self._http_client is None:
            self._http_client = tornado.httpclient.AsyncHTTPClient()

        return self._http_client

    def __call__(self, data, request_handler_callback):
        self._request_handler_callback = request_handler_callback

        self.http_client.fetch(
            "%s%s" % (self.upstream_server, data["uri"]),
            callback=self._on_response, method=data["method"],
            body=data["body"], headers=data["headers"], follow_redirects=True)

    def _on_response(self, response):
        self._request_handler_callback(
            api.Response(response.body, response.headers.items()))
