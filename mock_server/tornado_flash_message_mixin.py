#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.escape


class FlashMessageMixin(object):
    def set_flash_message(self, key, message):
        if not isinstance(message, basestring):
            message = tornado.escape.json_encode(message)

        self.set_secure_cookie("flash_msg_%s" % key, message)

    def get_flash_message(self, key):
        val = self.get_secure_cookie("flash_msg_%s" % key)
        self.clear_cookie("flash_msg_%s" % key)

        return val
