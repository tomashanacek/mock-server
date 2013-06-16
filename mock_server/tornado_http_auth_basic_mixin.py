# -*- coding: utf-8 -*-

import base64


class HttpAuthBasicMixin(object):
    def authorization(self):
        auth_header = self.request.headers.get("Authorization")

        if auth_header is not None and auth_header.startswith("Basic "):
            auth_decoded = base64.decodestring(auth_header[6:])
            username, password = auth_decoded.split(":", 2)
            return username, password

        return None

    def authenticate(self):
        self.set_status(401)
        self.set_header("WWW-Authenticate", 'Basic realm=Restricted')
        self.finish()
