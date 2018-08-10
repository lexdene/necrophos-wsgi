from asyncio import iscoroutinefunction

from .utils import ensure_bytes


class Response(object):
    def __init__(self, connection):
        self.connection = connection

        self.status = b''
        self.headers = []

        self.is_headers_sent = False

    async def run(self, app, env):
        # app = self.connection.server.get_app()
        if iscoroutinefunction(app):
            ret = await app(env, self.start_response)
        else:
            ret = app(env, self.start_response)

        length = None
        try:
            length = len(ret)
        except TypeError:
            pass

        if length == 1 and isinstance(ret[0], (bytes, str)):
            body = ensure_bytes(ret[0])

            content_length = len(body)

            self.headers.append(
                ('Content-Length', str(content_length)),
            )

        for chunk in ret:
            await self.write(chunk)

    def start_response(self, status, headers):
        self.status = status
        self.headers = headers

        return self.write

    async def write(self, chunk):
        if not self.is_headers_sent:
            await self.send_headers()

        self.connection.writer.write(ensure_bytes(chunk))
        await self.connection.writer.drain()

    async def send_headers(self):
        await self.connection.write_line(
            b'HTTP/1.1 %s' % ensure_bytes(self.status)
        )

        for key, value in self.headers:
            await self.connection.write_line(
                b'%s: %s' % (
                    ensure_bytes(key),
                    ensure_bytes(value),
                )
            )
        await self.connection.write_line(b'')
        await self.connection.writer.drain()

        self.is_headers_sent = True
