from ShardBot import Shard
import logging
import logging.handlers as handlers


def main(bot: Shard):
    # define logger for bot
    logging.basicConfig(filename="botlogs.log", level=logging.WARNING,
                        format='%(asctime)s %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)
    handler = handlers.RotatingFileHandler("botlogs.log", encoding="utf-8",
                                           mode='a', maxBytes=5000, backupCount=3)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    bot.run("ODM0ODkyMDM3MjE1NjE3MDk0.YIHfzQ.-UBhOq3ukC7kz3VTvUmpUBtjqaM", log_handler=handler)


main(Shard())
