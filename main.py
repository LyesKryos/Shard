from ShardBot import Shard
import asyncio


async def main(bot: Shard):
    async with bot:
        await bot.start("ODM0ODkyMDM3MjE1NjE3MDk0.YIHfzQ.-UBhOq3ukC7kz3VTvUmpUBtjqaM")


asyncio.run(main(Shard()))
