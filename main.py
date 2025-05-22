from ShardBot import Shard
import logging
import logging.handlers as handlers


def main(bot: Shard):
    handler = handlers.RotatingFileHandler("botlogs.log", encoding="utf-8",
                                           mode='a', maxBytes=1000000)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    handler.setLevel(logging.INFO)
    bot.run(log_handler=handler)


main(Shard())
