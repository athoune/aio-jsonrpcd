from typing import Any, cast
import logging

import jwt

from ..rpc.app import App, Request, Room, User, Session, Message


logger = logging.getLogger(__name__)


async def hello(request: Request) -> str:
    return f"Hello {cast(list[str], request.params)[0]}"


async def ping() -> str:
    logging.info("ping")
    return "pong"


async def all(request: Request):
    # Broadcast handler
    assert request.user is not None
    await request.session.room.broadcast(request.as_dict(), but=request.user.login)


class Club:
    def __init__(self, app: App):
        self._app = app
        self._app.handler("hello", public=True)(hello)
        self._app.function("ping", public=True)(ping)
        self._app.namespace("all")(all)
        self._app.handler("authenticate", public=True)(self.authenticate)
        self._app.on_close = close_session

        self._rooms = dict[str, Room]()
        self._secrets = dict[str, str]()

    def register_room(self, name: str, secret: str):
        "Create a new room, with its secret."
        room = Room(self._app)
        self._rooms[name] = room
        self._secrets[name] = secret

    async def authenticate(self, request: Request) -> dict[str, Any]:
        params = cast(dict[str, str], request.params)
        room_name = params["room"]

        room: Room = self._rooms[room_name]
        secret: str = self._secrets[room_name]
        meta: dict[str, Any] = jwt.decode(params["token"], secret, algorithms=["HS256"])

        user = User(meta["login"])
        user["meta"] = meta
        room.adduser(user, request.session)
        request.session.user = user
        request.session.authenticate()
        logger.info(f"authenticate: {user.login}")
        logger.info(f"room '{room_name}' has {len(room)} users.")
        assert request.room is not None
        return dict(me=meta["login"], users=list(request.room.users.keys()))


def close_session(session: Session):
    # Callback for jsonrpcd.ws.web.JsonRpcWebHandler
    session.close()
