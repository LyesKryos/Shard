import logging

import discord
import discord.errors
from discord import app_commands
from ShardBot import Shard
from discord.ext import commands
from customchecks import SilentFail


class ShardErrorHandler(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.debug_mode = False

    def cog_load(self):
        tree = self.bot.tree
        self._old_tree_error = tree.on_error
        tree.on_error = self.on_app_command_error
        # Patch discord.ui error handlers (Views, Modals) so their exceptions are caught and logged
        # Store originals to restore on unload
        self._old_view_on_error = getattr(discord.ui.View, 'on_error', None)
        self._old_modal_on_error = getattr(discord.ui.Modal, 'on_error', None)

        logger = self.logger

        async def _patched_view_on_error(view_self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction):
            try:
                view_name = type(view_self).__name__
                item_repr = getattr(item, 'custom_id', None) or getattr(item, 'label', None) or type(item).__name__
                cmd = interaction.command.name if getattr(interaction, 'command', None) else None
                where = f"View={view_name} Item={item_repr} Cmd={cmd or 'N/A'}"
                # Try to notify the user
                try:
                    content = "An error occurred while handling this UI action. The incident was logged."
                    if interaction.response.is_done():
                        await interaction.followup.send(content, ephemeral=True)
                    else:
                        await interaction.response.send_message(content, ephemeral=True)
                except Exception:
                    pass
                logger.exception(msg=f"Unhandled UI error in {where}", exc_info=error)
            except Exception:
                # Last-chance log if even the handler fails
                logger.exception(msg="Failed inside patched View.on_error handler", exc_info=True)

        async def _patched_modal_on_error(modal_self, interaction: discord.Interaction, error: Exception):
            try:
                modal_name = type(modal_self).__name__
                cmd = interaction.command.name if getattr(interaction, 'command', None) else None
                where = f"Modal={modal_name} Cmd={cmd or 'N/A'}"
                # Try to notify the user
                try:
                    content = "An error occurred while submitting this modal. The incident was logged."
                    if interaction.response.is_done():
                        await interaction.followup.send(content, ephemeral=True)
                    else:
                        await interaction.response.send_message(content, ephemeral=True)
                except Exception:
                    pass
                logger.exception(msg=f"Unhandled Modal error in {where}", exc_info=error)
            except Exception:
                logger.exception(msg="Failed inside patched Modal.on_error handler", exc_info=True)

        discord.ui.View.on_error = _patched_view_on_error
        discord.ui.Modal.on_error = _patched_modal_on_error

    def cog_unload(self):
        # Restore tree error handler
        try:
            tree = self.bot.tree
            tree.on_error = getattr(self, '_old_tree_error', tree.on_error)
        except Exception:
            pass
        # Restore original UI error handlers
        try:
            if getattr(self, '_old_view_on_error', None) is not None:
                discord.ui.View.on_error = self._old_view_on_error
            if getattr(self, '_old_modal_on_error', None) is not None:
                discord.ui.Modal.on_error = self._old_modal_on_error
        except Exception:
            self.logger.exception(msg="Failed to restore original UI error handlers on cog unload", exc_info=True)

    @commands.command()
    async def debug_mode(self, ctx, on_off: bool):
        self.debug_mode = on_off
        return await ctx.send(f"Debug mode: {self.debug_mode}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error: commands.CommandError):
        """
        Handler for any text command errors.
        """
        # load/unload/reload errors
        if isinstance(error, commands.ExtensionNotFound):
            await ctx.send("There is no such extension, idjit.")
        elif isinstance(error, commands.ExtensionNotLoaded):
            await ctx.send("Fool, you didn't load it!")
        elif isinstance(error, commands.ExtensionAlreadyLoaded):
            await ctx.send("Fool, you already loaded it!")
        elif isinstance(error, commands.ExtensionError):
            await ctx.send(f"Extension error. Check logs.")
            self.logger.exception(msg=error)
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
        elif isinstance(error, commands.errors.ExtensionNotLoaded):
            await ctx.send("That extension is not loaded.")
        else:
            # define command
            command_name = ctx.command.qualified_name or "No command name recognized."
            await ctx.send("An error occurred. Check the logs.")
            self.logger.exception(msg=f"Unhandled error in command: {command_name}", exc_info=error)


    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """
        Handler for any app command errors.
        """
        # define command name
        command_name = interaction.command.name if interaction.command else "Unknown Command"
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
            await interaction.response.send_message(content="You do not have the right permissions for this command "
                                                    "or are blocked from using this command.", ephemeral=True)
        elif isinstance(error, app_commands.errors.TransformerError):
            await interaction.response.send_message("I am unfamiliar with that input. Please try again.",
                                                    ephemeral=True)
        else:
            await interaction.channel.send(f"An error occurred. Check the logs.")
            self.logger.exception(msg=f"Unhandled error in command: {command_name}", exc_info=error)

    @commands.Cog.listener()
    async def on_error(self, event: str, error: Exception):
        """
        Global handler for errors raised in event listeners.
        This catches exceptions in events like on_message, on_member_join, etc.
        """
        self.logger.exception(msg=f"An error occurred in event `{event}`.", exc_info=True)


async def setup(bot: Shard):
    errorhandler = ShardErrorHandler(bot)
    await bot.add_cog(errorhandler)
