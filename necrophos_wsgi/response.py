from asyncio import iscoroutinefunction
from io import BytesIO

from .utils import ensure_bytes


def is_async_mode(app):
    return iscoroutinefunction(app) or iscoroutinefunction(app.__call__)


async def read_body(env):
    if 'CONTENT_LENGTH' in env:
        content_length = int(env['CONTENT_LENGTH'].decode())
        body = await env['wsgi.input'].read(content_length)

        env['wsgi.input'] = BytesIO(body)


class Response(object):
    def __init__(self, writer):
        # writer is a HttpWriter object
        self.writer = writer

        self.status = b''
        self.headers = []

        self.is_headers_sent = False

    async def run(self, app, env):
        if is_async_mode(app):
            ret = await app(env, self.start_response)
        else:
            await read_body(env)
            ret = app(env, self.sync_start_response)

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
            self.send_headers()
            await self.writer.drain()

        self.writer.write(ensure_bytes(chunk))
        await self.writer.drain()

    def sync_start_response(self, *argv):
        self.start_response(*argv)

        return self.sync_write

    def sync_write(self, chunk):
        if not self.is_headers_sent:
            self.send_headers()

        self.writer.write(ensure_bytes(chunk))

    def send_headers(self):
        self.writer.write_line(
            b'HTTP/1.1 %s' % ensure_bytes(self.status)
        )

        for key, value in self.headers:
            self.writer.write_line(
                b'%s: %s' % (
                    ensure_bytes(key),
                    ensure_bytes(value),
                )
            )
        self.writer.write_line(b'')

        self.is_headers_sent = True
