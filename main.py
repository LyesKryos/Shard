from ShardBot import Shard
import asyncio


def main(bot: Shard):
    bot.run("ODM0ODkyMDM3MjE1NjE3MDk0.YIHfzQ.-UBhOq3ukC7kz3VTvUmpUBtjqaM", log_handler=bot.logger)


main(Shard())
