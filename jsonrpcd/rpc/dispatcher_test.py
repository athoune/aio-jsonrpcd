from .dispatcher import Dispatcher
from typing import Any, Callable, Awaitable, cast, List
from .app import Request, App, Session
import pytest
from .app_test import OutTest


@pytest.mark.asyncio
async def test_dispatcher():
    async def _hello(request: Request) -> str:
        return f"Hello {cast(List[str], request.params)[0]}"

    async def _ns(request: Request) -> str:
        print(request.method, type(request.method))
        ns, method = request.method.split(".")
        return f"My namespace is {ns} with method {method}"

    app = App()
    out = OutTest()
    session = Session(out)

    d = Dispatcher[Callable[..., Awaitable[tuple[Request, dict[str, Any]]]]]()
    d.put_handler("hello", _hello)
    d.put_namespace("test", _ns)

    assert (
        await d["test.plop"](
            Request.from_json(app, session, dict(method="test.plop", params=["beuha"]))
        )
        == "My namespace is test with method plop"
    )
    assert (
        await d["hello"](
            Request.from_json(app, session, dict(method="hello", params=["World"]))
        )
        == "Hello World"
    )
