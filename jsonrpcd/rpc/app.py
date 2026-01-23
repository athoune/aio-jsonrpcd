import json
import logging
from typing import Any, AsyncGenerator, Awaitable, Callable, MutableMapping
import traceback
import sys

from .dispatcher import Dispatcher, MethodNotFoundException

MessageIn = AsyncGenerator[dict[str, Any], None]
MessageOut = Callable[[dict[str, Any]], Awaitable[None]]

logger = logging.getLogger(__name__)


class Bounced(Exception):
    "Authenticate first."

    pass


class Store(MutableMapping[str, Any]):
    def __init__(self) -> None:
        super().__init__()
        self._store = dict[str, Any]()

    def __iter__(self):
        return iter(self._store)

    def __len__(self) -> int:
        return len(self._store)

    def __delitem__(self, key: str) -> None:
        del self._store[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._store[key] = value

    def __getitem__(self, key: str, /) -> Any:
        return self._store[key]

    def __hash__(self) -> int:
        return id(self)


class Session(Store):
    """Websocket Session.
    Client connects and establish a connection."""

    _user: "User | None"
    authenticated: bool
    _out: MessageOut
    _room: "Room | None"

    def __init__(
        self,
        message_out: MessageOut,
        user: "User | None" = None,
    ) -> None:
        super().__init__()
        self.authenticated = False
        if user is None:
            self._user = None
        else:
            self.user = user
        self._out = message_out
        self._room = None

    @property
    def user(self) -> "User | None":
        return self._user

    @user.setter
    def user(self, usr):
        usr.sessions.add(self)
        self._user = usr

    @property
    def room(self) -> "Room":
        assert self._room is not None
        return self._room

    def authenticate(self):
        self.authenticated = True

    async def send_message(self, message: dict[str, Any]):
        """
        Write a message to the wire, something like a websocket.
        Used when sending events to the client."""
        await self._out(message)

    def close(self):
        assert self.user is not None
        self.user.close_session(self)
        self.authenticated = False
        logger.info(f"session closed: {self.user.login}")

    async def unicast(self, message: dict[str, Any]):
        raise NotImplementedError()


class User(Store):
    _room: "Room"
    sessions: set[Session]
    context: dict[str, Any]
    login: str

    def __init__(self, login: str) -> None:
        super().__init__()
        self.sessions = set[Session]()
        self.context = dict[str, Any]()
        self.login = login

    @property
    def app(self) -> "App":
        return self._room.app

    @property
    def room(self) -> "Room":
        return self._room

    def close_session(self, session: Session):
        self.sessions.remove(session)
        if len(self.sessions) == 0:
            # user leaves the room
            del self._room.users[self.login]
            logger.info(f"User {self.login} leaves the room")

    async def unicast(self, message: dict[str, Any]):
        for session in self.sessions:
            # FIXME handle function, not just event
            await session.unicast(message)


class Room(Store):
    _app: "App"
    _users: dict[str, User]

    def __init__(self, app: "App") -> None:
        super().__init__()
        self._app = app
        self._users = dict[str, User]()

    def adduser(self, user: User, session: Session | None = None):
        self._users[user.login] = user
        self._app._users[user.login] = user
        if session is not None:
            session._room = self
        user._room = self
        logger.info(f"User {user.login} added to the room")

    @property
    def users(self) -> dict[str, User]:
        return self._users

    @property
    def app(self):
        return self._app

    async def broadcast(self, message: dict[str, Any], but: str | None = None):
        assert message.get("id") is None  # it's an event
        users = set[str]()
        for user in self._users.values():
            if user.login == but:
                continue
            users.add(user.login)
            for session in user.sessions:
                await session.send_message(message)
        logger.info(f"Broadcast '{message['method']}' to {', '.join(users)}")

    def __len__(self) -> int:
        return len(self._users)


class App(Store):
    """json-rpc application, the top of the hierarchy.
    App has Users and registered Methods.
    """

    _handlers: Dispatcher[Callable[["Request"], Awaitable[Any]]]
    _users: dict[str, User]

    def __init__(self) -> None:
        super().__init__()
        self._handlers = Dispatcher[Callable[["Request"], Awaitable[Any]]]()
        self._users = dict()

    def add_user(self, user: User):
        self._users[user.login] = user

    def find_user(self, login: str) -> User:
        return self._users[login]

    def handler(self, method: str, public: bool = False):
        "Decorator appending an handler to the application"

        def decorator(
            function: Callable[["Request"], Awaitable[Any]],
        ) -> None:
            if public:
                self._handlers.put_handler(method, _anonymous(function))
            else:
                self._handlers.put_handler(method, function)

        return decorator

    def namespace(self, ns: str, public: bool = False):
        "Decorator appending an namespace to the application"

        def decorator(function: Callable[["Request"], Awaitable[Any]]) -> None:
            if public:
                self._handlers.put_namespace(ns, _anonymous(function))
            else:
                self._handlers.put_namespace(ns, function)

        return decorator

    def function(self, method: str, public: bool = False):
        "Decorator appending an namespace to the application"

        def handler(function: Callable):
            async def _f(request: Request):
                if isinstance(request.params, dict):
                    return await function(**request.params)
                else:
                    return await function(*request.params)

            if public:
                self._handlers.put_handler(method, _anonymous(_f))
            else:
                self._handlers.put_handler(method, _f)
            return _f

        return handler

    async def _handle(self, session: Session, rpc_request: dict[str, Any]) -> None:
        request: Request = Request.from_json(self, session, rpc_request)
        try:
            method: Callable[[Request], Awaitable[Any]] = self._handlers[request.method]
            if (
                "_anonymously" not in method.__qualname__  # type: ignore [FIXME] function has a __qualname__, what about hand crafted __call__ ?
                and not request.session.authenticated
            ):  # FIXME introspection seems ugly
                raise Bounced(f"'{request.method}' method needs authentication")
            logger.info(
                f"method call: {rpc_request['method']}",
                extra=dict(request=rpc_request, session=session),
            )
            result: Any
            result = await method(request)
        except MethodNotFoundException as e:
            response = dict(
                id=request.id_,
                jsonrpc=request.jsonrpc,
                error=dict(code=-32601, message="Method not found", data=str(e)),
            )
            await session._out(response)
        except Exception as e:
            logger.info("method error", extra=dict(stack=sys.exc_info()))
            # Lots of exception can be caught here
            # it can be hard to debug without stack trace.
            print("json rpc session error:", e, sys.exc_info())
            traceback.print_exception(e)
            if request.id_ is None:
                """…the Client would not be aware of any errors
                (like e.g. "Invalid params","Internal error")
                """
                print(f"jsonrpcsession error : {e}")
                # the client have to read logs to discover th exception
            else:
                response = dict(
                    id=request.id_,
                    jsonrpc=request.jsonrpc,
                    error=dict(code=-32000, message=str(e)),
                )
                await session._out(response)
        else:
            if request.id_ is not None:
                response = dict(id=request.id_, result=result, jsonrpc=request.jsonrpc)
                await session._out(response)
            elif result is not None:
                pass  # [FIXME] notification returns nothing


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
        id_: Any,
        method: str,
        params: dict[str, Any] | list[Any],
    ) -> None:
        self._app = app
        self._session = session
        self.id_ = id_
        self.method = method
        self.params = params
        self._anonymous = False
        self._jsonrpc = "2.0"  # Harcoded, this will never change

    @staticmethod
    def from_json(app: App, session: Session, message: dict[str, Any]) -> "Request":
        return Request(
            app,
            session,
            message.get("id"),
            message["method"],
            message.get("params", []),
        )

    def as_dict(self) -> dict[str, Any]:
        return dict(id=self.id_, method=self.method, params=self.params)

    def as_json(self) -> str:
        return json.dumps(self.as_dict())

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

    @property
    def jsonrpc(self) -> str:
        return self._jsonrpc


def _anonymous(
    function: Callable[[Request], Awaitable[Any]],
) -> Callable[[Request], Awaitable[Any]]:
    # It does nothing, just tagging the function
    async def _anonymously(request: Request) -> Any:
        request._anonymous = True
        return await function(request)

    return _anonymously
