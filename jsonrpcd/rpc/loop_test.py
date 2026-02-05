from asyncio import Queue, create_task, sleep
from collections.abc import AsyncGenerator
from typing import Any, Coroutine

import pytest

from .loop import Loop, Message


class OutTest:
    def __init__(self) -> None:
        self.messages = Queue[dict[str, Any]]()

    async def __call__(self, message: dict[str, Any]):
        await self.messages.put(message)

    def __len__(self) -> int:
        return self.messages.qsize()

    async def pop(self) -> dict[str, Any]:
        return await self.messages.get()


@pytest.mark.asyncio
async def test_loop_send():
    out = OutTest()

    async def _test_method(msg: Message) -> str:
        return f"Hello {msg['params'][0]}"

    def handler(msg: Message) -> Coroutine:
        if msg["method"] == "test":
            return _test_method(msg)
        else:
            raise Exception(f"Unregistered method: {msg['method']}")

    loop = Loop(handler, out)
    queue_in = Queue[dict[str, Any]]()

    async def pump() -> AsyncGenerator[dict[str, Any], None]:
        while True:
            yield await queue_in.get()

    async def looping() -> None:
        await loop.loop(pump())

    create_task(looping())

    await queue_in.put(dict(jsonrpc="2.0", method="test", params=[42], id=12))
    await sleep(0.1)
    r = await out.pop()
    assert r["result"] == "Hello 42"


@pytest.mark.asyncio
async def test_loop_receive():
    out = OutTest()

    def handler(msg: Message) -> Coroutine:
        async def nothing():
            pass

        return nothing()

    loop = Loop(handler, out)
    queue_in = Queue[dict[str, Any]]()

    async def pump() -> AsyncGenerator[dict[str, Any], None]:
        while True:
            yield await queue_in.get()

    async def looping() -> None:
        await loop.loop(pump())

    create_task(looping())

    async def response():
        r = await out.pop()
        print(r)
        assert r["id"] == 0
        assert r["method"] == "hola"
        assert r["params"] == ["Mundo"]
        await queue_in.put(dict(id=r["id"], result=f"Hola el {r['params'][0]}"))

    create_task(response())
    r = await loop.send_request("hola", ["Mundo"])
    print(r)
    assert r == "Hola el Mundo"
