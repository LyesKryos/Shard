import asyncio
import discord
from ShardBot import Shard
from discord.ext import commands
import os

class BaseCommands(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot
   
    @commands.command(aliases=["1080"])
    async def teneighty(self, ctx):
        await ctx.send("https://i.ibb.co/TtcdQ3d/image.png")

    @commands.command()
    @commands.is_owner()
    async def info(self, ctx):
        infoembed = discord.Embed(color=discord.Color.blue(), title="Shard", description="A purpose-built machine for "
                                                                                         "quality of life,"
                                                                                         " ease of access, "
                                                                                         "and entertainment.")
        infoembed.set_thumbnail(url="https://i.ibb.co/Sc45nVZ/Shard.webp")
        infoembed.add_field(name="Created", value="By Lies Kryos#1734\nApril 24, 2021")
        infoembed.add_field(name="Current version", value=f"{self.bot.version} {self.bot.version_name}")
        infoembed.add_field(name="Version Notes", value="None", inline=False)
        infoembed.add_field(name="Hosting Software", value="Amazon AWS EC2 Virtual Machine")
        await ctx.send(embed=infoembed)



    @commands.command()
    @commands.is_owner()
    async def shut_down(self, ctx, *args):
        channel_ids = [674285035905613825, 319961144091738112, 606505493657288735]
        for channels in channel_ids:
            channel = self.bot.get_channel(channels)
            await channel.send("I am shutting down with this message:\n"
                               f"```{' '.join(args[:])}```")
        await ctx.send("Shutting down!")
        exit(100)


    @commands.command()
    @commands.is_owner()
    async def nap(self, ctx):
        await ctx.send("Powering off...")
        await ctx.send("https://tenor.com/view/serio-no-nop-robot-robot-down-gif-12270251")
        exit("Nighty night")

    @commands.command()
    @commands.is_owner()
    async def announce_global(self, ctx, *args):
        channel_ids = [674285035905613825, 319961144091738112, 606505493657288735]
        for id in channel_ids:
            channel = self.bot.get_channel(id)
            await channel.send(' '.join(args[:]))

    @commands.command()
    @commands.is_owner()
    async def load(self, ctx, extension):
        self.bot.load_extension(f"cogs.{extension}")
        await ctx.send(f"Loaded extension: `{extension}`")


    @commands.command()
    @commands.is_owner()
    async def unload(self, ctx, extension):
        self.bot.unload_extension(f"cogs.{extension}")
        await ctx.send(f"Unloaded extension: `{extension}`")


    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, extension):
        self.bot.unload_extension(f"cogs.{extension}")
        self.bot.load_extension(f"cogs.{extension}")
        await ctx.send(f"Reloaded extension: `{extension}`")


    @commands.command()
    @commands.is_owner()
    async def recycle(self, ctx):
        await ctx.send("Recycling!")
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                self.bot.unload_extension(f"cogs.{filename[:-3]}")
                self.bot.load_extension(f"cogs.{filename[:-3]}")
        await ctx.send("Recycled all cogs.")
        
    @commands.command()
    async def ping(self, ctx):
        msg = await ctx.send(f"Round trip {round(self.bot.latency * 1000, 2)}ms!")
        await msg.add_reaction("↔")

    async def on_ready(self):
        print("Ready.")
        await self.bot.change_presence(activity=discord.Game("m$help for commands"))
        channel = self.bot.get_channel(835579413625569322)
        await channel.send("We are online.")

def setup(bot: Shard):
    async def alive(bot):
        await bot.wait_until_ready()
        try:
            server = bot.get_guild(728444080908140575)
            channel = server.get_channel(835579413625569322)
            await channel.send("We are online.")
        except Exception as error:
            print(error)
    loop = bot.loop
    loop.create_task(alive(bot))
    bot.add_cog(BaseCommands(bot))