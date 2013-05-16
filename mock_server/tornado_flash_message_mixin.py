# -*- coding: utf-8 -*-

import tornado.escape


class FlashMessageMixin(object):
    def set_flash_message(self, key, message):
        if not isinstance(message, basestring):
            message = tornado.escape.json_encode(message)

        self.set_secure_cookie("flash_msg_%s" % key, message)

    def get_flash_message(self, key):
        value = self.get_secure_cookie("flash_msg_%s" % key)
        self.clear_cookie("flash_msg_%s" % key)

        return value

    def get_flash_messages(self, keys):
        values = []

        for key in keys:
            value = self.get_flash_message(key)

            if value:
                values.append((key, value))

        return values
