from ShardBot import Shard
import discord
from discord.ext import commands
from discord import app_commands
import requests
import re
from bs4 import BeautifulSoup


class Roleplay(commands.Cog):
    def __init__(self, bot: Shard):
        self.bot = bot

    @commands.command(usage="[RSC/PPRC link]", aliases=['pprc_check'])
    @commands.guild_only()
    async def rsc_check(self, ctx, dispatch_link):
        dispatch_id = (re.findall('\d+', dispatch_link))[0]
        headers = {'User-Agent': 'Bassiliya'}
        params = {'q': 'dispatch',
                  'dispatchid': f"{dispatch_id}"}
        response = requests.get('https://www.nationstates.net/cgi-bin/api.cgi', headers=headers, params=params)
        if response.status_code != 200:
            return IndexError
        textsoup = BeautifulSoup(response.text, 'html.parser')
        dtext = textsoup.find('text').string
        numbers = re.findall(r'\d+?/100', dtext)
        numbers_list = list()
        total = 0
        for n in numbers:
            value = re.sub('/100', '', n)
            numbers_list.append(int(value))
            total += int(value)
        await ctx.send(f"Total: {total} points")
        return


async def setup(bot: Shard):
    await bot.add_cog(Roleplay(bot))
