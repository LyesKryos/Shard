import re
import typing

import requests
from bs4 import BeautifulSoup
from discord import app_commands, utils
from discord.ext import commands
from ShardBot import Shard
import discord
from ratelimiter import Ratelimiter
from customchecks import TooManyRequests
import asyncio
import typing
import math


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
        return await ctx.send(f"Total: {total}/**1300** points\n"
                              f"Total Percentages: {percents_total-20}/**300** percentage points")


    @app_commands.command(name="roleplay_intro", description="Sends information concerning the roleplay to new RPers.")
    @app_commands.describe(user="The user being introduced")
    async def roleplay_intro(self, interaction: discord.Interaction, user: discord.Member):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # get channel
        thegye_server = self.bot.get_guild(674259612580446230)
        rp_mod_role = thegye_server.get_role(674338522962067478)
        if rp_mod_role not in interaction.user.roles:
            return await interaction.followup.send("You do not have the appropriate role for this command.",
                                                   ephemeral=True)
        ooc_channel = thegye_server.get_channel(674337504933052469)
        await ooc_channel.send("**Welcome to Thegye RP!** \n\n"
                               "First, you should check out our roleplay dispatch located here: "
                               "[**Roleplay Dispatch**](https://www.nationstates.net/page=dispatch/id=1370630)"
                               " It has all the information to get you started in the world of Thegye roleplay. "
                               "However, before you dive into actual roleplay, you'll need to claim a place on the "
                               "regional map and fill out an RSC. \n[**Map Dispatch:**]("
                               "https://www.nationstates.net/page=dispatch/id=1310572) "
                               "*Note that the map on the dispatch is a bit older than the most updated one. "
                               "To view the most updated version, please use $nation_map in #bot_and_vc_chat"
                               " to see the most accurate map. \n[**Roleplay Statistics Chart**]("
                               "https://www.nationstates.net/page=dispatch/id=1371516) \n\nOnce you've completed those "
                               "steps, feel free to jump into roleplay! Be sure to check out our "
                               "[**iiWiki page**](<https://iiwiki.us/wiki/Portal:Thegye>) too. Of course, "
                               f"let us know if you have any questions. Happy RPing, {user.mention}!")
        return await interaction.followup.send("Done!")

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
        backroom = self.bot.get_channel(1112080185949437983)
        floor = self.bot.get_channel(1106963321896325241)
        chancellery = self.bot.get_channel(1106962638723887204)
        newsroom = self.bot.get_channel(1106962988960845925)
        await smoking_room.send(f"Senators, please welcome {senator_name} of {senator_constituency} "
                                f"({interaction.user.mention}) to the Grand Senate of the United Kingdom of Thegye!\n\n"
                                f"Now that your application is approved, you can begin being involved by saying hello "
                                f"in the {backroom.mention} OOC chat or introducing your character in the "
                                f"{smoking_room.mention} IC chat. You can also check out current legislation on the "
                                f"{floor.mention}, proposals in {chancellery.mention}, and the most recent news in the "
                                f"{newsroom.mention}. You can also create an account on our dedicated wiki "
                                f"(<https://thegye.miraheze.org/>), where legislation, characters, "
                                f"Ministry of Information Reports, and more are created and stored. "
                                f"If you have questions, feel free to ask them in {backroom.mention}. "
                                f"Once again, welcome!")
        await interaction.user.add_roles(senator_role)
        await interaction.followup.send("Application submitted!")
        return

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
        tags = floor_channel.available_tags
        for t in tags:
            if t.name == "Debating":
                debating = t
        thread = await floor_channel.create_thread(name=title, content=content_string,
                                                   applied_tags=[debating])
        # pin the first message
        await thread.message.pin()
        # add tupper
        tupper = self.bot.get_user(431544605209788416)
        await thread.thread.add_user(tupper)
        await interaction.followup.send("Done!")
        return

    @senate.command(name="create_party", description="Adds a new party to the Grand Senate.")
    @app_commands.describe(party_name="The name of the party. Please spell and capitalize correctly.",
                           party_color="Hex code of the party role. Ex: #123456",
                           leader="The player to be assigned the Party Leader role.")
    @app_commands.checks.has_any_role(674260151506698251, 1110374275740868628)
    async def add_party(self, interaction: discord.Interaction, party_name: str, party_color: str,
                        leader: discord.Member):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # create party role
        thegye_server = self.bot.get_guild(674259612580446230)
        senator_position = thegye_server.get_role(1109211491170783293).position
        new_party_role = await thegye_server.create_role(name=party_name, color=discord.Color.from_str(party_color))
        await new_party_role.edit(position=senator_position-1)
        # assign the role to the leader
        party_leader_role = thegye_server.get_role(1124422828641505300)
        await leader.add_roles(party_leader_role, new_party_role)
        # create a party room
        overwrites = {
            thegye_server.default_role: discord.PermissionOverwrite(view_channel=False),
            new_party_role: discord.PermissionOverwrite(read_messages=True, view_channel=True),
            party_leader_role: discord.PermissionOverwrite(manage_channels=True)
        }
        party_info_position = thegye_server.get_channel(1110371598487269417).position
        senate_category = utils.get(thegye_server.categories, name="The Grand Senate")
        party_channel = await thegye_server.create_text_channel(name=party_name, overwrites=overwrites,
                                                          position=party_info_position+1, category=senate_category,
                                                                topic=f"The party channel for {party_name}.")
        # define tupper and poll bots
        tupper = thegye_server.get_member(431544605209788416)
        poll_bot = thegye_server.get_member(437618149505105920)
        await party_channel.set_permissions(tupper, read_messages=True, send_messages=True, manage_messages=True)
        await party_channel.set_permissions(poll_bot, read_messages=True, send_messages=True)
        # update the database
        await conn.execute('''INSERT INTO senate_parties(name, role_id, party_leader, party_room) 
        VALUES ($1, $2, $3, $4);''',
                           party_name, new_party_role.id, leader.id, party_channel.id)
        # send message
        await interaction.followup.send(f"Party role {new_party_role.name} has been added to the Grand Senate.\n"
                                               f"Party leader assigned to {leader.display_name}.")
        return await party_channel.send(content=f"{party_leader_role.mention} of {new_party_role.mention}, "
                                                f"your party has been added to the Grand Senate of Thegye. "
                                                f"This channel will act as your party's official private channel. "
                                                f"The Party Leader will have control over the channel.")

    @senate.command(name="remove_party", description="Removes an inactive party from the Grand Senate. "
                                                     "USE WITH CAUTION.")
    @app_commands.checks.has_any_role(674260151506698251, 1110374275740868628)
    @app_commands.guild_only()
    async def remove_party(self, interaction: discord.Interaction, party_name: discord.Role):
        # defer interaction
        await interaction.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # search for party role
        party_info = await conn.fetchrow('''SELECT * FROM senate_parties WHERE role_id = $1;''', party_name.id)
        # if the party doesn't exist, return such
        if party_info is None:
            return await interaction.followup.send("That party does not exist.")
        # otherwise, carry on
        else:
            # get role
            thegye_server = self.bot.get_guild(674259612580446230)
            party_role = thegye_server.get_role(party_info['role_id'])
            # delete role






    @senate.command(name="party_role", description="Allows party leaders to add and remove party roles.")
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
            await interaction.followup.send(f"{senator.display_name} is not a member of the Grand Senate of Thegye.")
            return
        # pull party data
        conn = self.bot.pool
        party_data = await conn.fetch('''SELECT * FROM senate_parties WHERE active = True;''')
        party_roles = list()
        for party in party_data:
            party_roles.append(thegye_server.get_role(party['role_id']))
        # check to make sure the role is right
        if role not in party_roles:
            await interaction.followup.send(f"{role.name} is not a party role.")
            return
        # if the user does not have the role, add the role
        if role not in senator.roles:
            await senator.add_roles(role)
            await interaction.followup.send(f"{role.name} added to {senator.display_name}.")
        # if the user has the role, remove the role
        if role in senator.roles:
            await senator.remove_roles(role)
            await interaction.followup.send(f"{role.name} removed from {senator.display_name}.")
        return

    @senate.command(name="convert_thaler", description="Calculates the conversion of thaler.")
    @app_commands.describe(amount_in="The amount to be converted.", from_currency="The starting currency.",
                           to_currency="The currency to be converted to.")
    @app_commands.guild_only()
    async def convert_thaler(self, interaction: discord.Interaction, amount_in: float, from_currency:
    typing.Literal ['Thaler', '1880 USD', '1880 GBP', '2024 USD', '2024 GBP'], to_currency:
    typing.Literal ['Thaler', '1880 USD', '1880 GBP', '2024 USD', '2024 GBP']):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # define the rates
        Thaler = 1
        PPP = 2.2
        USD1880_out = Thaler * .2 * PPP
        USD1880_in = (Thaler / .2) / PPP
        GBP1880_out = Thaler * .2 * PPP
        GBP1880_in = (Thaler / .2) / PPP
        USD2024_out = USD1880_out * 30.62
        USD2024_in = USD1880_in * .03
        GBP2024_out = GBP1880_out * 150.76
        GBP2024_in = GBP1880_in * .01
        # select the option for from_currency
        if from_currency == "Thaler":
            from_currency_calc = Thaler
        elif from_currency == "1880 USD":
            from_currency_calc = USD1880_in
        elif from_currency == "1880 GBP":
            from_currency_calc = GBP1880_in
        elif from_currency == "2024 USD":
            from_currency_calc = USD2024_in
        elif from_currency == "2024 GBP":
            from_currency_calc = GBP2024_in
        else:
            symbol = None
            return await interaction.followup.send("Please select a listed option.")
        # select the option for to_currency
        if to_currency == "Thaler":
            to_currency_calc = Thaler
            symbol = "\u20B8"
        elif to_currency == "1880 USD":
            to_currency_calc = USD1880_out
            symbol = "\u0024"
        elif to_currency == "1880 GBP":
            to_currency_calc = GBP1880_out
            symbol = "\u00A3"
        elif to_currency == "2024 USD":
            to_currency_calc = USD2024_out
            symbol = "\u0024"
        elif to_currency == "2024 GBP":
            to_currency_calc = GBP2024_out
            symbol = "\u00A3"
        else:
            return await interaction.followup.send("Please select a listed option.")
        conversion = float((amount_in * from_currency_calc) * to_currency_calc)
        if to_currency == "Thaler":
            return await interaction.followup.send(f"{round(conversion, 3):,.3f}{symbol}")
        else:
            return await interaction.followup.send(f"{symbol}{round(conversion, 3):,.3f} ({to_currency})")

    @senate.command(name="divide_thaler",
                    description="Display the division of a given amount of thaler into respective parts.")
    @app_commands.describe(amount_in="The amount of Thaler to be divided.")
    @app_commands.guild_only()
    async def divide_thaler(self, interaction: discord.Interaction, amount_in: float):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # divide into parts
        thaler = math.floor(amount_in/1)
        dire = math.floor((amount_in-thaler)/(1/18))
        komat = math.ceil(((amount_in-thaler)-(dire*(1/18)))/(1/216))
        await interaction.followup.send(f"{thaler:,}\u20B8 {dire}\u1E9F {komat}\u04A1")

    @senate.command(name="count_members", description="Display the partisan division of the Grand Senate of Thegye.")
    @app_commands.guild_only()
    async def count_members(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # define the server
        thegye_server = self.bot.get_guild(674259612580446230)
        # count senator roles
        senator_role = thegye_server.get_role(1109211491170783293)
        senator_number = len(senator_role.members)
        # count party roles
        conn = self.bot.pool
        parties = await conn.fetch('''SELECT * FROM senate_parties WHERE active = True;''')
        party_roles = list()
        for p in parties:
            party_roles.append(thegye_server.get_role(p['role_id']))
        # construct message
        message = "**Senators**: 540\n"
        senators_in_parties = 0
        for p in party_roles:
            message += f"{p.name}: {math.floor((len(p.members)/senator_number)*540)}\n"
            senators_in_parties += math.floor((len(p.members)/senator_number)*540)
        message += f"Independents: {540-senators_in_parties}\n"
        message += "\n\n*Note: these numbers are provisional and are not official.*"
        # send message
        return await interaction.followup.send(message)



async def setup(bot: Shard):
    await bot.add_cog(Roleplay(bot))