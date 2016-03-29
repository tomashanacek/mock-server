# -*- coding: utf-8 -*-

import os
import tornado.web
from . import handlers
from . import api_settings
import imp

from concurrent import futures
from .data import SUPPORTED_FORMATS


class Application(tornado.web.Application):
    def __init__(self, port, address, api_dir, debug,
                 api_data_filename, custom_provider=None):

        self.pool = futures.ThreadPoolExecutor(2)
        self.api_settings_class = api_settings.ApiSettings
        self.custom_provider = None

        if custom_provider is not None:
            provider_path = os.path.abspath(custom_provider)
            print(provider_path)
            module = imp.load_source('custom_provider', provider_path)
            if hasattr(module, 'provider'):
                self.custom_provider = module.provider

        supported_formats = "|".join(
            [".%s" % x for x in list(SUPPORTED_FORMATS.keys())])
        handlers_list = [
            (r"/__manage/resource/(.*)", handlers.ResourceMethodHandler),
            (r"/__manage/rpc/(.*)", handlers.RPCMethodHandler),
            (r"/__manage/logs", handlers.ResourcesLogsHandler),
            (r"/__manage/create/rpc", handlers.CreateRPCMethodHandler),
            (r"/__manage/create", handlers.CreateResourceMethodHandler),
            (r"/__manage/login", handlers.LoginHandler),
            (r"/__manage/logout", handlers.LogoutHandler),
            (r"/__manage/settings", handlers.SettingsHandler),
            (r"/__manage/todo", handlers.TodoHandler),
            (r"/__manage", handlers.ListResourcesHandler),
            (r"/%s" % handlers.RPCHandler.PATH, handlers.RPCHandler),
            (r"/(.*)(%s)" % supported_formats, handlers.MainHandler),
            (r"/(.*)", handlers.MainHandler),
        ]
        settings = dict(
            debug=debug,
            port=port,
            address=address,
            dir=api_dir,
            api_data_filename=api_data_filename,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            static_url_prefix="/__static/",
            login_url="/__manage/login",
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        )
        super(Application, self).__init__(handlers_list, **settings)
