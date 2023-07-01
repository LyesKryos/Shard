import re
import typing

import requests
from bs4 import BeautifulSoup
from discord import app_commands
from discord.ext import commands
from ShardBot import Shard
import discord
from ratelimiter import Ratelimiter
from customchecks import TooManyRequests
import asyncio


class Roleplay(commands.Cog):
    def __init__(self, bot: Shard):
        self.bot = bot
        self.rate_limit = Ratelimiter()

    @commands.command(usage="[RSC/PPRC link]", aliases=['pprc_check'],
                      brief="Calculates total points and percentages for a given dispatch")
    @commands.guild_only()
    async def rsc_check(self, ctx, dispatch_link):
        while True:
            # see if there are enough available calls. if so, break the loop
            try:
                await self.rate_limit.call()
                break
            # if there are not enough available calls, continue the loop
            except TooManyRequests as error:
                await asyncio.sleep(int(str(error)))
                continue
        # fetch dispatch id, establish headers and params, and make API call
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
        return await ctx.send(f"Total: {total} points\nTotal Percentages: {percents_total} percentage points")


    @commands.command(usage="[user]", aliases=['rpi'], brief="Gives information to a user about roleplay.")
    @commands.has_role(674278988323225632)
    async def roleplay_intro(self, ctx, user: discord.Member):
        # get channel
        thegye_server = self.bot.get_guild(674259612580446230)
        ooc_channel = thegye_server.get_channel(674337504933052469)
        await ooc_channel.send("**Welcome to Thegye RP!** \n\n"
                               "First, you should check out our roleplay dispatch located here: "
                               "https://www.nationstates.net/page=dispatch/id=1370630 It has all the information to get"
                               " you started in the world of Thegye roleplay. "
                               "However, before you dive into actual roleplay, you'll need to claim a place on the "
                               "regional map and fill out an RSC. \n**Map Dispatch:** "
                               "https://www.nationstates.net/page=dispatch/id=1310572 "
                               "*Note that the map on the dispatch is a bit older than the most updated one. "
                               "To view the most updated version, please use $nation_map in #bot_and_vc_chat"
                               " to see the most accurate map. \n**Roleplay Statistics Chart:** "
                               "https://www.nationstates.net/page=dispatch/id=1371516 \n\nOnce you've completed those "
                               "steps, feel free to jump into roleplay! Of course, "
                               f"let us know if you have any questions. Happy RPing, {user.mention}!")
        return

    @commands.command(brief="Sends the nation map image.")
    @commands.guild_only()
    async def nation_map(self, ctx):
        # establishes database
        conn = self.bot.pool
        # fetches link
        map_link = await conn.fetchrow('''SELECT link FROM roleplay WHERE name = 'map';''')
        return await ctx.send(f"{map_link['link']}")

    @commands.command(brief="Updates the nation map image.")
    @commands.guild_only()
    @commands.has_role(674338522962067478)
    async def edit_map(self, ctx, link: str):
        # establishes connection
        conn = self.bot.pool
        # updates link
        await conn.execute('''UPDATE roleplay SET link = $1 WHERE name = 'map';''', link)
        return await ctx.send("Map updated!")

    senate = app_commands.Group(name="senate", description="...")

    @senate.command(name="apply", description="Submits an application to become a Senator.")
    @app_commands.guild_only()
    @app_commands.describe(senator_name="The name of your Senator character.",
                           senator_constituency="The name of your Senator's constituency.",
                           senator_wiki_page="A URL to your Senator's page on the Thegye Wiki.")
    async def senate_apply(self, interaction: discord.Interaction, senator_name: str, senator_constituency: str,
                           senator_wiki_page: str = None):
        # defer interation
        await interaction.response.defer(thinking=False, ephemeral=True)
        # get the senator role
        thegye_server = self.bot.get_guild(674259612580446230)
        senator_role = thegye_server.get_role(1109211491170783293)
        # if the user already has the senator role, end the interaction
        if senator_role in interaction.user.roles:
            await interaction.followup.send("You already have the Senator role!")
            return
        # post information in #roleplay_mods
        mod_channel = self.bot.get_channel(674338490321862672)
        await mod_channel.send(f"{interaction.user.name} has applied for the mock government roleplay.\n"
                               f"Senator: {senator_name}\n"
                               f"Constituency: {senator_constituency}\n"
                               f"Wiki page: {senator_wiki_page}")
        # post information in #smoking_room
        smoking_room = self.bot.get_channel(1106961957002686464)
        await smoking_room.send(f"Senators, please welcome {senator_name} ({interaction.user.mention})"
                                f" to the Grand Senate of the United Kingdom of Thegye!\n\n"
                                f"Now that your application is approved, you can begin being involved by saying hello"
                                f"in the <https://discord.com/channels/674259612580446230/1112080185949437983>"
                                f" OOC chat or introducing your character in the "
                                f"<https://discord.com/channels/674259612580446230/1106961957002686464> IC chat."
                                f"You can also check out current legislation on the #floor, "
                                f"proposals in #the_chancellery, and the most recent news in the #newsroom. You can"
                                f"also create an account on our dedicated wiki (<https://thegye.miraheze.org/>),"
                                f"where legislation, characters, Ministry of Information Reports, and more are stored"
                                f"and created. If you have questions, feel free to ask them in "
                                f"<https://discord.com/channels/674259612580446230/1112080185949437983>. "
                                f"Once again, welcome!")
        await interaction.user.add_roles(senator_role)
        await interaction.followup.send("Application submitted!")

    @senate.command(name="open_debate", description="Allows the Chancellor to open debate on legislation.")
    @app_commands.guild_only()
    @app_commands.checks.has_role(1110374275740868628)
    @app_commands.describe(title="The official title of the legislation", author="The full name of the Senator.",
                           url="Link to the wiki page of the legislation")
    async def open_debate(self, interaction: discord.Interaction, title: str, author: str, url: str):
        # defer interaction
        await interaction.response.defer(thinking=False, ephemeral=True)
        # get the forum channel
        floor_channel = self.bot.get_channel(1106963321896325241)
        # get the senator role
        thegye_server = self.bot.get_guild(674259612580446230)
        senator_role = thegye_server.get_role(1109211491170783293)
        # create a new thread
        content_string = f"Presented by Senator {author}.\n" \
                         f"{url}\n" \
                         f"{senator_role.mention}s, this bill is now open for debate."
        thread = await floor_channel.create_thread(name=title, content=content_string)
        # pin the first message
        await thread.message.pin()
        # add tupper
        tupper = self.bot.get_user(431544605209788416)
        await thread.thread.add_user(tupper)
        await interaction.followup.send("Done!")
        return

    @senate.command(name="party_role", description="Allows party leaders to add party roles.")
    @app_commands.guild_only()
    @app_commands.checks.has_role(1124422828641505300)
    async def party_role(self, interaction: discord.Interaction, senator: discord.Member, role: discord.Role):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # get the senator role
        thegye_server = self.bot.get_guild(674259612580446230)
        senator_role = thegye_server.get_role(1109211491170783293)
        # check for role
        if senator_role not in senator.roles:
            await interaction.followup.send(f"{senator} is not a member of the Grand Senate of Thegye.")
            return
        # get party roles
        bullturtle_party = thegye_server.get_role(1112893883832086622)
        rrp = thegye_server.get_role(1112894000995762266)
        party_roles = [bullturtle_party, rrp]
        # check to make sure the role is right
        if role not in party_roles:
            await interaction.followup.send(f"{role.name} is not a party role.")
            return
        # if the user does not have the role, add the role
        if role not in senator.roles:
            await senator.add_roles(role)
            await interaction.followup.send(f"{role.name} added to {senator.nick}.")
        # if the user has the role, remove the role
        if role in senator.roles:
            await senator.remove_roles(role)
            await interaction.followup.send(f"{role.name} removed from {senator.nick}.")
        return


async def setup(bot: Shard):
    await bot.add_cog(Roleplay(bot))
