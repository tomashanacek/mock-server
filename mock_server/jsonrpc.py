# -*- coding: utf-8 -*-

import jsonrpclib
import rpc


class FilesMockProvider(rpc.FilesMockProvider):

    CONTENT_TYPE = ("Content-Type", "application/json")

    def _fault(self, error):
        return jsonrpclib.Fault(*error)

    def _dump(self, data, rpcid=1):
        return jsonrpclib.dumps(data, methodresponse=True, rpcid=rpcid)

    @staticmethod
    def get_method_name(request_body):
        try:
            data = jsonrpclib.loads(request_body)
            if not data or "method" not in data:
                return ""
            return data["method"]
        except ValueError:
            return ""


class UpstreamServerProvider(rpc.UpstreamServerProvider):
    pass


if __name__ == "__main__":

    import api

    provider = FilesMockProvider("/Users/tomashanacek/Downloads/api")

    print provider(api.Request(body='{"method": "user.list", "id": 1}'))
    print provider.error

    print provider(
        method_name=FilesMockProvider.get_method_name(
            '{"method": "user.get", "id": 1}'))
    print provider.error
