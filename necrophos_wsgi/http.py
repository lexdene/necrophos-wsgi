HTTP_LINE_SEPARATOR = b'\r\n'


class HttpReader(object):
    def __init__(self, reader):
        self._real = reader

    async def iter_lines(self):
        while True:
            line = await self._real.readuntil(HTTP_LINE_SEPARATOR)

            # remove separator
            line = line[:-len(HTTP_LINE_SEPARATOR)]

            if not line:
                break

            yield line


class HttpWriter(object):
    def __init__(self, writer):
        self._real = writer

    def write_line(self, line):
        self._real.write(line + HTTP_LINE_SEPARATOR)

    # pass by methods
    def write(self, data):
        return self._real.write(data)

    async def drain(self):
        return await self._real.drain()

    def close(self):
        return self._real.close()
