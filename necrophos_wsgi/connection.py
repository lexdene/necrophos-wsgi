import logging
from itertools import chain

from .exceptions import ParseError
from .response import Response
from .utils import ensure_bytes

HTTP_LINE_SEPARATOR = b'\r\n'

logger = logging.getLogger(__name__)


class Connection(object):
    def __init__(self, server, reader, writer):
        self.server = server

        self.reader = reader
        self.writer = writer

        self.response = None

    async def run(self):
        env = {}

        line_it = self._read_line()
        first_line = await line_it.__anext__()
        env.update(_parse_first_line(first_line))

        async for line in line_it:
            name, value = _parse_header(line)

            if name == b'Host':
                host, port = _parse_server(value)
                env['SERVER_NAME'] = host
                env['SERVER_PORT'] = port
            else:
                key = name.upper().replace(b'-', b'_')
                if key in (
                    b'CONTENT_LENGTH',
                    b'CONTENT_TYPE',
                ):
                    env[key] = value

        logger.debug('env: %s', env)
        self.response = Response()

        app = self.server.get_app()
        ret = app(env, self.start_response)

        await self._write_line(b'HTTP/1.1 %s' % self.response.status.encode())

        if len(ret) == 1 and isinstance(ret[0], (bytes, str)):
            body = ensure_bytes(ret[0])

        content_length = len(body)

        headers = [
            ('Content-Length', str(content_length)),
        ]
        for key, value in chain(
            headers, self.response.headers
        ):
            await self._write_line(
                b'%s: %s' % (
                    ensure_bytes(key),
                    ensure_bytes(value),
                )
            )
        await self._write_line(b'')
        await self.writer.drain()

        self.writer.write(body)
        await self.writer.drain()

    async def _read_line(self):
        while True:
            line = await self.reader.readuntil(HTTP_LINE_SEPARATOR)

            # remove separator
            line = line[:-len(HTTP_LINE_SEPARATOR)]

            if not line:
                break

            yield line

    async def _write_line(self, line):
        self.writer.write(line + HTTP_LINE_SEPARATOR)

    def start_response(self, status, headers):
        self.response.status = status
        self.response.headers = headers


def _parse_first_line(line):
    env = {}

    parts = line.split(b' ')
    if len(parts) != 3:
        raise ParseError('first line parts count error: %d', len(parts))

    method, uri, version = parts

    path, query = _split_uri(uri)

    env['REQUEST_METHOD'] = method
    env['SCRIPT_NAME'] = ''
    env['PATH_INFO'] = path

    if query:
        env['QUERY_STRING'] = query

    env['SERVER_PROTOCOL'] = version

    return env


def _split_uri(uri):
    if b'?' in uri:
        parts = uri.split(b'?', 1)
        if len(parts) == 2:
            return parts
        else:
            raise ParseError('parse uri error: %s' % uri)
    else:
        return uri, ''


def _parse_header(line):
    parts = line.split(b':', 1)
    if len(parts) == 2:
        return parts[0], parts[1].strip()
    else:
        raise ParseError('parse header error: %s' % line)


def _parse_server(server):
    parts = server.split(b':', 1)
    if len(parts) == 2:
        host, port = parts
        port = int(port)
    else:
        host = server
        port = 80

    return host, port
