import logging

from .exceptions import ParseError
from .response import Response
from .http import HttpReader, HttpWriter

logger = logging.getLogger(__name__)


class Connection(object):
    def __init__(self, server, reader, writer):
        self.server = server

        self.reader = HttpReader(reader)
        self.writer = HttpWriter(writer)

    async def run(self):
        env = {}

        line_it = self.reader.iter_lines()
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

        app = self.server.get_app()

        response = Response(self.writer)
        await response.run(app, env)

        await self.writer.drain()
        self.writer.close()


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
