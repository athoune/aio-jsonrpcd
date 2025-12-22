import aiohttp
import asyncio


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect("http://localhost:8080/ws/prout") as ws:

            async def down():
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        if msg.data == "close cmd":
                            await ws.close()
                            break
                        else:
                            await ws.send_str(msg.data + "/answer")
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        break

            t = asyncio.create_task(down())
            await ws.send_json(dict(name="Gunter"))
            t.cancel()


asyncio.run(main())
