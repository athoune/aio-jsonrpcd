import asyncio
import jwt
import pytest

from ..rpc.app import App, Session, User
from ..rpc.app_test import OutTest
from .club import Club, all


@pytest.mark.asyncio
async def testClub():
    app = App()
    club = Club(app)
    club.register_room("harry", "potter")

    app.handler("authenticate", public=True)(club.authenticate)
    app.namespace("all")(all)

    outs = dict[str, OutTest]()
    users = dict[str, User]()
    sessions = dict[str, Session]()
    names = ["hermione", "ron", "lucius"]

    for name in names:
        token = jwt.encode({"login": name}, "potter", algorithm="HS256")

        out = OutTest()
        outs[name] = out
        session = Session(out)
        sessions[name] = session

        await app._handle(
            session,
            dict(method="authenticate", id=17, params=dict(room="harry", token=token)),
        )
        resp = out.messages.pop()
        assert resp["result"] is None

        assert name in app._users
        user = session.user
        assert user is not None
        users[name] = user
        assert session.authenticated
        assert session.room is not None
        assert session.room == club._rooms["harry"]
    await app._handle(
        sessions[names[0]],
        dict(jsonrpc="2.0", method="all.hello", params=["Everyone"]),
    )
    await asyncio.sleep(0.1)  # [FIXME] do real sync
    for name in names:
        if name == names[0]:  # The emitter
            assert len(outs[name].messages) == 0
            continue
        assert len(outs[name].messages) == 1
        message = outs[name].messages[0]
        assert message["method"] == "all.hello"
        print(name, outs[name].messages)
