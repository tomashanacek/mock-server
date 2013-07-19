# -*- coding: utf-8 -*-

import os
import re
import json
import xmlrpclib

from text import markdown
from util import read_file, slugify
from model import get_url_path


class MethodsLoader(object):

    def __init__(self, api_dir, application_data):
        self.api_dir = api_dir
        self.application_data = application_data

    def load(self):
        pass


class ResourcesLoader(MethodsLoader):

    def __init__(self, api_dir, application_data, SUPPORTED_METHODS):
        super(ResourcesLoader, self).__init__(api_dir, application_data)

        self.SUPPORTED_METHODS = SUPPORTED_METHODS

    def load(self):
        paths = [self._complete_path(item)
                 for item in os.walk(self.api_dir)
                 if self._check_folder(item)]
        return paths

    def _check_folder(self, item):
        if not item[2]:
            return False

        c = re.compile(r"(%s)_\d+\..*" % ("|".join(self.SUPPORTED_METHODS)))

        for current_file in item[2]:
            if c.search(current_file):
                return True

        return False

    def _complete_path(self, item):

        c = re.compile(r"(%s)_(\d+)\.(\w+)" %
                       ("|".join(self.SUPPORTED_METHODS)))

        url_path = UrlPath(get_url_path(item[0][len(self.api_dir):]))

        for current_file in sorted(item[2]):
            m = c.match(current_file)
            if m is None:
                continue
            method, status_code, format = m.groups()

            if method in url_path.resources:
                url_path.resources[method].files.append(
                    ResourceFormatFile(
                        status_code,
                        format,
                        read_file("%s/%s" % (item[0], current_file))))
            else:
                resource = self._create_resource(
                    item[0], method, url_path.path)

                resource.files.append(
                    ResourceFormatFile(
                        status_code,
                        format,
                        read_file("%s/%s" % (item[0], current_file))))

                # add resource to url_path
                url_path.resources[method] = resource

        return url_path

    def _create_resource(self, file_path, method, url_path):
        resource = Resource(method, url_path)

        # resource description
        resource_description_path = os.path.join(
            file_path, "%s_doc.md" % method)
        resource_description = read_file(resource_description_path)

        if resource_description:
            resource.description = resource_description

        # upstream server
        resource.upstream_server = \
            self.application_data.get_upstream_server(
                "%s-%s" % (method, file_path[len(self.api_dir):]))

        return resource


class UrlPath(object):

    def __init__(self, path):
        self.path = path
        self.id = slugify(self.path)
        self.resources = {}


class Resource(object):

    def __init__(self, method, url_path):
        self.method = method
        self.url_path = url_path

        self.id = "%s-%s" % (self.method, self.url_path)

        self.files = []
        self.upstream_server = False
        self._description = ""
        self.plain_description = ""

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self.plain_description = value
        self._description = markdown(value, protocol="rest", ref_id=self.id)


class ResourceFormatFile(object):

    def __init__(self, status_code, format, data):
        self.status_code = status_code
        self.format = format
        self.data = data


class RPCMethodsLoader(MethodsLoader):

    def __init__(self, api_dir, application_data, jsonrpc):
        super(RPCMethodsLoader, self).__init__(api_dir, application_data)

        self.jsonrpc = jsonrpc

    def load(self, path):
        rpc_methods = []
        methods_dir = os.path.join(self.api_dir, path)

        if not os.path.exists(methods_dir):
            return rpc_methods

        for method in os.listdir(methods_dir):

            if method.startswith(".") or method.endswith("_doc.md"):
                continue

            # load data
            data = read_file(os.path.join(methods_dir, method))
            responses = self._load_responses(method, data)

            # load description
            description_path = os.path.join(
                methods_dir, "%s_doc.md" % method)
            description = read_file(description_path)
            if description:
                description = markdown(
                    description, protocol="rpc", ref_id=method)

            # upstream server
            upstream_server = self.application_data.get_rpc_upstream_server(
                method)

            rpc_methods.append({
                "name": method,
                "id": method.replace(".", ""),
                "responses": responses,
                "description": description,
                "upstream_server": upstream_server
            })

        return rpc_methods

    def _load_responses(self, method, data):
        try:
            data = json.loads(data)
        except ValueError:
            data = data

        responses = {}

        responses["xmlrpc"] = XMLRPCMethod(method, data)

        if self.jsonrpc:
            responses["jsonrpc"] = JSONRPCMethod(method, data)

        return responses


class RPCMethod(object):

    CONTENT_TYPE = ""

    def __init__(self, method, data, method_call):
        self.method = method
        self.data = data
        self.method_call = method_call


class XMLRPCMethod(RPCMethod):

    CONTENT_TYPE = "text/xml"

    def __init__(self, method, data):
        data = xmlrpclib.dumps((data, ), methodresponse=True)
        method_call = "\"<?xml version='1.0'?><methodCall>"\
                      "<methodName>%s</methodName>"\
                      "<params></params></methodCall>\"" % method
        super(XMLRPCMethod, self).__init__(method, data, method_call)


class JSONRPCMethod(RPCMethod):

    CONTENT_TYPE = "application/json"

    def __init__(self, method, data):
        import jsonrpclib

        data = jsonrpclib.dumps(data, methodresponse=True, rpcid=1)
        method_call = '\'{"method": "%s", "id": 1}\'' % method

        super(JSONRPCMethod, self).__init__(method, data, method_call)
