from asyncio import get_event_loop, start_server


class EventLoop(object):
    def __init__(self, real_loop):
        self._real = real_loop

    @classmethod
    def get_event_loop(cls):
        real_loop = get_event_loop()
        return cls(real_loop)

    def create_task(self, coro):
        def on_task_done(fut):
            assert fut.done(), 'task is not done'

            err = fut.exception()
            if err:
                self._real.stop()
                raise err

        task = self._real.create_task(coro)
        task.add_done_callback(on_task_done)

        return task

    def start_server(self, connected, port):
        return start_server(
            connected, port=port, loop=self._real
        )

    # pass by methods
    def run_forever(self):
        return self._real.run_forever()
