from redis import asyncio as aioredis
from redis.asyncio.client import PubSub
import os
import json


class CRUD:
    def __init__(self, redis_url: str) -> None:
        self.redis: aioredis.Redis = aioredis.from_url(redis_url, decode_responses=True)
        here = os.path.dirname(__file__)
        self.lazy_delete: str = open(f"{here}/lazy_delete.lua", "r").read()

    async def put_dict(self, db: str, values: dict) -> None:
        async with self.redis.pipeline(transaction=True) as pipe:
            for k, v in values.items():
                if v is None:
                    await pipe.hdel(db, k)
                else:
                    await pipe.hset(db, k, json.dumps(v))
            await pipe.publish(db, json.dumps(values))
            await pipe.execute()

    async def delete(self, db: str, key: str):
        return await self.redis.eval(
            self.lazy_delete,
            1,
            db,
            key,
        )

    async def subscribe(self, db: str, raw=False):
        assert db is not None
        pubsub: PubSub = self.redis.pubsub()
        await pubsub.subscribe(db)
        async for response in pubsub.listen():
            if response["type"] != "message":
                continue
            if raw:
                yield response["data"]
            else:
                yield json.loads(response["data"])
