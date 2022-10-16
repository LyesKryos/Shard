import re
import traceback
from typing import Optional

import discord
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
                            value="Increased optimization, added new minigame, and added command descriptions for the "
                                  "help command.",
                            inline=False)
        infoembed.add_field(name="Hosting Software", value="Oracle Virtual Cloud Network Virtual Machine")
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

    @commands.command(brief="Measures latency between Discord and the host server.")
    async def ping(self, ctx):
        msg = await ctx.send(f"Round trip {round(self.bot.latency * 1000, 2)}ms!")
        await msg.add_reaction("↔")

    @commands.command(brief="Displays information about a user in the server.")
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
            if verified['main_nation'] == '':
                nation_list = []
                for n in verified['main_nation']:
                    nation_list.append(f"[{n}]"
                                       f"(https://www.nationstates.net/nation={self.sanitize_links_underscore(n)})")
                user_nations = ', '.join(nation_list)
            else:
                user_nations = f"[**{verified['main_nation']}**]" \
                               f"(https://www.nationstates.net/nation=" \
                               f"{self.sanitize_links_underscore(verified['main_nation'])})"
                for n in verified['nations']:
                    if n == verified['main_nation']:
                        continue
                    user_nations += f", [{n}](https://www.nationstates.net/nation={self.sanitize_links_underscore(n)})"
        # defines roles
        all_roles = user.roles[1:]
        role_names = [r.name for r in all_roles]
        user_roles = ', '.join(role_names[::-1])
        # creates embed
        user_embed = discord.Embed(title=f"{user.display_name}", description=f"Information about server member "
                                                                     f"{user.name}#{user.discriminator}\n"
                                                                     f"User ID: {user.id}.",

                                   color=user.color)
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

    @commands.command()
    @commands.is_owner()
    async def error(self, ctx):
        raise Exception("Custom error.")

    @commands.command()
    @commands.is_owner()
    async def silent_error(self, ctx, *, args):
        raise SilentFail

    async def on_member_join(self, member):
        if member.guild.id == 674259612580446230:
            role = member.guild.get_role(751113326481768479)
            await member.add_roles(role)


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
