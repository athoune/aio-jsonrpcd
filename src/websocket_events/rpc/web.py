from aiohttp import web
import aiohttp
from typing import cast, Any, Callable, AsyncGenerator, Awaitable
import json


from .tube import AutoTube
from .app import Bounced, User


async def websocketJsonRpcIterator(
    ws: web.WebSocketResponse,
) -> AsyncGenerator[dict[str, Any], None]:
    "Yield message as dict, don't bother with websockets or JSON details."
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                message: dict = msg.json()
                yield message
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print(
                    "ws connection closed with exception %s" % ws.exception(),
                )
                raise ws.exception()
            else:
                raise Exception("Unhandled websocket message type:", msg.type)
    finally:
        if not ws.closed:
            await ws.close()


class JsonRpcUserException(Exception):
    def __init__(self, error: dict[str, Any], id: Any | None = None) -> None:
        self._error = error
        self._id = id
        super().__init__(id, error)

    def message(self) -> dict[str, Any]:
        msg = dict(jsonrpc="2.0", error=self._error)
        if self._id is not None:
            msg["id"] = self._id
        return msg


class Bounce:
    def __init__(
        self,
        auth_method: Callable[..., Awaitable[tuple[User, str, Any]]],
        on_auth: Callable[[User], None] | None = None,
    ):
        self.auth_method = auth_method
        self.on_auth = on_auth

    async def __call__(self, user: User, message: dict[str, Any]) -> bool:
        if not user.authenticated:
            if message["method"] != "authenticate":
                raise Bounced(user)
            await self.auth_method(user, *message["params"])
            if self.on_auth is not None:
                self.on_auth(user)
            return True
        else:
            return False


class JsonRpsWebHandler:
    """aiohttp web handler managing the websocket connection."""

    def __init__(self, dispatcher: JsonRpcDispatcher, bounce: Bounce):
        self.dispatcher: JsonRpcDispatcher = dispatcher
        self.bounce = bounce

    async def rpc_handler(self, request: web.Request) -> web.Response:
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        user = User()
        await self.jsonRpcWebsocketLoop(ws, user)

        return cast(web.Response, ws)

    async def jsonRpcWebsocketLoop(self, ws: web.WebSocketResponse, user: User):
        """Handles jsonrpc exchanges in a websocket connection."""

        async def _writeResponse(response: dict[str, Any]):
            await ws.write(json.dumps(response).encode())

        _tube = AutoTube(_writeResponse)

        try:
            async for message in websocketJsonRpcIterator(ws):
                if "method" in message:
                    try:
                        if await self.bounce(user, message):
                            continue
                        _tube.put(self.dispatcher(message))
                    except Bounced:
                        id_: int | None = None
                        if "id" in message:
                            id_ = message["id"]
                        raise JsonRpcUserException(
                            dict(code=-32000, message="Unauthenticated"), id_
                        )
                elif "result" in message:
                    pass  # FIXME
                else:
                    raise Exception(f"strange message : {message}")
        except JsonRpcUserException as e:
            await _writeResponse(e.message())
        finally:
            await ws.close()
