from io import BytesIO

from asynctest import TestCase

from .utils import parse_response


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
    return 'hello, world!\n'


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


# read body
async def read_body_app(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])

    length = int(env['CONTENT_LENGTH'].decode())
    body = await env['wsgi.input'].read(length)
    return [b'body is `%s`\n' % body]


# old app read body
def old_app_read_body(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    length = int(env['CONTENT_LENGTH'].decode())
    body = env['wsgi.input'].read(length)
    return [b'body is `%s`\n' % body]


class TestReader:
    def __init__(self, content):
        self.content = content

    async def readuntil(self, sep):
        index = self.content.find(sep)

        p = index + len(sep)
        return await self.read(p)

    async def read(self, n):
        ret = self.content[:n]
        self.content = self.content[n:]

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

    async def request(self, method, path, headers={}, body=None):
        from necrophos_wsgi.connection import Connection

        req = BytesIO()
        req.write(('%s %s HTTP/1.1\r\n' % (method, path)).encode())
        for key, value in headers.items():
            req.write(b'%s: %s\r\n' % (key.encode(), value.encode()))
        req.write(b'\r\n')
        if body:
            req.write(body)

        content = req.getvalue()
        reader = TestReader(content)

        resp = BytesIO()
        writer = TestWriter(resp)

        cnct = Connection(self, reader, writer)
        await cnct.run()

        return parse_response(resp)

    def get_app(self):
        return self.app


class TestAppTestCase(TestCase):
    async def test_apps(self):
        for app, has_length in (
            (old_simple_app, True),
            (old_app_with_yield, False),
            (old_app_with_write, False),
            (OldAppObject(), True),
            (simple_async_app, True),
            (async_app_with_write, False),
            (AppObject(), True),
        ):
            with self.subTest(app=app):
                server = TestServer(app)
                resp = await server.request(
                    method='GET',
                    path='/test',
                )

                self.assertEqual(resp.status, 200)
                self.assertEqual(resp.headers['Content-Type'], 'text/plain')
                if has_length:
                    self.assertEqual(
                        resp.headers['Content-Length'],
                        '14'
                    )
                else:
                    self.assertNotIn(
                        'Content-Length', resp.headers
                    )

                body = resp.read1()
                self.assertEqual(body, b'hello, world!\n')

    async def test_read_body(self):
        for app in (
            read_body_app,
            old_app_read_body,
        ):
            with self.subTest(app=app):
                server = TestServer(app)

                body = b'some body here'

                resp = await server.request(
                    method='POST',
                    path='/test',
                    headers={
                        'Content-Length': str(len(body)),
                    },
                    body=body,
                )

                self.assertEqual(resp.status, 200)
                self.assertEqual(resp.headers['Content-Type'], 'text/plain')

                body = resp.read1()
                self.assertEqual(body, b'body is `some body here`\n')
