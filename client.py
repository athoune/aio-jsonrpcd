import aiohttp
import asyncio


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect("http://localhost:8080/ws/prout") as ws:

            async def down():
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        print(msg.data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        break

            async def up():
                await ws.send_json(dict(name="Gunter"))

            async with asyncio.TaskGroup() as tg:
                task_down = tg.create_task(down())
                task_up = tg.create_task(up())


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Bye!")
