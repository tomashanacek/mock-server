# -*- coding: utf-8 -*-

import os
import json

from abc import ABCMeta, abstractproperty, abstractmethod
from util import read_file
from model import ApiData


class ApiSettingsBase:

    __metaclass__ = ABCMeta

    def __init__(self, settings, request):
        self._settings = settings
        self._request = request

    @abstractproperty
    def api_dir(self):
        pass

    @abstractproperty
    def api_data(self):
        pass


class ApiDataModelBase:

    __metaclass__ = ABCMeta

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def save(self, data):
        pass


class ApiSettings(ApiSettingsBase):

    def __init__(self, settings, request):
        super(ApiSettings, self).__init__(settings, request)

        if not os.path.exists(self.api_dir):
            os.makedirs(self.api_dir)

    @property
    def api_dir(self):
        return self._settings["dir"]

    @property
    def api_data(self):
        api_data = ApiData(
            ApiDataModel(os.path.join(
                self.api_dir, self._settings["api_data_filename"])))
        api_data.load()

        return api_data


class ApiDataModel(ApiDataModelBase):

    def __init__(self, filename):
        self.filename = filename

    def load(self):
        data = read_file(self.filename)

        if data:
            try:
                return json.loads(data)
            except ValueError:
                pass

        return {}

    def save(self, data):
        with open(self.filename, "w") as f:
            f.write(json.dumps(data))
