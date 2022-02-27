import discord
from discord.ext import commands
import os
import logging
import time


prefix = "$"
user = commands.Bot.user
bot = commands.Bot(command_prefix=prefix, intents=discord.Intents.all())
logging.basicConfig(filename="botlogs.log", level=logging.WARNING, format='%(asctime)s %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
version = "Shard Version 1.3.1"
last_update = "Shard Update: Battleborn"

allowed_mentions = discord.AllowedMentions(
    users=True,  # Whether to ping individual user @mentions
    everyone=True,  # Whether to ping @everyone or @here mentions
    roles=True,  # Whether to ping role @mentions
    replied_user=True,  # Whether to ping on replies to messages
)


@bot.event
async def on_ready():
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} Ready.")
    await bot.change_presence(activity=discord.Game("$help for commands"))




@bot.event
async def on_member_join(member):
    if member.guild.id == 674259612580446230:
        role = member.guild.get_role(751113326481768479)
        await member.add_roles(role)


@bot.command()
async def ping(ctx):
    msg = await ctx.send(f"Round trip {round(bot.latency*1000, 2)}ms!")
    await msg.add_reaction("↔")
    
@bot.command(aliases=["1080"])
async def teneighty(ctx):
    await ctx.send("https://i.ibb.co/TtcdQ3d/image.png")
    return

for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")


@bot.command()
@commands.is_owner()
async def load(ctx, extension):
    bot.load_extension(f"cogs.{extension}")
    await ctx.send(f"Loaded extension: `{extension}`")



@bot.command()
@commands.is_owner()
async def unload(ctx, extension):
    bot.unload_extension(f"cogs.{extension}")
    await ctx.send(f"Unloaded extension: `{extension}`")


@bot.command()
@commands.is_owner()
async def reload(ctx, extension):
    bot.unload_extension(f"cogs.{extension}")
    bot.load_extension(f"cogs.{extension}")
    await ctx.send(f"Reloaded extension: `{extension}`")


@bot.command()
@commands.is_owner()
async def recycle(ctx):
    await ctx.send("Recycling!")
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            bot.unload_extension(f"cogs.{filename[:-3]}")
            bot.load_extension(f"cogs.{filename[:-3]}")
    await ctx.send("Recycled all cogs.")

@bot.command()
@commands.is_owner()
async def announce_global(ctx, *args):
    channel_ids = [674285035905613825, 319961144091738112]
    for id in channel_ids:
        channel = bot.get_channel(id)
        await channel.send(' '.join(args[:]))
    user = bot.get_user(228353948552134658)
    await user.send(await user.send(' '.join(args[:])))

@bot.command()
@commands.is_owner()
async def shut_down(ctx, *args):
    channel_ids = [674285035905613825, 319961144091738112]
    for id in channel_ids:
        channel = bot.get_channel(id)
        await channel.send("I am shutting down with this message:\n"
                           f"```{' '.join(args[:])}```")
    user = bot.get_user(228353948552134658)
    await user.send("I am shutting down with this message: \n"
                    f"```{' '.join(args[:])}```")
    await ctx.send("Shutting down!")
    exit(100)

@bot.command()
async def info(ctx):
    await ctx.send(f"{version}\n{last_update}")


@bot.event
async def on_member_join(member):
    if member.guild.id == 674259612580446230:
        role = member.guild.get_role(751113326481768479)
        await member.add_roles(role)


@load.error
async def on_load_error(ctx, error):
    if isinstance(error, commands.ExtensionAlreadyLoaded):
        await ctx.send("Fool, you already loaded it!")
    if isinstance(error, commands.ExtensionError):
        await ctx.send(f"Extension error: ``{error}``.")

@unload.error
async def on_unload_error(ctx, error):
    if isinstance(error, commands.ExtensionNotLoaded):
        await ctx.send("Fool, you didn't load it!")

@reload.error
async def on_reload_error(ctx, error):
    if isinstance(error, commands.ExtensionNotLoaded):
        await ctx.send("Fool, you didn't load it!")
    if isinstance(error, commands.ExtensionAlreadyLoaded):
        await ctx.send("Fool, you already loaded it!")
    if isinstance(error, commands.ExtensionError):
        await ctx.send(f"Extension error: ``{error}``.")




@bot.event
async def on_command_error(ctx, error):
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
        await ctx.send(f"Command `{prefix}{ctx.invoked_with}` not found.")
        logging.warning(f"{time} {ctx.message.author} {ctx.message.id} caused the error \"{error}\" using the command "
                        f"{ctx.invoked_with}")
    if isinstance(error, RuntimeError):
        await ctx.send("Command already running.")
        logging.warning(f"{time} {ctx.message.author} {ctx.message.id} caused the error \"{error}\" using the command "
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
        await ctx.send_help(ctx.invoked_with)
    else:
        logging.warning(f"{time} {ctx.message.author} {ctx.message.id} {ctx.guild.id} caused the error \"{error}\" using the command "
                        f"{ctx.invoked_with}")

bot.run("ODM0ODkyMDM3MjE1NjE3MDk0.YIHfzQ.-UBhOq3ukC7kz3VTvUmpUBtjqaM")