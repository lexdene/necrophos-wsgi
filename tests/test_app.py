# compat with old style
def old_simple_app(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return ["hello, world!\n"]


# yield response in old style
def old_app_with_yield(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    yield "hello, world!\n"


# not supported: write must be async
def old_app_with_write(env, start_response):
    write = start_response('200 OK', [('Content-Type', 'text/plain')])
    write('hello, world!\n')
    return []


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
