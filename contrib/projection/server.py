#!/usr/bin/env python
import logging
import os
from aiohttp import web
from typing import cast

from jsonrpcd.rpc.app import Request
from jsonrpcd.fan.web import ClubWeb

logging.getLogger("asyncio").setLevel(logging.WARNING)

app = web.Application()

club = ClubWeb(app)
club.register_room("secret_room", os.getenv("FAN_KEY", ""))


@club.rpc_app.handler("hello", public=True)
async def hello(request: Request) -> str:
    return f"Hello {cast(list[str], request.params)[0]}"


async def index(request):
    fp = open("./templates/auth.html", "r")
    return web.Response(body=fp.read(), content_type="text/html")


app.router.add_static("/js", "./www-data/js")
app.router.add_get("/", index)

if __name__ == "__main__":
    web.run_app(app)
