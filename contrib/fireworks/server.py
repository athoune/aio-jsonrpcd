#!/usr/bin/env python
import logging
import os
from aiohttp import web
from typing import cast

from jsonrpcd.rpc.app import App as RpcApp
from jsonrpcd.rpc.app import Request
from jsonrpcd.ws.web import JsonRpcWebHandler
from jsonrpcd.fan.club import Club, all, close_session

logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)

rpc_app = RpcApp()
club = Club(rpc_app)
club.register_room("secret_room", os.getenv("FAN_KEY", ""))

rpc_app.namespace("all")(all)
rpc_app.handler("authenticate", public=True)(club.authenticate)


@rpc_app.handler("hello", public=True)
async def hello(request: Request) -> str:
    return f"Hello {cast(list[str], request.params)[0]}"


ws_app = JsonRpcWebHandler(rpc_app, on_close=close_session)


async def index(request):
    fp = open("./www-data/index.html", "r")
    return web.Response(body=fp.read(), content_type="text/html")


routes = web.RouteTableDef()
routes.get("/rpc")(ws_app)
routes.static("/js", "./www-data/js")
routes.get("/")(index)

app = web.Application()
app.add_routes(routes)


if __name__ == "__main__":
    web.run_app(app)
