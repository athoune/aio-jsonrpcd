import asyncio
import json
from typing import Any, cast

import pytest
from aiohttp import WSMsgType, web
from aiohttp._websocket.models import WSMessage

from jsonrpcd.rpc.app_test import OutTest

from ..rpc.app import App, Bounced, Request, Session
from .web import JsonRpcWebHandler


class WebsocketMockup:
    def __init__(self) -> None:
        self._responses = asyncio.Queue[str]()
        self._requests = asyncio.Queue[str]()
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        return WSMessage(type=WSMsgType.TEXT, data=await self.read(), extra=None)

    async def write(self, txt: str):
        "Send response."
        await self._responses.put(txt)

    async def send_json(self, data: Any):
        await self._responses.put(json.dumps(data))

    async def read(self) -> str:
        "Next request."
        return await self._requests.get()

    async def get(self) -> str:
        "Next response."
        return await self._responses.get()

    async def put(self, txt: str):
        "Add request."
        return await self._requests.put(txt)

    async def close(self):
        self.closed = True

    def dump(self) -> str:
        return (
            f"requests: {self._requests.qsize()} responses: {self._responses.qsize()}"
        )


class AsyncInfiniteLoop:
    def __aiter__(self):
        return self

    async def __anext__(self):
        return await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def testRaise():
    loop = AsyncInfiniteLoop()
    ok = False
    async for a in loop:
        try:
            raise Bounced("test")
        except Bounced as e:
            print(e)
        finally:
            ok = True
        break
    assert ok


@pytest.mark.asyncio
async def testWebsocketMockup():
    ws = WebsocketMockup()
    await ws.put("a")
    assert "a" == await ws.read()
    await ws.write("b")
    assert "b" == await ws.get()


@pytest.fixture
def app():
    _app = App()

    @_app.handler("hello")
    async def hello(request: Request) -> str:
        return f"Hello {cast(list[str], request.params)[0]}"

    return _app


@pytest.mark.asyncio
async def testBadJson(app: App):
    web_handler = JsonRpcWebHandler(app)
    out = OutTest()
    session = Session(out)
    ws = WebsocketMockup()
    t = asyncio.create_task(
        web_handler._json_rpc_loop(session, cast(web.WebSocketResponse, ws))
    )

    # The JSON is malformed
    await ws.put(
        """{
        "jsonrpc":"2.0",
        "method":"hello",
        "id": 1,
        "params": ["world"
        }"""
    )
    debug = ws.dump()
    print(debug)
    resp: dict[str, Any] = json.loads(await ws._responses.get())
    debug = ws.dump()
    print(debug)
    assert "error" in resp
    assert t.done


@pytest.mark.asyncio
async def testBadMethod(app: App):
    web_handler = JsonRpcWebHandler(app)
    out = OutTest()
    session = Session(out)
    ws = WebsocketMockup()
    t = asyncio.create_task(
        web_handler._json_rpc_loop(session, cast(web.WebSocketResponse, ws))
    )

    await ws.put(
        """{
            "jsonrpc":"2.0",
            "method":"authenticate",
            "id": 1,
            "params": ["Bob", "Sinclar"]}"""
    )
    resp: dict[str, Any] = json.loads(await ws._responses.get())
    # The method is not known by the application
    assert "error" in resp
    assert t.done


@pytest.mark.asyncio
async def testAuthenticate(app: App):
    web_handler = JsonRpcWebHandler(app)

    @app.handler("authenticate", public=True)
    async def _authenticate(request: Request):
        # some auth
        request.session.authenticated = True

    out = OutTest()
    session = Session(out)
    ws = WebsocketMockup()
    t = asyncio.create_task(
        web_handler._json_rpc_loop(session, cast(web.WebSocketResponse, ws))
    )

    await ws.put(
        """{
            "jsonrpc":"2.0",
            "method":"authenticate",
            "id": 1,
            "params": ["Bob", "Sinclar"]}"""
    )
    resp: dict[str, Any] = json.loads(await ws._responses.get())

    assert resp["result"] is None

    await ws.put(
        """{
        "jsonrpc":"2.0",
        "method":"hello",
        "id": 1,
        "params": ["world"]
        }"""
    )
    resp: dict[str, Any] = json.loads(await ws._responses.get())
    print(resp)
    assert resp["result"] == "Hello world"
    assert resp["id"] == 1
    assert t.cancel()
