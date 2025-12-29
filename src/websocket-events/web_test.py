from typing import cast
import pytest
from aiohttp import web, WSMsgType
import asyncio
from json_rpc import Dispatcher
from web import JSONRPC
from aiohttp._websocket.models import WSMessage
import json


async def app_test():
    routes = web.RouteTableDef()
    app = web.Application()

    @routes.get("/rpc")
    async def testWS(request: web.Request):
        pass

    app.add_routes(routes)
    web.run_app(app)


class WebsocketMockup:
    def __init__(self) -> None:
        self.wrote = asyncio.Queue[str]()
        self.read = asyncio.Queue[str]()

    def __aiter__(self):
        return self

    async def __anext__(self):
        data = await self.read.get()
        return WSMessage(type=WSMsgType.TEXT, data=data, extra=None)

    async def write(self, txt: str):
        await self.wrote.put(txt)


@pytest.mark.asyncio
async def testPlop():
    async def hello(txt: str) -> str:
        return f"Hello {txt}"

    dispatcher = Dispatcher()
    dispatcher.register("hello", hello)
    rpc = JSONRPC(dispatcher)
    ws = WebsocketMockup()
    t = asyncio.create_task(rpc.wsloop(cast(web.WebSocketResponse, ws)))
    await ws.read.put(
        '{"jsonrpc":"2.0", "method":"hello", "id": 1, "params": ["world"]}'
    )
    resp = json.loads(await ws.wrote.get())
    print(resp)
    assert resp["result"] == "Hello world"
    assert resp["id"] == 1
    assert t.cancel()
