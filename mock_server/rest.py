# -*- coding: utf-8 -*-

import os
import re
import api
import util
from email.parser import Parser


class FilesMockProvider(api.FilesMockProvider):

    def __call__(self, request, status_code=200, format="json"):

        self._request = request
        self._status_code = status_code
        self._format = format

        # prepare response
        response = api.Response()

        # get paths
        paths = self._get_path(self._get_filename())

        if not paths:
            return self._error(response)

        content_path, file_url_path = paths

        headers_path = os.path.join(file_url_path, self._get_header_filename())

        content = self._get_content(content_path)

        if content is None:
            return self._error(response)

        response.status_code = status_code
        response.content = content
        response.headers = self._get_headers(headers_path)

        return response

    def _error(self, response, status_code=404):
        self.error = 1

        response.content = \
            'Api does\'t exists, <a href="/__manage/create?url_path=%s&'\
            'method=%s&status_code=%d&format=%s">create resource method</a>' %\
            (self._request.url_path, self._request.method,
             self._status_code, self._format)
        response.status_code = status_code

        return response

    def _get_content(self, content_path):
        return util.read_file(content_path)

    def _get_headers(self, headers_path):
        headers = []

        if not os.path.isfile(headers_path):
            return headers

        try:
            with open(headers_path) as f:
                strip = lambda s: s if len(s) == 0 \
                    else s[0] + s[1:].strip()
                return Parser().parsestr(
                    "\r\n".join(map(strip, f.readlines()))).items()
        except IOError:
            return headers

    def _get_filename(self):
        return "%s_%s.%s" % (self._request.method,
                             self._status_code, self._format)

    def _get_header_filename(self):
        return "%s_H_%s.%s" % (self._request.method,
                               self._status_code, self._format)

    def _get_path(self, filename):
        url_path = re.sub("/{2,}", "/", self._request.url_path, count=1)

        content_path = os.path.join(self._api_dir, url_path, filename)

        if os.path.isfile(content_path):
            return content_path, os.path.join(self._api_dir, url_path)

        if url_path.endswith("/"):
            url_path = url_path[:-1]

        if "/" not in url_path:
            return None

        path_regex = []
        for item in url_path.split("/"):
            path_regex.append("(%s|__[^\/]*)" % item)
        c = re.compile("%s%s" % (self._api_dir, "/".join(path_regex)))

        for path in os.walk(self._api_dir):
            m = c.match(path[0])
            if m:
                return os.path.join(path[0], filename), path[0]

        return None


def get_desired_response(provider, request, status_code=200, format="json"):
    resposne = provider(request, status_code, format)
    return resposne


def resolve_request(provider, method, url_path,
                    status_code=200, format="json"):

    return get_desired_response(
        provider, api.Request(method, url_path), status_code, format)


if __name__ == "__main__":

    provider = FilesMockProvider("/Users/tomashanacek/Downloads/api")

    print resolve_request(provider, "post", "/ble")
    print resolve_request(provider, "get", "/user/tomas/family/marek")

    print resolve_request(provider, "get", "/user/dsfsd")
    print resolve_request(provider, "get", "/dsf")
