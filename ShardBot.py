import asyncpg
import discord
from discord.ext import commands
import os
import logging
from datetime import datetime as dt
from customchecks import SilentFail
import traceback


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

    async def on_command_error(self, ctx, error):
        # parses the error
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        # load/unload/reload errors
        if isinstance(error, commands.ExtensionNotFound):
            await ctx.send("There is no such extension, idjit.")
        elif isinstance(error, commands.ExtensionNotLoaded):
            await ctx.send("Fool, you didn't load it!")
        elif isinstance(error, commands.ExtensionAlreadyLoaded):
            await ctx.send("Fool, you already loaded it!")
        elif isinstance(error, commands.ExtensionError):
            await ctx.send(f"Extension error: ``{error}``.")
        # if the command used does not exist
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"Command `{self.prefix}{ctx.invoked_with}` not found.")
        if isinstance(error, RuntimeError):
            await ctx.send("Command already running.")
        # if the user is not authorized
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"I do not have the proper permissions for `{ctx.invoked_with}`.")
        # if the user is really not authorized
        elif isinstance(error, commands.NotOwner):
            await ctx.send("There is only one Lord of the Shard. And he does not share power!")
        # if the user is missing a role necessary for the command
        elif isinstance(error, commands.MissingRole):
            await ctx.send("You do not have the proper role for that, amigo.")
        # if the user attempts to use a command in DMs that is not authorized to use in DMs
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(f"I cannot run `${ctx.invoked_with}` in DMs! Return to the safety of a server.")
        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send(f"I cannot run `${ctx.invoked_with}` outside of DMs!")
        elif isinstance(error, commands.MaxConcurrencyReached):
            await ctx.send(f"You're already using `${ctx.invoked_with}`.")
        # if there is a custom check error
        elif isinstance(error, commands.UserInputError):
            await ctx.send_help(ctx.invoked_with)
        elif isinstance(error, SilentFail):
            return
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("A check failed. Check the logs.")
            self.logger.warning(msg=traceback.format_exc())
        else:
            self.logger.warning(msg=traceback.format_exc())
