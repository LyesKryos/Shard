import re
import requests
from bs4 import BeautifulSoup
from discord.ext import commands
from ShardBot import Shard


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
        total = 0
        for n in numbers:
            value = re.sub('/100', '', n)
            total += int(value)
        percents = re.findall(r'\d+?&#37', dtext)
        percents_total = 0
        for p in percents:
            value = re.sub('&#37', '', p)
            percents_total += int(value)
        await ctx.send(f"Total: {total} points\nTotal Percentages: {percents_total} percentage points")
        return


def setup(bot: Shard):
    bot.add_cog(Roleplay(bot))
