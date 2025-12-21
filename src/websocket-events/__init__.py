from aiohttp import web
import aiohttp
from redis import asyncio as aioredis
import asyncio
import json

from aiohttp_sse import sse_response

routes = web.RouteTableDef()
redis: aioredis.Redis = aioredis.from_url("redis://localhost", decode_responses=True)


@routes.get("/")
async def home(request):
    return web.Response(text="Master of events.")


@routes.get("/{db}")
async def db(request):
    key: str = request.match_info["db"].encode("utf8")
    all: dict[str, str] = await redis.hgetall(key)
    return web.json_response(all)


@routes.put("/{db}")
async def db_put(request):
    key: str = request.match_info["db"].encode("utf8")
    values: dict = await request.json()
    print(values)
    async with redis.pipeline(transaction=True) as pipe:
        for k, v in values.items():
            if v is None:
                await pipe.hdel(key, k)
            else:
                await pipe.hset(key, k, json.dumps(v))
        await pipe.publish(key, await request.text())
        await pipe.execute()
    return web.Response()


@routes.get("/sub/{db}")
async def subscribe(request):
    key: str = request.match_info["db"].encode("utf8")
    pubsub = redis.pubsub()
    await pubsub.subscribe(key)
    async with sse_response(request) as resp:
        while resp.is_connected():
            async for response in pubsub.listen():
                if response["type"] == "message":
                    await resp.send(response["data"])
    return resp


@routes.get("/ws/{db}")
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    key: str = request.match_info["db"].encode("utf8")
    pubsub: aioredis.PubSub = redis.pubsub()
    await pubsub.subscribe(key)

    async def sub():
        for response in pubsub.listen():
            message: dict = await pubsub.handle_message(response)
            print(message)
            await ws.send_json(message)

    task = asyncio.create_task(sub())

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == "close":
                await ws.close()
            else:
                await ws.send_str(msg.data + "/answer")
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print("ws connection closed with exception %s" % ws.exception())

    print("websocket connection closed")
    await task

    return ws


app = web.Application()
app.add_routes(routes)
web.run_app(app)
