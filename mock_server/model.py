# -*- coding: utf-8 -*-

import os
import re
import json
import glob

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from string import ascii_letters, digits
from random import choice
from tornado.escape import utf8
from util import read_file, ExtendedJSONEncoder
from data import SUPPORTED_METHODS


def gencryptsalt():
    symbols = ascii_letters + digits
    return choice(symbols) + choice(symbols)


def get_url_path(file_path):
    url_path = []

    for path in file_path.split("/"):
        url_path.append(re.sub(r"__(.*)", r"{\1}", path))

    return u"/".join(url_path)


def get_file_path(url_path):
    if url_path.startswith("/"):
        url_path = url_path[1:]

    file_path = []
    for path in url_path.split("/"):
        file_path.append(re.sub(r"{(.*)}", r"__\1", path))

    return "/".join(file_path)


class ApiData(object):

    def __init__(self, model):
        self._model = model
        self.data = {}
        self._upstream_server = ""
        self.password = ""
        self.http_username = ""
        self.http_password = ""
        self.resources = {}
        self.categories = set()

    @property
    def upstream_server(self):
        return self._upstream_server

    @upstream_server.setter
    def upstream_server(self, value):
        if value.endswith("/"):
            self._upstream_server = value[:-1]
        else:
            self._upstream_server = value

    def load(self):
        self.data = self._model.load()

        self.upstream_server = self.data.get("upstream-server", "")
        self.password = self.data.get("password", "")
        self.resources = self.data.get("resources", self.resources)
        self.http_username = self.data.get("http_username", "")
        self.http_password = self.data.get("http_password", "")

        self.load_categories()

    def load_categories(self):
        if not self.resources:
            return

        self.categories = set(resource["category"]
                              for resource in self.resources.itervalues()
                              if "category" in resource)

    def save(self):
        self.data = {}

        if self.resources:
            self.data["resources"] = self.resources
        if self.upstream_server:
            self.data["upstream-server"] = self.upstream_server
        if self.password:
            self.data["password"] = self.password
        if self.http_username:
            self.data["http_username"] = self.http_username
        if self.http_password:
            self.data["http_password"] = self.http_password

        self._model.save(self.data)

    def get_category(self, resource):
        return self._get_resource_attribute(resource, "category")

    def get_upstream_server(self, resource):
        return self._get_resource_attribute(resource, "upstream-server", False)

    def get_rpc_category(self, method_name):
        return self._get_rpc_attributes(method_name, "category")

    def get_rpc_upstream_server(self, method_name):
        return self._get_rpc_attributes(method_name, "upstream-server", False)

    def list_categories(self):
        if self.resources:
            categories = {}
            resources = {}
            for file_url_path, resource in self.resources.iteritems():
                if "category" in resource and resource["category"]:
                    categories[resource["category"]] = []
                    resources[get_url_path(file_url_path)] = resource
        else:
            categories = {}
            resources = []

        categories["__default"] = []

        def compare_category_name(x, y):
            if y[0] == "__default":
                return -1
            return cmp(x[0].lower(), y[0].lower())

        return (OrderedDict(sorted(categories.items(),
                                   cmp=compare_category_name)),
                resources)

    def save_category(self, resource, category_name):
        self._set_resource_attribute(resource, "category", category_name)
        self.categories.add(category_name)

        self.save()

    def save_method_upstream_server(self, resource, activate=True):
        self._set_resource_attribute(
            get_file_path(resource), "upstream-server", activate)

        self.save()

    def delete_resource(self, name):
        if name in self.resources:
            del self.resources[name]

        self.save()

    def _get_rpc_attributes(self, method_name, key, default=""):

        method = "RPC-%s" % method_name

        if method in self.resources and \
                key in self.resources[method]:
            return self.resources[method][key]
        else:
            return default

    def _get_resource_attribute(self, resource, key, default=""):
        # get method, status_code and url_path
        c = re.compile(r"(%s)-(.*)" %
                       ("|".join(SUPPORTED_METHODS)))
        m = c.match(resource)
        method, url_path = m.groups()

        # match resource
        path_regex = "/".join(["(%s|__[^\/]*)" % item
                               for item in url_path.split("/")])
        c = re.compile("%s-%s" % (method, path_regex))

        for resource_name, data in self.resources.items():
            m = c.match(resource_name)
            if m and key in data and m.groups()[0] != "":
                return data[key]

        return default

    def _set_resource_attribute(self, resource, key, value):
        if self.resources:
            if resource in self.resources:
                self.resources[resource][key] = value
            else:
                self.resources[resource] = {
                    key: value
                }
        else:
            self.resources = {
                resource: {
                    key: value
                }
            }


