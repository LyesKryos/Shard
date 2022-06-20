import re
import requests
from bs4 import BeautifulSoup
from discord.ext import commands
from ShardBot import Shard


class Roleplay(commands.Cog):
    def __init__(self, bot: Shard):
        self.bot = bot

    @commands.command(usage="[RSC/PPRC link]", aliases=['pprc_check'],
                      brief="Calculates total points and percentages for a given dispatch")
    @commands.guild_only()
    async def rsc_check(self, ctx, dispatch_link):
        # fetch dispatch id, establish headers and params, and make API call
        dispatch_id = (re.findall('\d+', dispatch_link))[0]
        headers = {'User-Agent': 'Bassiliya'}
        params = {'q': 'dispatch',
                  'dispatchid': f"{dispatch_id}"}
        response = requests.get('https://www.nationstates.net/cgi-bin/api.cgi', headers=headers, params=params)
        # if the call is rejected or otherwise causes an issue
        if response.status_code != 200:
            return IndexError
        # parse the html and pull out all numbers followed by /100
        textsoup = BeautifulSoup(response.text, 'html.parser')
        dtext = textsoup.find('text').string
        numbers = re.findall(r'\d+?/100', dtext)
        total = 0
        # add all numbers together
        for n in numbers:
            value = re.sub('/100', '', n)
            total += int(value)
        # find and add all percents together
        percents = re.findall(r'\d+?&#37', dtext)
        percents_total = 0
        for p in percents:
            value = re.sub('&#37', '', p)
            percents_total += int(value)
        # send totals
        await ctx.send(f"Total: {total} points\nTotal Percentages: {percents_total} percentage points")
        return


async def setup(bot: Shard):
    await bot.add_cog(Roleplay(bot))
