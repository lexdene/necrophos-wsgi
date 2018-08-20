from io import BytesIO

from asynctest import TestCase


# compat with old style
def old_simple_app(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return ["hello, world!\n"]


# yield response in old style
def old_app_with_yield(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    yield "hello, world!\n"


# use write
def old_app_with_write(env, start_response):
    write = start_response('200 OK', [('Content-Type', 'text/plain')])
    write('hello, world!\n')
    return []


class OldAppObject:
    def __call__(self, env, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return ["hello, world!\n"]


async def get_response():
    from asyncio import sleep

    await sleep(0.1)
    return 'hello from get response\n'


# simple async app
async def simple_async_app(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    res = await get_response()
    return [res]


# use write in async app
async def async_app_with_write(env, start_response):
    write = start_response('200 OK', [('Content-Type', 'text/plain')])
    await write('hello, world!\n')
    return []


class AppObject:
    async def __call__(self, env, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        res = await get_response()
        return [res]


class TestReader:
    def __init__(self, content):
        self.content = content

    async def readuntil(self, sep):
        index = self.content.find(sep)

        p = index + len(sep)
        ret = self.content[:p]
        self.content = self.content[p:]

        return ret


class TestWriter:
    def __init__(self, fp):
        self.fp = fp

    def write(self, data):
        self.fp.write(data)

    async def drain(self):
        pass

    def close(self):
        pass


class TestServer:
    def __init__(self, app):
        self.app = app

    async def request(self, method, path):
        from necrophos_wsgi.connection import Connection

        req = BytesIO()
        req.write(('%s %s HTTP/1.1\r\n' % (method, path)).encode())
        req.write(b'\r\n')
        content = req.getvalue()
        reader = TestReader(content)

        resp = BytesIO()
        writer = TestWriter(resp)

        cnct = Connection(self, reader, writer)
        await cnct.run()

        return resp

    def get_app(self):
        return self.app


class TestAppTestCase(TestCase):
    async def test_old_simple_app(self):
        server = TestServer(old_simple_app)
        resp = await server.request(
            method='GET',
            path='/test',
        )

        content = resp.getvalue()

        self.assertEqual(
            content,
            b'HTTP/1.1 200 OK\r\n'
            b'Content-Type: text/plain\r\n'
            b'Content-Length: 14\r\n'
            b'\r\n'
            b'hello, world!\n'
        )

    async def test_old_app_with_yield(self):
        server = TestServer(old_app_with_yield)
        resp = await server.request(
            method='GET',
            path='/test',
        )

        content = resp.getvalue()

        self.assertEqual(
            content,
            b'HTTP/1.1 200 OK\r\n'
            b'Content-Type: text/plain\r\n'
            b'\r\n'
            b'hello, world!\n'
        )

    async def test_old_app_with_write(self):
        server = TestServer(old_app_with_write)
        resp = await server.request(
            method='GET',
            path='/test',
        )

        content = resp.getvalue()

        self.assertEqual(
            content,
            b'HTTP/1.1 200 OK\r\n'
            b'Content-Type: text/plain\r\n'
            b'\r\n'
            b'hello, world!\n'
        )

    async def test_old_app_object(self):
        server = TestServer(OldAppObject())
        resp = await server.request(
            method='GET',
            path='/test',
        )

        content = resp.getvalue()

        self.assertEqual(
            content,
            b'HTTP/1.1 200 OK\r\n'
            b'Content-Type: text/plain\r\n'
            b'Content-Length: 14\r\n'
            b'\r\n'
            b'hello, world!\n'
        )

    async def test_simple_async_app(self):
        server = TestServer(simple_async_app)
        resp = await server.request(
            method='GET',
            path='/test',
        )

        content = resp.getvalue()

        self.assertEqual(
            content,
            b'HTTP/1.1 200 OK\r\n'
            b'Content-Type: text/plain\r\n'
            b'Content-Length: 24\r\n'
            b'\r\n'
            b'hello from get response\n'
        )

    async def test_async_app_with_write(self):
        server = TestServer(async_app_with_write)
        resp = await server.request(
            method='GET',
            path='/test',
        )

        content = resp.getvalue()

        self.assertEqual(
            content,
            b'HTTP/1.1 200 OK\r\n'
            b'Content-Type: text/plain\r\n'
            b'\r\n'
            b'hello, world!\n'
        )

    async def test_app_object(self):
        server = TestServer(AppObject())
        resp = await server.request(
            method='GET',
            path='/test',
        )

        content = resp.getvalue()

        self.assertEqual(
            content,
            b'HTTP/1.1 200 OK\r\n'
            b'Content-Type: text/plain\r\n'
            b'Content-Length: 24\r\n'
            b'\r\n'
            b'hello from get response\n'
        )
