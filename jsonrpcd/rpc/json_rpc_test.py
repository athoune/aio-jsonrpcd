from .json_rpc import jsonrpc_wrapper
import pytest
from typing import Callable


@pytest.mark.asyncio
async def test_jsonize():
    async def _test(name: str, age) -> dict:
        return dict(age=age, name=name)

    j = jsonrpc_wrapper(_test)
    a = await j(dict(params=["Simone", 42], id=1, method="_test", jsonrpc="2.0"))
    assert a["id"] == 1
    assert a["result"] == dict(name="Simone", age=42)

    async def _error() -> int | float:
        return 1 / 0

    j2: Callable = jsonrpc_wrapper(_error)
    b: dict = await j2(dict(jsonrpc="2.0", id=2))
    assert b["id"] == 2
    assert b["error"]["code"] == -32000
    assert b["error"]["message"] == "division by zero"
