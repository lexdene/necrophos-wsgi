import logging

from .event_loop import EventLoop
from .connection import Connection
from .utils import import_object

logger = logging.getLogger(__name__)


class Server(object):
    def __init__(self, app_path, loop=None):
        self.app_path = app_path

        if loop is None:
            loop = EventLoop.get_event_loop()

        self.loop = loop

    def run(self, *argv, **kwargs):
        self.loop.create_task(
            self.startup(*argv, **kwargs)
        )

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass

    async def startup(self, port):
        await self.loop.start_server(
            self._client_connected,
            port=port
        )
        logger.info('server started on port %s' % (port,))

    async def _client_connected(self, reader, writer):
        logger.info('connected!')
        cnct = Connection(self, reader, writer)
        await cnct.run()

    def get_app(self):
        return import_object(self.app_path)
