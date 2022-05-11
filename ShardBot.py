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
                         activity=discord.Game(f"{self.prefix}help for commands"))
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                self.load_extension(f"cogs.{filename[:-3]}")
        # sets up logging, time, and allowed mentions
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.WARNING)
        handler = logging.FileHandler("botlogs.log", encoding="utf-8", mode='a')
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
        self.logger.addHandler(handler)
        self.time = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        self.version = "v.1.4"
        self.version_name = "Repairman"
        self.allowed_mentions = discord.AllowedMentions(
            users=True,  # Whether to ping individual user @mentions
            everyone=True,  # Whether to ping @everyone or @here mentions
            roles=True,  # Whether to ping role @mentions
            replied_user=True,  # Whether to ping on replies to messages
        )
        # creates connection pool
        self.pool: asyncpg.Pool = self.loop.run_until_complete(asyncpg.create_pool('postgres://postgres@127.0.0.1:5432',
                                                      database="botdb",
                                                      password="postgres"))



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
            logging.warning(
                f"{self.time} {ctx.message.author} {ctx.message.id} caused the error \"{error}\" using the command "
                f"{ctx.invoked_with}")
        if isinstance(error, RuntimeError):
            await ctx.send("Command already running.")
            logging.warning(
                f"{self.time} {ctx.message.author} {ctx.message.id} caused the error \"{error}\" using the command "
                f"{ctx.invoked_with}")
        # if the user is not authorized
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"I do not have the proper permissions for `{ctx.invoked_with}`.")
        # if the user is really not authorized
        elif isinstance(error, commands.NotOwner):
            await ctx.send("There is only one Lord of the Shard. And he does not share power!")
        # if the user is missing a role necessary for the command
        elif isinstance(error, commands.MissingRole):
            await ctx.send("You do not have the proper role for that, buddy.")
        # if the user attempts to use a command in DMs that is not authorized to use in DMs
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(f"I cannot run `${ctx.invoked_with}` in DMs! Return to the safety of a server.")
        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send(f"I cannot run `${ctx.invoked_with}` outside of DMs!")
        # if there is a custom check error
        elif isinstance(error, commands.UserInputError):
            await ctx.send_help(ctx.invoked_with)
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(str(error))
        else:
            logging.warning(
                f"{self.time} {ctx.message.author} {ctx.message.id} caused the error \"{error}\" using the command "
                f"{ctx.invoked_with}")

