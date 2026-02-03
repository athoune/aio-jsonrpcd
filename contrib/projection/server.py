#!/usr/bin/env python
import logging
import os
from aiohttp import web

from jsonrpcd.fan.web import ClubWeb

logging.getLogger("asyncio").setLevel(logging.WARNING)

app = web.Application()

club = ClubWeb(app)
key: str | None = os.getenv("FAN_KEY")
if key is None:
    print("Set the FAN_KEY ENV")
    exit(-1)
else:
    club.register_room("secret_room", key)


async def index(request):
    fp = open("./templates/index.html", "r")
    return web.Response(body=fp.read(), content_type="text/html")


app.router.add_static("/js", "./www-data/js")
app.router.add_static("/css", "./www-data/css")
app.router.add_get("/", index)

if __name__ == "__main__":
    web.run_app(app)
