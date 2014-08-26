from mock_server.api import Response
import json


def provider(request):
    if request.uri == '/abc':
        headers = [("Content-Type", "application/json; charset=utf-8")]
        content = {"name": "Tomas", "surname": "Hanacek"}
        return Response(json.dumps(content), headers, 200)
