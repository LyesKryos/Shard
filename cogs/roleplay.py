import re
import requests
from bs4 import BeautifulSoup
from discord.ext import commands
from ShardBot import Shard
import discord


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

    @commands.command(usage="[user]", aliases=['rpi'], brief="Gives information to a user about roleplay.")
    @commands.has_role(674278988323225632)
    async def roleplay_intro(self, ctx, user: discord.Member):
        # get channel
        thegye_server = self.bot.get_guild(674259612580446230)
        ooc_channel = thegye_server.get_channel(674337504933052469)
        await ooc_channel.send("Welcome to Thegye RP! \n\n"
                               "First, you should check out our roleplay dispatch located here: "
                               "https://www.nationstates.net/page=dispatch/id=1370630 It has all the information to get"
                               " you started in the world of Thegye roleplay. "
                               "However, before you dive into actual roleplay, you'll need to claim a place on the "
                               "regional map and fill out an RSC. \nMap Dispatch: "
                               "https://www.nationstates.net/page=dispatch/id=1310572 "
                               "*Note that the map on the dispatch is a bit older than the most updated one. "
                               "If you want to view the most updated version, please use >nation_map in bot_and_vc_chat "
                               "to see the most accurate map. \nRoleplay Statistics Chart: "
                               "https://www.nationstates.net/page=dispatch/id=1371516 \n\n Once you've completed those "
                               "steps, feel free to jump into roleplay! Of course, "
                               f"let us know if you have any questions. Happy RPing, {user.mention}!")
        return


async def setup(bot: Shard):
    await bot.add_cog(Roleplay(bot))
