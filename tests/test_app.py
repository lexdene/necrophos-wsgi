# compat with old style
def old_simple_app(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return ["hello, world!\n"]


# use write in old style
def old_app_with_write(env, start_response):
    write = start_response('200 OK', [('Content-Type', 'text/plain')])
    write('hello, world!')
    return []


# simple async app
async def simple_async_app(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    res = await get_response()
    return [res]


# use write in async app
async def async_app_with_write(env, start_response):
    write = start_response('200 OK', [('Content-Type', 'text/plain')])
    await write('hello, world!')
    return []
