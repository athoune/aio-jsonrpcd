import jwt
import pytest

from ..rpc.app import App, Request, Room, Session, User, anonymous
from ..rpc.app_test import OutTest
from .club import Club


@pytest.mark.asyncio
async def testClub():
    app = App()
    club = Club(app)
    club.register_room("harry", "potter")

    app.handler("authenticate")(anonymous(club.authenticate))

    token = jwt.encode({"login": "hermione"}, "potter", algorithm="HS256")

    out = OutTest()
    session = Session(out)

    resp = await app._handle(
        session,
        dict(method="authenticate", id=17, params=dict(room="harry", token=token)),
    )

    assert resp is None
    assert "hermione" in app._users
    hermione = session.user
    assert hermione is not None
    assert session.authenticated
    assert session.room is not None
    assert session.room == club._rooms["harry"]
