from ShardBot import Shard
import logging
import logging.handlers as handlers
import asyncio
import json
import discord

def main(bot: Shard):'
    print(discord.__version__)
    # read config file
    token_raw = json.load(open("config.json"))
    token = token_raw["token"]
    # setup logger
    handler = handlers.RotatingFileHandler("botlogs.log", encoding="utf-8",
                                           mode='a', maxBytes=50000, backupCount=3)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    handler.setLevel(logging.INFO)
    bot.run(token, log_handler=handler)

main(Shard())
