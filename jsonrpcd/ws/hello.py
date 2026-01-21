from aiohttp import web

from ..rpc.app import App as WsApp
from ..rpc.app import Request, anonymous
from .web import JsonRpcWebHandler

ws_app = WsApp()


@ws_app.handler("hello")
@anonymous
async def hello(request: Request) -> str:
    return f"Hello {request.params[0]}"


rpc_app = JsonRpcWebHandler(ws_app)

routes = web.RouteTableDef()

routes.get("/rpc")(rpc_app)


@routes.get("/")
async def hello(request):
    return web.Response(text="Hello, world")


app = web.Application()
app.add_routes(routes)


if __name__ == "__main__":
    web.run_app(app)
