import asyncpg
import discord
from discord.ext import commands
import os
import logging
import logging.handlers as handlers
from datetime import datetime as dt


class Shard(commands.Bot):
    def __init__(self):
        # sets prefix, initiates bot, and loads cogs
        self.pool = None
        self.prefix = "$"
        super().__init__(command_prefix=self.prefix, intents=discord.Intents.all(),
                         activity=discord.Game(f"{self.prefix}help for commands"))
        # setup logger
        logging.basicConfig(filename="botlogs.log", level=logging.WARNING,
                            format='%(asctime)s %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.WARNING)
        # sets up time, version, and mentions
        self.time = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        self.version = "Shard Version 1.6"
        self.last_update = "Shard Update: Silver and Gold"
        self.allowed_mentions = discord.AllowedMentions(
            users=True,  # Whether to ping individual user @mentions
            everyone=True,  # Whether to ping @everyone or @here mentions
            roles=True,  # Whether to ping role @mentions
            replied_user=True,  # Whether to ping on replies to messages
        )

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")
        # creates connection pool
        self.pool: asyncpg.Pool = await asyncpg.create_pool('postgresql://postgres@127.0.0.1:5432',

                                                            database="botdb")

    async def close(self):
        await super().close()
