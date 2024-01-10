from ShardBot import Shard
import logging
import logging.handlers as handlers


def main(bot: Shard):
    bot.run("ODM0ODkyMDM3MjE1NjE3MDk0.YIHfzQ.-UBhOq3ukC7kz3VTvUmpUBtjqaM", log_handler=bot.logger)


main(Shard())
