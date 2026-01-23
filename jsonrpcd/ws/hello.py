from typing import cast
from aiohttp import web

from ..rpc.app import App, Request
from .web import JsonRpcWebHandler

app = App()


@app.handler("hello", public=True)
async def hello(request: Request) -> str:
    return f"Hello {cast(list[str], request.params)[0]}"


rpc_app = JsonRpcWebHandler(app)

routes = web.RouteTableDef()

routes.get("/rpc")(rpc_app)

app = web.Application()
app.add_routes(routes)


if __name__ == "__main__":
    web.run_app(app)
