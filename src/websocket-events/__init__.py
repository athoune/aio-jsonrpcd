from aiohttp import web
from redis import asyncio as aioredis

routes = web.RouteTableDef()
redis: aioredis.Redis = aioredis.from_url("redis://localhost", decode_responses=True)


@routes.get("/")
async def home(request):
    return web.Response(text="Master of events.")


@routes.get("/{db}")
async def hello(request):
    key: str = request.match_info["db"].encode("utf8")
    all: dict[str, str] = await redis.hgetall(key)
    return web.json_response(all)


app = web.Application()
app.add_routes(routes)
web.run_app(app)
