from asyncio import get_event_loop, start_server
from itertools import chain

HTTP_LINE_SEPARATOR = b'\r\n'


def create_critical_task(loop, coro):
    def on_task_done(fut):
        assert fut.done(), 'task is not done'

        err = fut.exception()
        if err:
            loop.stop()
            raise err

    task = loop.create_task(coro)
    task.add_done_callback(on_task_done)

    return task


async def startup(loop, port):
    await start_server(
        _client_connected,
        port=port,
        loop=loop,
    )
    print('server started on port %s' % port)


class Response(object):
    def __init__(self):
        self.status = b''
        self.headers = []
        self.body = b''


class Connection(object):
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

        self.response = None

    async def run(self):
        env = {}

        line_it = self._read_line()
        first_line = await line_it.__anext__()
        _parse_first_line(env, first_line)

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

        self.response = Response()

        app = get_app()
        ret = app(env, self.start_response)

        await self._write_line(b'HTTP/1.1 %s' % self.response.status.encode())

        if len(ret) == 1 and isinstance(ret[0], (bytes, str)):
            body = _ensure_bytes(ret[0])

        content_length = len(body)

        headers = [
            ('Content-Length', str(content_length)),
        ]
        for key, value in chain(
            headers, self.response.headers
        ):
            await self._write_line(
                b'%s: %s' % (
                    _ensure_bytes(key),
                    _ensure_bytes(value),
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


async def _client_connected(reader, writer):
    print('connected!')
    cnct = Connection(reader, writer)
    await cnct.run()


class ParseError(Exception):
    pass


def _parse_first_line(env, line):
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


def _ensure_bytes(value):
    if isinstance(value, str):
        value = value.encode('utf-8')

    return value


def get_app():
    from tests.test_app import old_simple_app
    return old_simple_app


def main():
    loop = get_event_loop()
    create_critical_task(loop, startup(loop, 8080))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
