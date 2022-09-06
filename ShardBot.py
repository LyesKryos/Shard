import asyncpg
import discord
from discord.ext import commands
import os
import logging
from datetime import datetime as dt


class Shard(commands.Bot):
    def __init__(self):
        # sets prefix, initiates bot, and loads cogs
        self.prefix = "$"
        super().__init__(command_prefix=self.prefix, intents=discord.Intents.all(),
                         activity=discord.Game(f"{self.prefix}help for commands"),
                         application_id=849028002406858753)
        # sets up logging, time, and allowed mentions
        logging.basicConfig(filename="botlogs.log", level=logging.WARNING,
                            format='%(asctime)s %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.WARNING)
        handler = logging.FileHandler("mendedshardlogs.log", encoding="utf-8", mode='a')
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
        self.logger.addHandler(handler)
        self.time = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        self.version = "Shard Version 1.4"
        self.last_update = "Shard Update: Repairman"
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

    async def on_member_join(self, member):
        if member.guild.id == 674259612580446230:
            role = member.guild.get_role(751113326481768479)
            await member.add_roles(role)


