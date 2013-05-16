# -*- coding: utf-8 -*-

import os
import re
import json
import glob
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from tornado.escape import utf8
from util import read_file


def get_url_path(file_path):
    url_path = []

    for path in file_path.split("/"):
        url_path.append(re.sub(r"__(.*)", r"{\1}", path))

    return "/".join(url_path)


def get_file_path(url_path):
    if url_path.startswith("/"):
        url_path = url_path[1:]

    file_path = []
    for path in url_path.split("/"):
        file_path.append(re.sub(r"{(.*)}", r"__\1", path))

    return "/".join(file_path)


class ApplicationData(object):

    def __init__(self, filename):
        self.filename = filename
        self.data = {}
        self._upstream_server = ""
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
        data = read_file(self.filename)

        if data:
            try:
                self.data = json.loads(data)

                self.upstream_server = self.data.get("upstream-server", "")
                self.resources = self.data.get("resources", self.resources)

                self.load_categories()

            except ValueError:
                pass

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

        with open(self.filename, "w") as f:
            f.write(json.dumps(self.data))

    def get_category(self, resource):
        return self._get_resource_attribute(resource, "category")

    def get_upstream_server(self, resource):
        return self._get_resource_attribute(resource, "upstream-server", False)

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

    def _get_resource_attribute(self, resource, key, default=""):
        if resource in self.resources and \
                key in self.resources[resource]:
            return self.resources[resource][key]
        else:
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

    def __init__(self, api_dir, url_path, method, status_code):
        super(ResourceMethod, self).__init__()

        self.url_path = url_path
        self.method = method
        self.status_code = status_code

        file_url_path = get_file_path(url_path)

        self.id = "%s-%s-%s" % (method, status_code, file_url_path)
        self.resource_dir = os.path.join(api_dir, file_url_path)

        self.formats = []

    def load_format(self, format):
        self.format = format

        self.response_body = read_file(
            os.path.join(
                self.resource_dir,
                "%s_%s.%s" % (self.method, self.status_code, format)))
        self.response_headers = read_file(
            os.path.join(
                self.resource_dir,
                "%s_H_%s.%s" % (self.method, self.status_code, format)))

        if self.response_body:
            self.edit = True

    def load_description(self):
        self.description = read_file(
            os.path.join(
                self.resource_dir,
                "%s_%s_doc.md" % (self.method, self.status_code)))

    def add_format(self, format, response_body, response_headers):

        self.formats.append((format, response_body, response_headers))

    def save(self):
        if not os.path.exists(self.resource_dir):
            os.makedirs(self.resource_dir)

        # save resource in given formats
        for format in self.formats:
            self.save_format(*format)

        # write description
        if self.description:
            description_path = os.path.join(
                self.resource_dir,
                "%s_%s_doc.md" % (self.method, self.status_code))
            with open(description_path, "w") as f:
                f.write(utf8(self.description))

    def save_format(self, format, response_body, response_headers):
        content_path = os.path.join(
            self.resource_dir,
            "%s_%s.%s" % (self.method, self.status_code, format))
        headers_path = os.path.join(
            self.resource_dir,
            "%s_H_%s.%s" % (self.method, self.status_code, format))

        # write content
        with open(content_path, "w") as f:
            f.write(utf8(response_body))

        # write headers
        with open(headers_path, "w") as f:
            f.write(utf8(response_headers))

    def delete(self):
        # delete all resource method body and headers
        content_path = os.path.join(
            self.resource_dir,
            "%s_%s.*" % (self.method, self.status_code))
        headers_path = os.path.join(
            self.resource_dir,
            "%s_H_%s.*" % (self.method, self.status_code))

        for path in glob.glob(content_path):
            os.unlink(path)

        for path in glob.glob(headers_path):
            os.unlink(path)

        # delete description
        description_path = os.path.join(
            self.resource_dir,
            "%s_%s_doc.md" % (self.method, self.status_code))

        self._delete_file(description_path)


class RPCMethod(BaseMethod):

    def __init__(self, methods_dir):
        super(RPCMethod, self).__init__()

        self.methods_dir = methods_dir
        self.name = ""
        self.description = ""

    def save(self, name, response):
        if not os.path.exists(self.methods_dir):
            os.makedirs(self.methods_dir)

        # write description
        if self.description:
            description_path = os.path.join(
                self.methods_dir,
                "%s_doc.md" % name)
            with open(description_path, "w") as f:
                f.write(utf8(self.description))

        # write method
        method_path = os.path.join(self.methods_dir, name)

        with open(method_path, "w") as f:
            f.write(utf8(response))

    def delete(self, name):
        method_path = os.path.join(self.methods_dir, name)
        description_path = os.path.join(self.methods_dir, "%s_doc.md" % name)

        self._delete_file(method_path)
        self._delete_file(description_path)

    def load(self, name):
        self.name = name
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
        f.write("%s\n" % json.dumps(data))
