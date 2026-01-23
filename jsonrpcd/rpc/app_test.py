from typing import Any, cast

import pytest

from .app import App, Bounced, Request, Room, Session, User, _anonymous


class OutTest:
    def __init__(self) -> None:
        self.messages = list[dict[str, Any]]()

    async def __call__(self, message: dict[str, Any]):
        self.messages.append(message)

    def __len__(self) -> int:
        return len(self.messages)


def testStore():
    app = App()
    app["db"] = 42
    app["name"] = "My App"

    assert len(app) == 2
    assert set(key for key in app) == {"name", "db"}
    assert "name" in app
    del app["name"]
    assert "name" not in app


@pytest.mark.asyncio
async def testRoom():
    app = App()

    @app.handler("hello", public=True)
    async def _hello(request: Request) -> str:
        return f"Hello {cast(list, request.params)[0]}"

    room = Room(app)
    alice = User("Alice")
    bob = User("Bob")
    room.adduser(alice)
    room.adduser(bob)

    out_a = OutTest()
    out_b = OutTest()
    Session(out_a, alice)
    assert len(alice.sessions) == 1
    Session(out_b, bob)
    await room.broadcast(dict(method="hello", params=["World"]))
    assert len(out_a) == 1
    assert len(out_b) == 1
    assert out_a.messages[0] == dict(method="hello", params=["World"])
    assert out_b.messages[0] == dict(method="hello", params=["World"])


@pytest.mark.asyncio
async def testApp():
    app = App()
    app.add_user(User("alice"))

    @app.handler("hello")
    async def _hello(request: Request) -> str:
        return f"Hello {cast(list, request.params)[0]}"

    out = OutTest()
    session = Session(out)

    with pytest.raises(Bounced):
        await app._handle(session, dict(method="hello", params=["World"]))

    @app.handler("authenticate", public=True)
    async def _authenticate(request: Request) -> None:
        assert request.app is not None
        user = request.app.find_user(cast(str, cast(list, request.params)[0]))
        # use token to authenticate
        request.session.authenticate()
        session.user = user

    await app._handle(
        session, dict(method="authenticate", params=["alice", "some token"])
    )
    resp = await app._handle(session, dict(method="hello", params=["World"]))
    assert resp == "Hello World"


@pytest.mark.asyncio
async def testNamespace():
    app = App()
    app.add_user(User("alice"))
    out = OutTest()
    session = Session(out)

    @app.namespace("test", public=True)
    async def _ns(request: Request) -> str:
        ns, method = request.method.split(".")
        return f"ns: {ns} method:{method}"

    resp = await app._handle(session, dict(method="test.hello", params=["World"]))
    assert resp == "ns: test method:hello"


@pytest.mark.asyncio
async def testFunction():
    app = App()
    app.add_user(User("alice"))
    out = OutTest()
    session = Session(out)

    @app.function("hello", public=True)
    async def _function(name: str) -> str:
        return f"Hello {name}"

    resp = await app._handle(session, dict(method="hello", params=["World"]))
    assert resp == "Hello World"


@pytest.mark.asyncio
async def testAnonymous():
    out = OutTest()
    session = Session(out)
    tests = list()  # I need a pointer, not a value

    async def _ano(r: Request) -> None:
        tests.append(1)

    app = App()
    request = Request.from_json(app, session, dict(method="whatever"))
    assert not request._anonymous

    await _anonymous(_ano)(request)
    assert request._anonymous

    assert len(tests)
