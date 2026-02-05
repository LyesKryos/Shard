import random
import re
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

    @app_commands.command(description="Rolls a dice as specified.")
    @app_commands.describe(dice="The type of dice to be rolled. For example: 1d6 or d10 or 10d20.",
                           modifier="The modifier to be added to the outcome. For example: +1, -4.")
    async def roll(self, interaction: discord.Interaction,  dice: str, modifier: int = 0):
        # parse dice
        dice_data = dice.split("d")
        # check the amount of dice
        if dice_data[0] == "":
            dice_amount = 1
        else:
            dice_amount = int(dice_data[0])
        # check type of dice
        try:
            dice_type = int(dice_data[1])
        except ValueError:
           return await interaction.response.send_message(f"I do not know what kind of dice a {dice_data[1]} is!")
        # calculate the dice
        rolls = 0
        outcome = 0
        while rolls < dice_amount:
            outcome = random.randint(1, dice_type) + modifier
            rolls += 1
        return await interaction.response.send_message(f"Roll: {outcome}")



    # === SENATE COMMANDS ===

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
        await interaction.response.defer(thinking=True)
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
            party_room = thegye_server.get_channel(party_info['party_room'])
            party_leader = thegye_server.get_member(party_info['party_leader'])
            party_leader_role = thegye_server.get_role(1124422828641505300)
            # delete role
            await party_role.delete()
            # archive room
            archive_category = utils.get(thegye_server.categories, name="Archive")
            await party_room.move(category=archive_category, beginning=True)
            await party_room.edit(sync_permissions=True)
            # remove leader
            await party_leader.remove_roles(party_leader_role)
            await conn.execute('''UPDATE senate_parties SET active = False WHERE role_id = $1;''', party_name.id)
            return await interaction.followup.send(f"{party_name.name} has been removed from the Grand Senate.")

    @senate.command(name="alter_leader", description="Alter the party leader for a given party.")
    @app_commands.checks.has_any_role(674260151506698251, 1110374275740868628)
    @app_commands.guild_only()
    @app_commands.describe(party_name="The name of the party that needs a new leader.",
                           new_leader="The player that is the new leader of the party.")
    async def alter_leader(self, interaction: discord.Interaction, party_name: discord.Role, new_leader: discord.Member):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # search for party role
        party_info = await conn.fetchrow('''SELECT * FROM senate_parties WHERE role_id = $1;''', party_name.id)
        # if the party doesn't exist, return such
        if party_info is None:
            return await interaction.followup.send("That party does not exist.")
        # otherwise, carry on
        else:
            # define server
            thegye_server = self.bot.get_guild(674259612580446230)
            leader_role = thegye_server.get_role(1124422828641505300)
            party_role = thegye_server.get_role(party_info['role_id'])
            # if the new leader isn't in the party
            if party_role not in new_leader.roles:
                # return denial message
                return await interaction.followup.send(f"{new_leader.display_name} is not a "
                                                       f"member of {party_name.name}.")
            # remove the previous leader
            previous_leader = thegye_server.get_member(party_info['party_leader'])
            await previous_leader.remove_roles(leader_role)
            # add leader role to new leader
            await new_leader.add_roles(leader_role)
            return await interaction.followup.send(f"{new_leader.display_name} is now party leader "
                                                   f"of {party_name.name}.")

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
    typing.Literal ['Thaler', '1895 USD', '1895 GBP', '2025 USD', '2025 GBP'], to_currency:
    typing.Literal ['Thaler', '1895 USD', '1895 GBP', '2025 USD', '2025 GBP'], consider_ppp: bool = False):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # determine codes for the various symbols
        currency_symbols = {"1895 USD":"\U00000024","1895 GBP":"\U000000a3","2025 USD":"\U00000024","2025 GBP":"\U000000a3","Thaler":"\U000020b8"}
        # remember that Thaler = 1/ (Currency Strength/100) (representing 100 CS = Int'l (1990) $1)
        # the rates are all in Int'l (1990) dollars: 1 INTL $ = 1.84 Thaler, 1 INTL $ = 0.34 1895 USD
        currency_rates = {"Thaler": 1.84,"1895 USD":.34,"1895 GBP":.070,"2025 USD":2.54,"2025 GBP":.31}
        # define the PPP rates
        USD_PPP = 1.08
        # remember that the GBP PPP to the International Dollar 2000 is 0.67
        GBP_PPP = .7236
        # calculate the conversion
        exchange = (currency_rates[to_currency]/currency_rates[from_currency]) * amount_in
        # if the ppp is to be considered, multiply by that
        if consider_ppp:
            # if the from or to is not the thaler, disallow, as the PPP doesn't matter for the other currencies
            if "Thaler" not in from_currency and "Thaler" not in to_currency:
                return await interaction.followup.send("The PPP does not apply to the conversion of "
                                                       "currencies other than the Thaler.")
            # if the currency is USD, multiply by the PPPq
            if "USD" in from_currency:
                exchange /= USD_PPP
            elif "USD" in to_currency:
                exchange *= USD_PPP
            elif "GBP" in from_currency:
                exchange /= GBP_PPP
            elif "GBP" in to_currency:
                exchange *= GBP_PPP
        # return the display of the conversion
        # "," > with thousands separator
        # ".3" > with 3 decimal places
        # "f" > with fixed-point notation
        return await interaction.followup.send(f"{currency_symbols[to_currency]}{exchange:,.3f}")

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
        message = f"**Senators**: 540 ({senator_number} players)\n"
        senators_in_parties = 0
        players_in_parties = 0
        for p in party_roles:
            message += f"{p.name}: {math.floor((len(p.members)/senator_number)*540)} ({len(p.members)} players)\n"
            senators_in_parties += math.floor((len(p.members)/senator_number)*540)
            players_in_parties += len(p.members)
        message += f"Independents: {540-senators_in_parties} ({senator_number-players_in_parties} players)\n"
        message += "\n*Note: these numbers are provisional and are not official.*"
        # send message
        return await interaction.followup.send(message)

async def setup(bot: Shard):
    await bot.add_cog(Roleplay(bot))
