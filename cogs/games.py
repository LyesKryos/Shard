import asyncio
import discord.errors
from ShardBot import Shard
from discord.ext import commands
from customchecks import SilentFail
from pkgutil import iter_modules
EXTENSIONS = [module.name for module in iter_modules(__path__, f'{__package__}.')]

class Games(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def valheim(self, ctx):
        # establish pool
        conn = self.bot.pool
        # check for an existing entry
        user_info = await conn.fetchrow('''SELECT * FROM games WHERE game = 'Valheim' AND user_id = $1;''',
                                        ctx.author.id)
        # fetch game information
        valheim_info = await conn.fetchrow('''SELECT * FROM games_info WHERE game_name = 'Valheim';''')
        if user_info is not None:
            # if the user already exists and is not banned, send them the port and password
            if user_info['banned'] is False:
                return await ctx.author.send(f"Server Name: {valheim_info['server_name']}\n"
                                             f"Server Port: {valheim_info['server_port']}\n"
                                             f"Server Password: ||{valheim_info['server_password']}||\n"
                                             f"Server Rules: https://www.nationstates.net/page=dispatch/id=1794380\n\n"
                                             f"**Remember that sharing server access information with others is against "
                                             f"the rules and can lead to a permanent ban.**")
            elif user_info['banned'] is True:
                return await ctx.send("You are banned from playing Valheim in the Thegye server.")

    @commands.command()
    @commands.guild_only()
    async def minecraft(self, ctx):
        await ctx.send("Sending you a DM!")
        # send information
        return await ctx.author.send(f"Server IP: `71.206.132.216`\n"
                                     f"Server port: `:25565`\n"
                                     f"Server Rules: https://www.nationstates.net/page=dispatch/id=1840173")

async def setup(bot: Shard):
    # define the cog and add the cog
    cog = Games(bot)
    await bot.add_cog(cog)
