from typing import cast, Any
import pytest
from aiohttp import web, WSMsgType
import asyncio
from .json_rpc import JsonRpcDispatcher
from aiohttp._websocket.models import WSMessage
import json
from .web import jsonRpcWebsocketLoop, websocketJsonRpcIterator, Bounce
from .auth import none_auth
from .app import User, Bounced


async def app_test():
    routes = web.RouteTableDef()
    app = web.Application()

    @routes.get("/rpc")
    async def testWS(request: web.Request):
        return web.Response()  # FIXME

    app.add_routes(routes)
    web.run_app(app)


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


@pytest.mark.asyncio
async def testJsonWsIterator():
    ws = WebsocketMockup()

    async def _client():
        await ws.put(
            '{"jsonrpc":"2.0", "method":"hello", "id": 1, "params": ["world"]}'
        )
        await ws.put("some garbage")

    t = asyncio.create_task(_client())
    one_message = False
    one_json_error = False

    try:
        async for message in websocketJsonRpcIterator(cast(web.WebSocketResponse, ws)):
            assert message["id"] == 1
            one_message = True
    except json.JSONDecodeError:
        one_json_error = True

    assert one_message
    assert one_json_error
    assert t.done


@pytest.mark.asyncio
async def testBounce():
    b = Bounce(none_auth, None)
    alice = User()
    assert not alice.authenticated
    assert await b(alice, dict(method="authenticate", params=("Alice", 42)))
    assert alice.authenticated
    assert alice.login == "Alice"
    assert not await b(alice, dict(method="authenticate", params=("Alice", 42)))

    bob = User()
    assert not bob.authenticated
    bounced = False
    try:
        await b(bob, dict(method="hello", params="world"))
    except Bounced:
        bounced = True
    assert bounced
    assert not bob.authenticated


@pytest.mark.asyncio
async def testJsonRpcWebsocketLoop():
    ws = WebsocketMockup()
    dispatcher = JsonRpcDispatcher()

    t = asyncio.create_task(
        jsonRpcWebsocketLoop(
            dispatcher, Bounce(none_auth, None), cast(web.WebSocketResponse, ws)
        )
    )

    await ws.put('{"jsonrpc":"2.0", "method":"hello", "id": 1, "params": ["world"]}')
    message = json.loads(await ws.get())
    print("message:", message)
    assert message["result"] == "hello world"

    assert t.cancelled


@pytest.mark.asyncio
async def testPlop():
    async def hello(txt: str) -> str:
        return f"Hello {txt}"

    dispatcher = JsonRpcDispatcher()
    dispatcher.register("hello", hello)
    ws = WebsocketMockup()
    t = asyncio.create_task(
        jsonRpcWebsocketLoop(dispatcher, none_auth, cast(web.WebSocketResponse, ws))
    )

    def dump(task: asyncio.Task):
        print(task)

    t.add_done_callback(dump)

    await ws.put('{"jsonrpc":"2.0", "method":"hello", "id": 1, "params": ["world"]}')
    resp: dict[str, Any] = json.loads(await ws._responses.get())
    assert "error" in resp
    assert ws.closed
    assert t.done

    ws = WebsocketMockup()
    t = asyncio.create_task(
        jsonRpcWebsocketLoop(dispatcher, none_auth, cast(web.WebSocketResponse, ws))
    )

    await ws.read.put(
        '{"jsonrpc":"2.0", "method":"authenticate", "id": 1, "params": ["Bob", "Sinclar"]}'
    )
    resp: dict[str, Any] = json.loads(await ws._responses.get())
    print(resp)

    await ws.read.put(
        '{"jsonrpc":"2.0", "method":"hello", "id": 2, "params": ["world"]}'
    )
    resp: dict[str, Any] = json.loads(await ws._responses.get())

    assert resp["result"] == "Hello world"
    assert resp["id"] == 1
    assert t.cancel()
