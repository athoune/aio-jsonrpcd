#!/usr/bin/env python3
"""
Neutral websocket client.

    ./client.py http://0.0.0.0:8080/rpc

 * Connect to the websocket url.
 * Use the prompt (the line beginning with a "->") for sending data
 * Responses are lines
"""

import aiohttp
import asyncio
import aioconsole


class Client:
    async def connect(self, url: str):
        session = aiohttp.ClientSession()
        self.ws = await session.ws_connect(url)

    async def loop(self):
        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                print(msg.data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                break

    async def send(self, message: str):
        await self.ws.send_str(message)


async def main(url: str):
    client = Client()
    await client.connect(url)
    t = asyncio.create_task(client.loop())
    try:
        while True:
            line = await aioconsole.ainput("-> ")
            await client.send(line)
    except RuntimeError:
        pass
    finally:
        t.cancel()


if __name__ == "__main__":
    import sys

    try:
        asyncio.run(main(sys.argv[1]))
    except KeyboardInterrupt:
        print("Bye!")
