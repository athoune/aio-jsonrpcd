#!/usr/bin/env python
import logging
import os
from aiohttp import web
from typing import cast

from jsonrpcd.rpc.app import Request
from jsonrpcd.fan.web import ClubWeb
from jsonrpcd.fan.club import all

logging.getLogger("asyncio").setLevel(logging.WARNING)

app = web.Application()

club = ClubWeb(app)
key: str | None = os.getenv("FAN_KEY")
if key is None:
    print("Set the FAN_KEY ENV")
    exit(-1)
else:
    club.register_room("secret_room", key)


@club.rpc_app.handler("hello", public=True)
async def hello(request: Request) -> str:
    return f"Hello {cast(list[str], request.params)[0]}"


@club.rpc_app.function("ping", public=True)
async def ping() -> str:
    logging.info("ping")
    return "pong"


club.rpc_app.namespace("all")(all)


async def index(request):
    fp = open("./templates/index.html", "r")
    return web.Response(body=fp.read(), content_type="text/html")


app.router.add_static("/js", "./www-data/js")
app.router.add_static("/css", "./www-data/css")
app.router.add_get("/", index)

if __name__ == "__main__":
    web.run_app(app)
