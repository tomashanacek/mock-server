# -*- coding: utf-8 -*-

import os
import tornado.web
import handlers
import api_settings

from concurrent import futures
from data import SUPPORTED_FORMATS


class Application(tornado.web.Application):
    def __init__(self, port, address, api_dir, debug, api_data_filename):

        self.pool = futures.ThreadPoolExecutor(2)
        self.api_settings_class = api_settings.ApiSettings

        supported_formats = "|".join(
            map(lambda x: ".%s" % x, SUPPORTED_FORMATS.keys()))
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
