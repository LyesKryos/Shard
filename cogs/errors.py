import traceback

import discord.errors
from discord import app_commands
from ShardBot import Shard
from discord.ext import commands
from customchecks import SilentFail


class ShardErrorHandler(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot
        self.debug_mode = False

    def cog_load(self):
        tree = self.bot.tree
        self._old_tree_error = tree.on_error
        tree.on_error = self.on_app_command_error

    @commands.command()
    async def debug_mode(self, ctx, on_off: bool):
        self.debug_mode = on_off
        return await ctx.send(f"Debug mode: {self.debug_mode}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error: commands.CommandError):
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
            await ctx.send(f"Extension error. Check logs.")
            self.bot.logger.exception(error)
        # if the command used does not exist
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send(f"Command `{self.bot.prefix}{ctx.invoked_with}` not found.")
        elif isinstance(error, RuntimeError):
            await ctx.send("Command already running.")
        # if the user is not authorized
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(f"I do not have the proper permissions for `{ctx.invoked_with}`.")
        # if the user is really not authorized
        elif isinstance(error, commands.NotOwner):
            await ctx.send("There is only one Lord of the Shard. And he does not share power!")
        # if the user is missing a role necessary for the command
        elif isinstance(error, commands.MissingRole):
            await ctx.send("You do not have the proper role for that, amigo.")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("I cannot find that server member.")
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
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Slow down! Try again in {error.retry_after:.2f} seconds.")
        elif isinstance(error, SilentFail):
            return
        elif isinstance(error, commands.UserNotFound):
            await ctx.send("I cannot find that user.")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("A check failed. Check the logs.")
        elif isinstance(error, discord.errors.Forbidden):
            await ctx.send("I cannot complete that action.")
        else:
            self.bot.logger.exception(msg=error)

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        # unwrap error
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original
        # if the user attempts to use a command in DMs that is not authorized to use in DMs
        if isinstance(error, app_commands.errors.NoPrivateMessage):
            await interaction.response.send_message(f"I cannot run `{interaction.command}` in DMs! "
                                                    f"Return to the safety of a server.")
        elif isinstance(error, app_commands.errors.CommandOnCooldown):
            await interaction.response.send_message(f"Slow down! Try again in {int(error.retry_after)} seconds.",
                                                    ephemeral=True)
        elif isinstance(error, app_commands.errors.MissingRole):
            await interaction.response.send_message("You are missing the proper roles for this command.")
        elif isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("You do not have the right permissions for this command "
                                                    "or are blocked from using this command.", ephemeral=True)
        else:
            self.bot.logger.exception(msg=error)
            if self.debug_mode is False:
                return await interaction.channel.send("An error occurred, check the logs.")
            elif self.debug_mode is True:
                return await interaction.channel.send(f"Error:\n```{error}```")


async def setup(bot: Shard):
    errorhandler = ShardErrorHandler(bot)
    await bot.add_cog(errorhandler)
