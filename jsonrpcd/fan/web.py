#!/usr/bin/env python
import logging
from aiohttp import web

from ..rpc.app import App as RpcApp
from ..ws.web import JsonRpcWebHandler
from .club import Club, all, close_session


class ClubWeb:
    def __init__(self, app: web.Application, loglevel=logging.INFO) -> None:
        logging.basicConfig(level=loglevel)
        self.rpc_app = RpcApp()
        self.club = Club(self.rpc_app)
        # RPC
        self.rpc_app.namespace("all")(all)
        self.rpc_app.handler("authenticate", public=True)(self.club.authenticate)
        # Websocket
        ws_app = JsonRpcWebHandler(self.rpc_app, on_close=close_session)
        # Http
        self.routes = web.RouteTableDef()
        self.routes.get("/rpc")(ws_app)
        app.add_routes(self.routes)

    def register_room(self, room: str, key: str):
        self.club.register_room(room, key)
