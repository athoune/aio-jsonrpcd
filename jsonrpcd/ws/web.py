from typing import cast, Any, AsyncGenerator, Callable

from aiohttp.web import WebSocketResponse
from aiohttp import web
import aiohttp

from ..rpc.json_rpc import checkup, JsonRpcRequestException
from ..rpc.tube import AutoTube
from ..rpc.app import App, Session
from ..rpc.dispatcher import MethodNotFoundException


async def websocketJsonRpcIterator(
    ws: web.WebSocketResponse,
) -> AsyncGenerator[dict[str, Any], None]:
    "Yield message as dict, don't bother with websockets or JSON details."
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    message: dict = msg.json()
                except Exception as e:
                    response = dict(
                        jsonrpc="2.0",
                        id=None,
                        error=dict(code=-32700, message="Parse error", data=str(e)),
                    )
                    await ws.send_json(response)
                    continue
                try:
                    checkup(message)
                except JsonRpcRequestException as e:
                    response = dict(
                        jsonrpc="2.0",
                        error=dict(code=-32600, message="Invalid Request", data=str(e)),
                    )
                    await ws.send_json(response)
                    continue
                yield message
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print(
                    "ws connection closed with exception %s" % ws.exception(),
                )
                raise ws.exception()
            else:
                raise Exception("Unhandled websocket message type:", msg.type)
    except Exception as e:
        response = dict(
            jsonrpc="2.0",
            error=dict(code=-32603, message="Internal error", data=str(e)),
        )
        await ws.send_json(response)
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


class JsonRpcSession:
    """Jsonrcp Session.
    The client is connected and can start sending requests (and receiving responses).
    """

    def __init__(self, app: App, session: Session, ws: WebSocketResponse) -> None:
        self.app = app
        self.session = session
        self.ws = ws

    async def __call__(self, message: dict[str, Any]):
        """Execute a request.
        The execution is detached, and return nothing.
        The call receive a Request and answer with a Response, through the websocket."""
        id_ = message.get("id")
        result: Any
        try:
            result = await self.app._handle(self.session, message)
        except MethodNotFoundException as e:
            response = dict(
                id=id_,
                jsonrpc=message["jsonrpc"],
                error=dict(code=-32601, message="Method not found", data=str(e)),
            )
            await self.ws.send_json(response)
        except Exception as e:
            # Lots of exception can be caught here
            # it can be hard to debug without stack trace.
            print("json rpc session error:", e)
            if id_ is None:
                """…the Client would not be aware of any errors
                (like e.g. "Invalid params","Internal error")
                """
                print(f"jsonrpcsession error : {e}")
                # the client have to read logs to discover th exception
            else:
                response = dict(
                    id=id_,
                    jsonrpc=message["jsonrpc"],
                    error=dict(code=-32000, message=str(e)),
                )
                await self.ws.send_json(response)
        else:
            if id_ is not None:
                response = dict(id=id_, result=result, jsonrpc=message["jsonrpc"])
                await self.ws.send_json(response)
            elif result is not None:
                pass  # [FIXME] notification returns nothing


class JsonRpcWebHandler:
    """aiohttp web handler managing the websocket connection."""

    _app: App

    def __init__(self, app=App, init: None | Callable = None):
        """Init async function is called in the websocket connection step.
        It is used to add information to the session."""
        self._app: App = app
        self._init = init

    async def __call__(self, request: web.Request) -> web.Response:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        session = Session(ws.send_json)
        session["http-request"] = request
        if self._init is not None:
            await self._init(session)
        await self._json_rpc_loop(session, ws)
        return cast(web.Response, ws)

    async def _json_rpc_loop(self, session: Session, ws: web.WebSocketResponse) -> None:
        # No HTTP in this context, just a websocket
        jsonrpc_session = JsonRpcSession(self._app, session, ws)

        _tube = AutoTube()

        async for message in websocketJsonRpcIterator(ws):
            if "method" in message:
                _tube.put(jsonrpc_session(message))
            elif "result" in message:
                pass  # FIXME
            else:
                raise Exception(f"strange message : {message}")
        await ws.close()
