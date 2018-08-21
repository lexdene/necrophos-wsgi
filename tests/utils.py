from http.client import HTTPResponse


class FakeSocket:
    def __init__(self, fp):
        self.fp = fp

    def makefile(self, *argv, **kwargs):
        return self.fp


def parse_response(fp):
    fp.seek(0)
    resp = HTTPResponse(FakeSocket(fp))
    resp.begin()

    return resp
