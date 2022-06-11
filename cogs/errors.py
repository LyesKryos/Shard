import discord
import traceback
import sys
from ShardBot import Shard
from discord.ext import commands
from customchecks import SilentFail


class ShardErrorHandler(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        crashchannel = self.bot.get_channel(835579413625569322)
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
            await ctx.send(f"Command `{self.bot.prefix}{ctx.invoked_with}` not found.")
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
            self.bot.logger.warning(msg=traceback.format_exc())
        else:
            self.bot.logger.warning(msg=error)

async def setup(bot: Shard):
    errorhandler = ShardErrorHandler(bot)
    await bot.add_cog(errorhandler)
