from ShardBot import Shard
import asyncio


async def main(bot: Shard):
    async with bot:
        bot.run("ODM0ODkyMDM3MjE1NjE3MDk0.YIHfzQ.-UBhOq3ukC7kz3VTvUmpUBtjqaM", log_handler=bot.logger)


asyncio.run(main(Shard()))
