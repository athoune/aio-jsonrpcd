from aiohttp import web
import aiohttp
from aiohttp.client_exceptions import ClientConnectionResetError
from redis import asyncio as aioredis
import asyncio
import json
import os
from .crud import CRUD
import uuid

from aiohttp_sse import sse_response


class TerminateTaskGroup(Exception):
    """Exception raised to terminate a task group."""


PLAYERS = "players"


routes = web.RouteTableDef()
app = web.Application()
app[PLAYERS] = set()

redis: aioredis.Redis = aioredis.from_url("redis://localhost", decode_responses=True)
here = os.path.dirname(__file__)
lazy_delete: str = open(f"{here}/lazy_delete.lua", "r").read()
crud: CRUD = CRUD("redis://localhost")


@routes.get("/")
async def home(request):
    return web.Response(text="Master of events.")


@routes.get("/{db}")
async def db(request):
    key: str = request.match_info["db"].encode("utf8")
    return web.json_response(await crud.all(key))


@routes.put("/{db}")
async def db_mput(request):
    key: str = request.match_info["db"]
    values: dict = await request.json()
    await crud.put_dict(key, values)
    return web.Response()


@routes.delete("/{db}/{key}")
async def db_delete(request):
    db: str = request.match_info["db"]
    key: str = request.match_info["key"]

    lazy = await crud.delete(db, key)
    print("lazy:", lazy)
    return web.Response()


@routes.get("/sub/{db}")
async def subscribe(request):
    key: str = request.match_info["db"]
    id = uuid.uuid1()
    request.app[PLAYERS].add(id)
    print(id, ", SSE subscriber, joins the server", request.app[PLAYERS])
    sub = crud.subscribe(key)

    async def loop():
        async with sse_response(request) as resp:
            while resp.is_connected():
                async for msg in sub:
                    if resp.is_connected():
                        await resp.send(json.dumps(msg))
                    else:
                        print("disconnected")
                        return

    def done(future):
        print(id, ", SSE subscriber, leaves")
        request.app[PLAYERS].remove(id)

    t = asyncio.create_task(loop())
    t.add_done_callback(done)
    await t
    done(None)
    return web.Response()


@routes.get("/ws/{db}")
async def websocket_handler(request):
    db: str = request.match_info["db"]

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    id = uuid.uuid1()
    request.app[PLAYERS].add(id)
    print(id, "joins the server", request.app[PLAYERS])
    await ws.send_json(dict(action="connected", id=str(id)))

    async def sub():
        async for message in crud.subscribe(db, raw=True):
            try:
                await ws.send_str(message)
            except ClientConnectionResetError as e:
                print(id, "websocket sub error:", e)
                # await ws.close()
                raise TerminateTaskGroup()

    async def uplink():
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await crud.put_dict(db, json.loads(msg.data))
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(id, "ws connection closed with exception %s" % ws.exception())
                else:
                    print(id, "WTF ws message:", msg)
        except Exception as e:
            print(id, "uplink error:", type(e), e)
            raise TerminateTaskGroup()

    def done_callback(fut):
        print(id, "disconnects")  # , fut)
        request.app[PLAYERS].remove(id)

    try:
        async with asyncio.TaskGroup() as tg:
            t_sub = tg.create_task(sub())
            t_sub.add_done_callback(done_callback)
            t_uplink = tg.create_task(uplink())
            t_uplink.add_done_callback(done_callback)
    except* TerminateTaskGroup:
        print(id, "leaves")

    print(id, "websocket connection closed")

    return ws


app.add_routes(routes)


def listen():
    web.run_app(app)
