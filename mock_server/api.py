# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod


class FilesMockProvider:

    __metaclass__ = ABCMeta

    def __init__(self, api_dir):
        self._api_dir = api_dir
        self.error = 0

    @abstractmethod
    def __call__(self, *args, **kwargs):
        """
        :returns: Response
        """
        pass


class Request(object):
    def __init__(self, method="GET", url_path="", body=""):
        self.method = method
        self.url_path = url_path
        self.body = body


class Response(object):
    def __init__(self, content="", headers=None, status_code=200):
        self.content = content
        if headers is None:
            headers = []

        self.headers = headers
        self.status_code = status_code

    def __str__(self):
        return "Response(content='%s', headers=%s, status_code=%s)" % \
               (self.content, self.headers, self.status_code)


class UpstreamServerProvider:

    __metaclass__ = ABCMeta

    def __init__(self, upstream_server):
        self.upstream_server = upstream_server

    @abstractmethod
    def __call__(self, data, request_handler_callback):
        """
        :returns Response
        """
        pass
