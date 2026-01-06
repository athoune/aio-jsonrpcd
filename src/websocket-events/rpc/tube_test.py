import pytest
from .json_rpc import jsonrpc_wrapper
from .tube import Tube
from asyncio import sleep


@pytest.mark.asyncio
async def test_tube():
    async def _add(a: int, b: int, wait=0) -> int:
        await sleep(wait)
        return a + b

    w = jsonrpc_wrapper(_add)
    tube = Tube()
    tube.put(w(dict(jsonrpc="2.0", id=1, params=[1, 1, 0.5], method="_add")))
    tube.put(w(dict(jsonrpc="2.0", id=2, params=[41, 1, 0.1], method="_add")))
    i = 1
    results = []
    async for response in tube:
        results.append(response)
        if i == 2:
            break
        i += 1
    assert len(results) == 2
    assert results[0]["result"] == 42
    assert results[1]["result"] == 2
