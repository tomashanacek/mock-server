# -*- coding: utf-8 -*-

import xmlrpclib
import rpc
from xml.parsers import expat


class FilesMockProvider(rpc.FilesMockProvider):

    CONTENT_TYPE = ("Content-Type", "text/xml")

    @staticmethod
    def get_method_name(request_body):
        try:
            return xmlrpclib.loads(request_body)[1]
        except expat.ExpatError:
            return ""

    def _fault(self, error):
        return xmlrpclib.Fault(*error)

    def _dump(self, data):
        return xmlrpclib.dumps((data, ), methodresponse=True)


class UpstreamServerProvider(rpc.UpstreamServerProvider):
    pass


if __name__ == "__main__":

    import api

    provider = FilesMockProvider("/Users/tomashanacek/Downloads/api")

    print provider(api.Request(
        body="<?xml version='1.0'?><methodCall><methodName>user.list"
             "</methodName><params></params></methodCall>"))
    print provider.error

    print provider(api.Request(
        body="<?xml version='1.0'?><methodCall><methodName>user.get"
             "</methodName><params></params></methodCall>"))
    print provider.error
