from typing import Any, cast
import logging

import jwt

from ..rpc.app import App, Request, Room, User, Session


logger = logging.getLogger(__name__)


class Club:
    def __init__(self, app: App):
        self._app = app
        self._rooms = dict[str, Room]()
        self._secrets = dict[str, str]()

    def register_room(self, name: str, secret: str):
        "Create a new room, with its secret."
        room = Room(self._app)
        self._rooms[name] = room
        self._secrets[name] = secret

    async def authenticate(self, request: Request):
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


def close_session(session: Session):
    # Callback for jsonrpcd.ws.web.JsonRpcWebHandler
    session.close()


async def all(request: Request):
    # Broadcast handler
    assert request.user is not None
    await request.session.room.broadcast(request.as_dict(), but=request.user.login)
