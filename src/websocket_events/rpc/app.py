from typing import Any, Callable, Awaitable, Coroutine, Protocol, AsyncGenerator


MessageIn = AsyncGenerator[dict[str, Any], None]
MessageOut = Callable[[dict[str, Any]], Awaitable[None]]


class Bounced(Exception):
    "Authenticate first."

    pass


class Session:
    _values: dict
    _user: "User | None"
    authenticated: bool
    _out: MessageOut

    def __init__(
        self,
        message_out: MessageOut,
        user: "User | None" = None,
    ) -> None:
        self._values = dict()
        self.authenticated = False
        if user is None:
            self._user = None
        else:
            self.user = user
        self._out = message_out

    @property
    def user(self) -> "User":
        return self._user

    @user.setter
    def user(self, usr):
        usr.sessions.add(self)
        self._user = usr

    def __setitem__(self, key, value):
        self._values[key] = value

    def __getitem__(self, key) -> Any:
        return self._values[key]

    def authenticate(self):
        self.authenticated = True

    # FIXME a getter and a setter that does nothing, why ?
    @property
    def user(self) -> "User | None":
        return self._user

    @user.setter
    def user(self, usr: "User"):
        usr.sessions.add(self)
        self._user = usr

    async def send_message(self, message: dict[str, Any]):
        """
        Write a message to the wire, something like a websocket.
        Used when sending events to the client."""
        await self._out(message)


class User:
    _room: "Room"
    sessions: set[Session]
    context: dict[str, Any]
    login: str

    def __init__(self, login: str) -> None:
        self.sessions = set[Session]()
        self.context = dict[str, Any]()
        self.login = login

    @property
    def app(self) -> "App":
        return self._room.app

    @property
    def room(self) -> "Room":
        return self._room


class Room:
    _app: "App"
    _users: dict[str, User]

    def __init__(self, app: "App") -> None:
        self._app = app
        self._users = dict[str, User]()

    def adduser(self, user: User):
        self._users[user.login] = User

    @property
    def app(self):
        return self._app

    def __delitem__(self, key: Any):
        del (self._users, key)

    def __setitem__(self, key: Any, value: User):
        self._users[key] = value

    async def broadcast(self, msg: dict[str, Any]):
        for user in self._users.values():
            for session in user.sessions:
                await session.send_message(msg)


class App:
    _handlers: dict[str, Callable[..., Awaitable[tuple["Request", dict[str, Any]]]]]
    _users: dict[str, User]

    def __init__(self) -> None:
        self._handlers = dict()
        self._users = dict()

    def add_user(self, user: User):
        user._app = self
        self._users[user.login] = user

    def find_user(self, login: str) -> User:
        return self._users[login]

    def handler(self, method: str):
        def decorator(function):
            self._handlers[method] = function

        return decorator

    async def _handle(self, session: Session, rpc_request: dict[str, Any]) -> Any:
        request = Request(self, session, rpc_request["method"], rpc_request["params"])
        method = self._handlers[request.method]
        if (
            "_anonymously" not in method.__qualname__
            and not request.session.authenticated
        ):  # FIXME introspection seems ugly
            raise Bounced()
        return await method(request)


class Request:
    _session: Session
    _app: App
    method: str
    params: dict[str, Any] | list[Any]
    id_: Any
    _anonymous: bool

    def __init__(
        self,
        app: App,
        session: Session,
        method: str,
        params: dict[str, Any] | list[Any],
    ) -> None:
        self._app = app
        self._session = session
        self.method = method
        self.params = params
        self._anonymous = False

    @property
    def session(self) -> Session:
        return self._session

    @property
    def user(self) -> User | None:
        return self._session._user

    @property
    def room(self) -> Room | None:
        if self._session._user is None:
            return None
        return self._session._user._room

    @property
    def app(self) -> App:
        return self._app


def anonymous(function: Callable) -> Callable:
    # It does nothing, just tagging the function
    async def _anonymously(request: Request) -> Any:
        request._anonymous = True
        return await function(request)

    return _anonymously
