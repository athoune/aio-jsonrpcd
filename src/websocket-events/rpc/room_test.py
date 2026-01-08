import pytest

from .json_rpc import JsonRpcDispatcher
from .room import Room, User


class TestUser(User):
    name: str

    def __init__(self, name: str, output: list[str]) -> None:
        super().__init__()
        self.name = name
        self._output = output
        self._dispatcher = JsonRpcDispatcher()
        self._dispatcher.register("hello", self.hello)

    async def hello(self, name: str) -> None:
        self._output.append(f"Hello {name} to {self.name}")


@pytest.mark.asyncio
async def testRoom():
    room = Room()
    out = list[str]()
    alice = TestUser("Alice", out)
    bob = TestUser("Bob", out)
    room["alice"] = alice
    room["bob"] = bob
    s_alice = alice.session()
    s_bob = bob.session()
    await room.broadcast(dict(method="hello", params=["World"]))
    assert len(out) == 2
    for line in out:
        assert line.find("World")

    txt = "\n".join(out)
    assert txt.find("Alice")
    assert txt.find("Bob")
