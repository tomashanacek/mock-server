# -*- coding: utf-8 -*-

import fastrpc
import rpc
import api


class FilesMockProvider(rpc.FilesMockProvider):

    CONTENT_TYPE = ("Content-Type", "application/x-frpc")

    @staticmethod
    def get_method_name(request_body):
        try:
            return fastrpc.loads(request_body)[1]
        except RuntimeError, e:
            print e
            return ""

    def _fault(self, error):
        return fastrpc.Fault(*error)

    def _dump(self, data):
        if isinstance(data, fastrpc.Fault):
            return fastrpc.dumps(data, methodresponse=True, useBinary=True)
        else:
            return fastrpc.dumps((data, ), methodresponse=True, useBinary=True)


class UpstreamServerProvider(api.UpstreamServerProvider):

    def __init__(self, upstream_server):
        super(UpstreamServerProvider, self).__init__(upstream_server)

        self._proxy = None

    @property
    def proxy(self):
        if self._proxy is None:
            self._proxy = fastrpc.ServerProxy(self.upstream_server)

        return self._proxy

    def __call__(self, data, request_handler_callback):
        request = fastrpc.loads(data)

        f = getattr(self.proxy, request[1])
        try:
            data = (f(*request[0]), )
        except fastrpc.Fault, e:
            data = e

        request_handler_callback(
            api.Response(
                fastrpc.dumps(data, methodresponse=True, useBinary=True),
                [("Content-Type", "application/x-frpc")]))
