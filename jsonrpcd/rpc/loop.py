import logging
from asyncio import Event
from typing import Any, AsyncGenerator, Awaitable, Callable, Coroutine

from .tube import AutoTube

logger = logging.getLogger(__name__)


MessageOut = Callable[[dict[str, Any]], Awaitable[None]]
Message = dict[str, Any]


class Response:
    event: Event
    response: Any

    def __init__(self):
        self.event = Event()
        self.response = None


class Loop:
    _id: int
    _out: MessageOut
    _requests: dict[int, Response]
    _handle: Callable[[Message], Coroutine]

    def __init__(self, handle: Callable[[Message], Coroutine], out: MessageOut):
        self._id = 0
        self._handle = handle
        self._out = out
        self._requests = dict[int, Response]()

    async def send_message(self, message: Message):
        """
        Write a message to the wire, something like a websocket.
        Used when sending events to the client."""
        await self._out(message)

    async def send_request(self, method, params) -> Any:
        await self.send_message(
            Message(jsonrpc=2.0, id=self._id, method=method, params=params)
        )
        response = Response()
        self._requests[self._id] = response
        await response.event.wait()
        self._id += 1
        return response.response

    async def send_event(self, method, params):
        await self.send_message(Message(jsonrpc=2.0, method=method, params=params))

    async def _wrap_response(self, id: int | None, action: Coroutine):
        try:
            resp: Any = await action
        except Exception as e:
            if id is None:  # It's an event
                logger.error(e)
            else:
                await self.send_message(
                    dict(
                        jsonrpc="2.0",
                        id=id,
                        error=dict(code=-32700, message="Method error", data=str(e)),
                    )
                )
        else:
            if id is not None:
                await self.send_message(dict(jsonrpc="2.0", id=id, result=resp))

    async def loop(self, messages: AsyncGenerator[Message, None]):
        _tube = AutoTube()
        async for message in messages:
            if "method" in message:
                _tube.put(self._wrap_response(message.get("id"), self._handle(message)))
            elif "result" in message:
                response = self._requests[message["id"]]
                response.response = message["result"]
                response.event.set()
            else:
                raise Exception(f"Wrong message format: {message}")
