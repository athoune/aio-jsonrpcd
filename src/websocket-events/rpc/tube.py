from typing import Coroutine
from asyncio import Queue, create_task, Future, Task


class Tube:
    """Put coroutines in the tube and iterate over unordered results."""

    def __init__(
        self,
    ) -> None:
        self._queries = set()
        self._answers = Queue()

    def _done(self, future: Future) -> None:
        self._queries.discard(future)
        self._answers.put_nowait(future.result())

    def put(self, coro: Coroutine) -> None:
        t: Task = create_task(coro)
        self._queries.add(t)
        t.add_done_callback(self._done)

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self._answers.get()
