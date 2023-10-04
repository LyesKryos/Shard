import re
import traceback
from typing import Optional

import discord
from discord import app_commands

from ShardBot import Shard
from discord.ext import commands
import os
from customchecks import SilentFail


class BaseCommands(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot

    def sanitize_links_underscore(self, userinput: str) -> str:
        # replaces user input with proper, url-friendly code
        to_regex = userinput.replace(" ", "_")
        return re.sub(r"[^a-zA-Z0-9_-]", ' ', to_regex)

    @commands.command(aliases=["1080"])
    async def teneighty(self, ctx):
        await ctx.send("https://i.ibb.co/TtcdQ3d/image.png")

    @commands.command(brief="Displays information about the bot")
    async def info(self, ctx):
        infoembed = discord.Embed(color=discord.Color.blue(), title="Shard", description="A purpose-built machine for "
                                                                                         "quality of life,"
                                                                                         " ease of access, "
                                                                                         "and entertainment.")
        infoembed.set_thumbnail(url="https://i.ibb.co/Sc45nVZ/Shard.webp")
        infoembed.add_field(name="Created", value="By Lies Kryos#1734\nApril 24, 2021")
        infoembed.add_field(name="Current version", value=f"{self.bot.version}")
        infoembed.add_field(name="Version Notes",
                            value="Introduced new ecnomy system.",
                            inline=False)
        infoembed.add_field(name="Hosting Software", value="Oracle Virtual Cloud Network Virtual Machine")
        infoembed.set_footer(text="[Donate to the creator!](https://ko-fi.com/shardbot)")
        await ctx.send(embed=infoembed)

    @commands.command(brief="Shuts down the bot with a global message")
    @commands.is_owner()
    async def shut_down(self, ctx, *args):
        channel_ids = [674285035905613825, 319961144091738112, 606505493657288735]
        for channels in channel_ids:
            channel = self.bot.get_channel(channels)
            await channel.send("I am shutting down with this message:\n"
                               f"```{' '.join(args[:])}```")
        await ctx.send("Shutting down!")
        exit(100)

    @commands.command(brief="Shuts down the bot without a global message.")
    @commands.is_owner()
    async def nap(self, ctx):
        await ctx.send("Powering off...")
        await ctx.send("https://tenor.com/view/serio-no-nop-robot-robot-down-gif-12270251")
        exit("Nighty night")

    @commands.command(brief="Sends a plaintext message to all channels associated.")
    @commands.is_owner()
    async def announce_global(self, ctx, *, args):
        try:
            channel_ids = [674285035905613825, 319961144091738112, 606505493657288735]
            for id in channel_ids:
                channel = self.bot.get_channel(id)
                await channel.send(args)
        except Exception:
            self.bot.logger.warning(msg=traceback.format_exc())

    @commands.command(brief="Loads cog")
    @commands.is_owner()
    async def load(self, ctx, extension):
        await self.bot.load_extension(f"cogs.{extension}")
        await ctx.send(f"Loaded extension: `{extension}`")

    @commands.command(brief="Unloads cog")
    @commands.is_owner()
    async def unload(self, ctx, extension):
        await self.bot.unload_extension(f"cogs.{extension}")
        await ctx.send(f"Unloaded extension: `{extension}`")

    @commands.command(brief="Reloads cog")
    @commands.is_owner()
    async def reload(self, ctx, extension):
        await self.bot.unload_extension(f"cogs.{extension}")
        await self.bot.load_extension(f"cogs.{extension}")
        await ctx.send(f"Reloaded extension: `{extension}`")

    @commands.command(brief="Reloads all cogs")
    @commands.is_owner()
    async def recycle(self, ctx):
        await ctx.send("Recycling!")
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await self.bot.unload_extension(f"cogs.{filename[:-3]}")
                await self.bot.load_extension(f"cogs.{filename[:-3]}")
        await ctx.send("Recycled all cogs.")

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx):
        syncing = await ctx.send("Syncing app commands!")
        synced = await self.bot.tree.sync()
        await syncing.edit(content=f"Synced {len(synced)} commands.")

    @commands.command(brief="Measures latency between Discord and the host server.")
    async def ping(self, ctx):
        msg = await ctx.send(f"Round trip {round(self.bot.latency * 1000, 2)}ms!")
        await msg.add_reaction("↔")

    @commands.command(brief="Displays information about a user in the server.", aliases=['p'])
    @commands.guild_only()
    async def profile(self, ctx, *, args=None):
        # establishes connection
        conn = self.bot.pool
        # gets user
        if args is None:
            user = ctx.author
        else:
            user = await commands.converter.MemberConverter().convert(ctx, args)
        # fetches nation information
        verified = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''', user.id)
        if verified is None:
            user_nations = "*None*"
        else:
            user_nations += (f", [{verified['main_nation']}](https://www.nationstates.net/nation="
                             f"{self.sanitize_links_underscore(verified['main_nation'])})")
        # defines roles
        all_roles = user.roles[1:]
        role_names = [f"<@&{r.id}>" for r in all_roles]
        user_roles = ', '.join(role_names[::-1])
        # creates embed
        user_embed = discord.Embed(title=f"{user.display_name}", description=f"Information about server member "
                                                                     f"{user.name}#{user.discriminator}\n"
                                                                     f"User ID: {user.id}.", color=user.color)
        user_embed.set_thumbnail(url=user.display_avatar.url)
        user_embed.add_field(name="Joined Discord", value=f"{user.created_at.strftime('%d %B %Y')}")
        user_embed.add_field(name="Joined Server", value=f"{user.joined_at.strftime('%d %B %Y')}")
        user_embed.add_field(name="\u200b", value="\u200b")
        user_embed.add_field(name="Roles", value=f"{user_roles}", inline=False)
        user_embed.add_field(name="Nations", value=user_nations)
        await ctx.send(embed=user_embed)

    async def on_ready(self):
        print("Ready.")
        await self.bot.change_presence(activity=discord.Game("m$help for commands"))
        channel = self.bot.get_channel(835579413625569322)
        await channel.send("We are online.")

    @app_commands.command(name="manage_roles", description="Adds a legal role to a user.")
    @app_commands.describe(role="The role you wish to add.", user="MODERATORS ONLY")
    async def manage_roles(self, interaction: discord.Interaction, role: discord.Role, user: discord.User = None):
        # defer interaction
        await interaction.response.defer(thinking=True)
        moderator = interaction.guild.get_role(798416884462387220)
        admin = interaction.guild.get_role(674278353204674598)
        # if the user tries to assign a role to someone else and they are not a moderator, refuse
        if moderator not in interaction.user.roles:
            if admin not in interaction.user.roles:
                return interaction.followup.send("You do not have the permissions to assign roles to other users.")
        # make connection
        conn = self.bot.pool
        # fetch all the role IDs
        roles = await conn.fetchrow('''SELECT * FROM info WHERE name='roles';''')
        roles = roles['number_list']
        if role.id not in roles:
            return await interaction.followup.send("That role cannot be self-assigned.")
        else:
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                return await interaction.followup.send(f"You have removed the `{role.name}` role.")
            else:
                await interaction.user.add_roles(role)
                return await interaction.followup.send(f"You have added the `{role.name}` role.")



    @commands.command()
    @commands.is_owner()
    async def error(self, ctx):
        raise Exception("Custom error.")

    @commands.command()
    @commands.is_owner()
    async def silent_error(self, ctx, *, args):
        raise SilentFail

    @commands.command()
    @commands.is_owner()
    async def repeat(self, ctx, *, args):
        await ctx.send(args)
        return


async def setup(bot: Shard):
    async def alive(bot):
        await bot.wait_until_ready()
        try:
            server = bot.get_guild(728444080908140575)
            channel = server.get_channel(835579413625569322)
            await channel.send("We are online.")
        except Exception:
            bot.logger.warning(msg=traceback.format_exc())

    loop = bot.loop
    loop.create_task(alive(bot))
    await bot.add_cog(BaseCommands(bot))
