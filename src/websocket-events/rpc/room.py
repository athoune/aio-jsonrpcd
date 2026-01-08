from typing import Any

from .json_rpc import JsonRpcDispatcher


class Session:
    _user: "User"

    async def request(self, msg: dict[str, Any]) -> Any:
        return await self._user.request(msg)


class User:
    _sessions: list[Session]
    _dispatcher: JsonRpcDispatcher

    def __init__(self) -> None:
        self._sessions = list[Session]()

    def session(self) -> Session:
        session = Session()
        session._user = self
        self._sessions.append(session)
        return session

    async def request(self, msg: dict[str, Any]) -> Any:
        response = await self._dispatcher(msg)
        print(self, msg, response)


class Room:
    _users: dict[Any, User]

    def __init__(self) -> None:
        self._users = dict[Any, User]()

    def __delitem__(self, key: Any):
        del (self._users, key)

    def __setitem__(self, key: Any, value: User):
        self._users[key] = value

    async def broadcast(self, msg: dict[str, Any]):
        for user in self._users.values():
            for session in user._sessions:
                await session.request(msg)
