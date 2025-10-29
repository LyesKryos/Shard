import json
import asyncpg
import discord
from discord.ext import commands
import os
import logging
from datetime import datetime as dt
from cogs import EXTENSIONS


class Shard(commands.Bot):
    def __init__(self):
        # sets prefix, initiates bot, and loads cogs
        self.pool = None
        self.prefix = "$"
        super().__init__(command_prefix=self.prefix, intents=discord.Intents.all(),
                         activity=discord.Game(f"{self.prefix}help for commands"))
        # setup logger
        logging.basicConfig(filename="botlogs.log", format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt="%Y-%m-%d %H:%M:%S")
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
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
        self.system_message = ""
        self.config = json.load(open("config.json"))

    async def setup_hook(self):
        for extension in EXTENSIONS:
            await self.load_extension(extension)
            print(extension)
        # creates connection pool
        self.pool: asyncpg.Pool = await asyncpg.create_pool(self.config["dsn"])

    async def close(self):
        await super().close()

    def run(self, *args, **kwargs):
        super().run(self.config["token"])