class BaseMethod(object):

    def __init__(self):
        self.description = ""
        self.edit = False

    def _delete_file(self, path):
        if os.path.exists(path):
            os.unlink(path)


class ResourceMethod(BaseMethod):

    def __init__(self, api_dir, url_path, method):
        super(ResourceMethod, self).__init__()

        self.url_path = url_path
        self.method = method

        file_url_path = get_file_path(url_path)

        self.id = "%s-%s" % (method, file_url_path)
        self.resource_dir = os.path.join(api_dir, file_url_path)

        self.responses = []

    def load_responses(self):

        c = re.compile(r"%s_(\d{3})\.(\w+)" % self.method)

        if not os.path.exists(self.resource_dir):
            return

        for item in os.listdir(self.resource_dir):
            m = c.match(item)
            if m:
                status_code, format = m.groups()

                body = read_file(
                    os.path.join(
                        self.resource_dir,
                        "%s_%s.%s" % (self.method, status_code, format)))
                headers = read_file(
                    os.path.join(
                        self.resource_dir,
                        "%s_H_%s.%s" % (self.method, status_code, format)))
                self.add_response(status_code, format, body, headers)

    def load_description(self):
        self.description = read_file(
            os.path.join(
                self.resource_dir,
                "%s_doc.md" % self.method))

    def add_response(self, status_code, format, body, headers):
        self.responses.append({
            "status_code": status_code,
            "format": format,
            "body": body,
            "headers": headers
        })

    def save(self):
        if not os.path.exists(self.resource_dir):
            os.makedirs(self.resource_dir)

        # save resource in given responses
        for response in self.responses:
            self.save_response(**response)

        # write description
        if self.description:
            self.save_description()

    def save_description(self):
        description_path = os.path.join(
            self.resource_dir, "%s_doc.md" % self.method)
        with open(description_path, "w") as f:
            f.write(utf8(self.description))

    def save_response(self, status_code, format, body, headers):
        content_path = os.path.join(
            self.resource_dir,
            "%s_%s.%s" % (self.method, status_code, format))
        headers_path = os.path.join(
            self.resource_dir,
            "%s_H_%s.%s" % (self.method, status_code, format))

        # write content
        with open(content_path, "w") as f:
            f.write(utf8(body))

        # write headers
        with open(headers_path, "w") as f:
            f.write(utf8(headers))

    def delete(self):
        # delete all resource method body and headers
        content_path = os.path.join(
            self.resource_dir,
            "%s_*" % self.method)
        headers_path = os.path.join(
            self.resource_dir,
            "%s_H_*" % self.method)

        for path in glob.glob(content_path):
            os.unlink(path)

        for path in glob.glob(headers_path):
            os.unlink(path)

        # delete description
        description_path = os.path.join(
            self.resource_dir,
            "%s_doc.md" % self.method)

        self._delete_file(description_path)


class RPCMethod(BaseMethod):

    def __init__(self, methods_dir, name):
        super(RPCMethod, self).__init__()

        self.methods_dir = methods_dir
        self.name = name
        self.description = ""

    def save(self, response):
        if not os.path.exists(self.methods_dir):
            os.makedirs(self.methods_dir)

        # write description
        if self.description:
            self.save_description()

        # write method
        method_path = os.path.join(self.methods_dir, self.name)

        with open(method_path, "w") as f:
            f.write(utf8(response))

    def save_description(self):
        description_path = os.path.join(
            self.methods_dir,
            "%s_doc.md" % self.name)
        with open(description_path, "w") as f:
            f.write(utf8(self.description))

    def delete(self):
        method_path = os.path.join(self.methods_dir, self.name)
        description_path = os.path.join(
            self.methods_dir, "%s_doc.md" % self.name)

        self._delete_file(method_path)
        self._delete_file(description_path)

    def load(self):
        self.edit = True
        self.method_response = read_file(
            os.path.join(self.methods_dir, self.name))

    def load_description(self):
        self.description = read_file(
            os.path.join(self.methods_dir, "%s_doc.md" % self.name))


def load_resources_log(log_name):
    if os.path.isfile(log_name):
        with open(log_name) as f:
            data = [json.loads(line) for line in f.readlines()]
    else:
        data = []
    return data


def add_to_resources_log(log_name, data):
    with open(log_name, "a") as f:
        f.write("%s\n" % json.dumps(data, cls=ExtendedJSONEncoder))
