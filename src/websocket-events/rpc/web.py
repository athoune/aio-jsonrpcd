from aiohttp import web
import aiohttp
from typing import cast, Any, Callable
import asyncio
import json

from .json_rpc import Dispatcher


class TerminateTaskGroup(Exception):
    """Exception raised to terminate a task group."""


class JsonRpcWebsocketHandler:
    """Handles jsonrpc in a websocket."""

    def __init__(self, dispatcher: Dispatcher):
        self.dispatcher = dispatcher

    async def push(self):
        raise TerminateTaskGroup()

    async def detached_response(
        self, ws: web.WebSocketResponse, message: dict[str, Any]
    ):
        method: Callable = self.dispatcher[message["method"]]
        print("method", method, type(method))
        response: dict[str, Any] = await method(message)
        await ws.write(json.dumps(response).encode())

    async def pull(self, ws: web.WebSocketResponse):
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        message: dict = msg.json()
                    except Exception as e:
                        error = dict(
                            code=-32700, data=str(e), message="JSON parsing error"
                        )
                        await ws.write(json.dumps(error).encode())
                        continue
                    if "method" in message:
                        asyncio.create_task(self.detached_response(ws, message))
                    elif "result" in message:
                        pass
                    else:
                        raise Exception("")

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(
                        id,
                        "ws connection closed with exception %s" % ws.exception(),
                    )
                else:
                    print(id, "WTF ws message:", msg)
        except Exception as e:
            print(id, "uplink error:", type(e), e)
            raise TerminateTaskGroup()

    def done_callback(self, fut):
        print(id, "disconnects")  # , fut)

    async def wsloop(self, ws: web.WebSocketResponse):
        try:
            async with asyncio.TaskGroup() as tg:
                t_sub = tg.create_task(self.push())
                t_sub.add_done_callback(self.done_callback)
                t_uplink = tg.create_task(self.pull(ws))
                t_uplink.add_done_callback(self.done_callback)
        except* TerminateTaskGroup:
            print(id, "leaves")

        print(id, "websocket connection closed")


class JsonRpsWebHandler:
    def __init__(
        self, ws_handler: JsonRpcWebsocketHandler, dispatcher: Dispatcher | Callable
    ):
        self.ws_handler = ws_handler
        self.dispatcher: Dispatcher | Callable = dispatcher

    async def rpc(self, request: web.Request) -> web.Response:
        if isinstance(Dispatcher, self.dispatcher):  # static
            d: Dispatcher = self.dispatcher
        else:  # dynamic
            d: Dispatcher = self.dispatcher(request)
        loop = JsonRpcWebsocketHandler(d)

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        await loop.wsloop(ws)

        return cast(web.Response, ws)
