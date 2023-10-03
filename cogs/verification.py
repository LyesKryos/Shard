# Shard Verification 0.1b
import traceback
from datetime import datetime, timedelta
import discord.channel
from discord import app_commands
from discord.ui import View

from ShardBot import Shard
import asyncio
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import re
from pytz import timezone
import aiohttp
from typing import Optional

from customchecks import TooManyRequests
from ratelimiter import Ratelimiter


class VerificationView(View):
    def __init__(self, member, message, bot):
        self.member = member
        self.message = message
        super().__init__(timeout=300)
        self.add_item(VerificationDropdown(member, bot, message))

    async def on_timeout(self) -> None:
        # remove dropdown
        '''''''''''for item in self.children:
            self.remove_item(item)
        return await self.message.edit(content="Timed out. Please respond next time!", view=self)'''''''''''


class VerificationDropdown(discord.ui.Select):

    def __init__(self, member, bot, message):
        # define bot
        self.bot = bot
        # define message
        self.message = message
        self.member = member
        # define page
        self.page = 1
        # define options
        options = [
            discord.SelectOption(label="NationStates",
                                 description="You already have a NationStates account.",
                                 emoji="<:thegyeofficialflag:1098650865331613836>"),
            discord.SelectOption(label="Geopolitical Roleplay",
                                 description="You're here to roleplay within the Thegye geopolitical universe!",
                                 emoji="\U0001f310"),
            discord.SelectOption(label="Grand Senate of Thegye Roleplay",
                                 description="You're here to roleplay as a Senator of the United Kingdom of Thegye!",
                                 emoji="\U0001f3e6"),
            discord.SelectOption(label="Other",
                                 description="You have ulterior motives!",
                                 emoji="\U0001f575")
        ]

        super().__init__(placeholder="Choose which option best describes you...",
                         min_values=1, max_values=4, options=options)

    def sanitize_links_underscore(self, userinput: str) -> str:
        """Replaces spaces with proper, url-friendly underscores"""
        to_regex = userinput.replace(" ", "_")
        return re.sub(r"[^a-zA-Z0-9_-]", ' ', to_regex)

    async def callback(self, interaction: discord.Interaction):
        try:
            # establish connection
            conn = self.bot.pool
            # define roles
            thegye_server = self.bot.get_guild(674259612580446230)
            user = thegye_server.get_member(self.member)
            unverified_role = thegye_server.get_role(1028144304507592704)
            nationstates_role = thegye_server.get_role(1150861314424573992)
            roleplay_role = thegye_server.get_role(674339122491424789)
            traveler_role = thegye_server.get_role(674280677268652047)
            gatehouse = thegye_server.get_channel(674284159128043530)
            user = self.member
            # delete message
            await self.message.delete()
            # assign roles for nationstates
            for response in self.values:
                # assign roles for nation RP
                if response == "Geopolitical Roleplay":
                    await user.remove_roles(unverified_role)
                    await user.add_roles(roleplay_role, traveler_role)
                    ooc_chat = thegye_server.get_channel(674337504933052469)
                    await ooc_chat.send(f"Welcome to the Geopolitical Roleplay channels, {user.mention}!\n\n"
                                        f"These channels are used solely for the geopolitical roleplay within the Thegye "
                                        f"universe. Here you can browse current RPs, participate in worldbuilding, and chat"
                                        f" with your fellow RPers. If you'd like to join our RP, you will need to:\n"
                                        f"**1.** Have a nation within the [**Thegye NationStates region**]"
                                        f"(<https://www.nationstates.net/region=thegye>)\n"
                                        f"**2.** Fill out the [**Roleplay Statistics Chart**]"
                                        f"(<https://www.nationstates.net/page=dispatch/id=1371516>) and follow the "
                                        f"instructions to submit it for verification.\n"
                                        f"**3.** Apply for a location on the [**nation map**]"
                                        f"(<https://www.nationstates.net/page=dispatch/id=1310572>)\n\n"
                                        f"After you have completed those steps, you are ready to go! Check out our "
                                        f"[**roleplay dispatch**](<https://www.nationstates.net/page=dispatch/id=1370630>)"
                                        f" and our [**iiWiki page**](<https://iiwiki.us/wiki/Portal:Thegye>) for more "
                                        f"information! Feel free to let us know if you have any questions.")
                # assign roles for Senate RP
                if response == "Grand Senate of Thegye Roleplay" in self.values:
                    await user.remove_roles(unverified_role)
                    await user.add_roles(traveler_role)
                    backroom_channel = thegye_server.get_channel(1112080185949437983)
                    await backroom_channel.send(f"Welcome to the Grand Senate of Thegye, {user.mention}!\n\n"
                                                f"To apply for the Senate role, just use the `/senate apply` command and "
                                                f"fill out all the required fields. If you've like to find more information"
                                                f" about our roleplay and how you can participate before applying, "
                                                f"be sure to check out our [dedicated wiki]"
                                                f"(<https://thegye.miraheze.org/wiki/Main_Page>) where you can find helpful"
                                                f" information and more! Be sure to let us know if you have any questions.")
                # assign roles for other
                if response == "Other" in self.values:
                    await user.add_roles(traveler_role)
                if response == "NationStates":
                    # add the nationstates role
                    await user.add_roles(nationstates_role)
                    await gatehouse.send(message="I am sending you a DM!")
                    # send the user a DM asking for a nation
                    try:
                        verify_dm = await user.create_dm()
                        await verify_dm.send("Please reply in this DM with your nation's name. "
                                             "Please only include the nation's offical name; for example, "
                                             "if your nation appears as \"The Botique Empire of Bassiliya\", "
                                             "please enter only \"Bassiliya\".")
                    except discord.Forbidden:
                        # send a message welcoming the user
                        open_square = thegye_server.get_channel(674335095628365855)
                        await open_square.send(f"The gods have sent us {user.mention}! Welcome, traveler, "
                                               f"and introduce yourself!")
                        return await gatehouse.send(
                            f"{user.mention}, I can't DM you! This could be for a few reasons: \n\n"
                            f"1. You have me blocked. Sad. \U0001f614 \n"
                            f"2. You are no longer in this server or any server we share. "
                            f"*Come back!*\n"
                            f"3. You accept DMs only from users you have in your Friends list. "
                            f"In order to allow me to DM you, go to `Settings > "
                            f"Privacy & Safety > Server Privacy Defaults` and toggle **ON** the"
                            f" `Allow direct messages from server members.\n\n"
                            f"Once you have fixed any of the aforementioned issues"
                            f", please use the `/verification verify` command again to complete"
                            f" the verification process.")

                    # checks to make sure the author is the author and the guild is a DM
                    def authorcheck(message):
                        return user.id == message.author.id and message.guild is None

                    try:
                        nation_reply = await self.bot.wait_for('message', check=authorcheck, timeout=300)
                    except asyncio.TimeoutError:
                        await user.add_role(traveler_role)
                        return await verify_dm.send("Timed out. Please answer me next time!")
                    # get the content
                    nation = nation_reply.content
                    # if content is cancel, cancel
                    if nation.lower() == "cancel":
                        await user.add_role(traveler_role)
                        return await verify_dm.send("Cancelling!")
                    # checks to see if the user has already verified yet or not
                    verified_check = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''',
                                                         user.id)
                    # if the user has no verified nations
                    if verified_check is None:
                        # sends DM to initiate verification
                        await verify_dm.send(f"**Welcome to the Shard Verification, {user.name}!** \n\n"
                                             f"To begin the verification process, please login to {nation}. "
                                             f"Here is a URL to your nation page: https://www.nationstates.net/nation="
                                             f"{self.sanitize_links_underscore(nation)}")
                    # if the user does have some verified nation(s)
                    else:
                        # sends DM to initiate verification
                        await verify_dm.send(f"**Welcome back to the Shard Verification, {user.name}!** \n\n"
                                             f"To begin the verification process, please login to {nation}. "
                                             f"Here is a URL to your nation page: https://www.nationstates.net/nation="
                                             f"{self.sanitize_links_underscore(nation)}")
                    # waits for the user to reply with their nation
                    headers = {"User-Agent": "Bassiliya"}
                    nation_exist = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={nation}",
                                                headers=headers)
                    # if the nation does not exist, let the user know
                    if nation_exist.status_code == 404:
                        await verify_dm.send(
                            f"No such nation as `{nation}`. Please check that you are using only the nation's"
                            f" name, without the pretitle. **You will need to use the `/verify` command again.**")
                        return await user.add_role(traveler_role)
                    # get official nation name
                    nation_raw = nation_exist.text
                    nation_soup = BeautifulSoup(nation_raw, 'lxml')
                    nation_name = nation_soup.find('name').text
                    # if the user has already verified that nation
                    if verified_check is not None:
                        if nation_name.lower() in [n.lower() for n in verified_check['nations']]:
                            return await verify_dm.send(
                                f"You have already verified `{nation_name}`. To view your verified nations, "
                                f"use `/view_verified`.")
                    # send verification instructions via DM
                    await verify_dm.send(
                        f"Please login to {nation_name}. Once complete, head to this link and send me the "
                        f"verification code displayed: https://www.nationstates.net/page=verify_login. "
                        f"You may give the code displayed to an external website or tool, like me, "
                        f"which can use it to verify that you are indeed currently logged in as this nation. "
                        f"This is *all* I can do with it: It does not allow me to access your nation.")
                    # wait for response
                    try:
                        code_reply = await self.bot.wait_for('message', check=authorcheck, timeout=300)
                    except asyncio.TimeoutError:
                        await user.add_role(traveler_role)
                        return await verify_dm.send("Verification timed out. Please answer me next time!")
                    # define headers and parameters
                    params = {'a': 'verify',
                              'nation': nation_name,
                              'checksum': code_reply.content,
                              'q': 'region+wa'}
                    # start session
                    async with aiohttp.ClientSession() as verify_session:
                        # call for necessary data
                        async with verify_session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                                      headers=headers, params=params) as verifying:
                            await asyncio.sleep(.6)
                            # parse the verification response
                            verification_raw = await verifying.text()
                            verification_soup = BeautifulSoup(verification_raw, 'lxml')
                            # fetch verification
                            verification = verification_soup.verify.string
                            # if the verification code is good
                            if int(verification) == 1:
                                # if the user has no verified nation, add a new row
                                if verified_check is None:
                                    await conn.execute(
                                        '''INSERT INTO verified_nations(user_id, main_nation) VALUES ($1, $2);''',
                                        user.id, nation_name)
                                    # if the nation's region is Thegye, add the Thegye role
                                    if verification_soup.region.text == "Thegye":
                                        thegye_role = thegye_server.get_role(674260547897917460)
                                        user = thegye_server.get_member(user.id)
                                        # if the nation is in the WA, add the WA role
                                        if verification_soup.unstatus.text != "Non-member":
                                            wa_role = thegye_server.get_role(674283915870994442)
                                            await user.add_roles(wa_role)
                                        await user.add_roles(thegye_role)
                                    # if the nation's region is Karma, add the Karma role
                                    elif verification_soup.region.text == "Karma":
                                        thegye_server = self.bot.get_guild(674259612580446230)
                                        karma_role = thegye_server.get_role(771456227674685440)
                                        user = thegye_server.get_member(user.id)
                                        await user.add_roles(karma_role)
                                    # otherwise, add the traveler role
                                    else:
                                        thegye_server = self.bot.get_guild(674259612580446230)
                                        traveler_role = thegye_server.get_role(674280677268652047)
                                        user = thegye_server.get_member(user.id)
                                        await user.add_roles(traveler_role)
                                # if the user has previously verified a nation
                                else:
                                    # append the verified nation to the list
                                    await conn.execute('''UPDATE verified_nations SET main_nation = $1 
                                    WHERE user_id = $2;''', nation_name, user.id)
                                    thegye_role = thegye_server.get_role(674260547897917460)
                                    karma_role = thegye_server.get_role(771456227674685440)
                                    await user.remove_roles(thegye_role, traveler_role, karma_role)
                                    async with verify_session.get(
                                            f"https://www.nationstates.net/cgi-bin/api.cgi?nation={nation_name}",
                                            headers=headers) as nation_info:
                                        await asyncio.sleep(.6)
                                        nation_info_raw = await nation_info.text()
                                        nation_info_soup = BeautifulSoup(nation_info_raw, 'lxml')
                                        region = nation_info_soup.region.text
                                        # if the nation's region is Thegye, add the Thegye role
                                        if region == "Thegye":
                                            # if the nation is in the WA, add the WA role
                                            if nation_info_soup.unstatus.text != "Non-member":
                                                wa_role = thegye_server.get_role(674283915870994442)
                                                await user.add_roles(wa_role)
                                            await user.add_roles(thegye_role)
                                            await user.remove_roles(traveler_role, karma_role)
                                            await verify_dm.send(
                                                f"Success! You have now verified `{nation_name}`. "
                                                f"Your roles will update momentarily. ")
                                        # if the nation's region is Karma, add the Karma role
                                        elif region == "Karma":
                                            await user.add_roles(karma_role)
                                        # otherwise, add the traveler role
                                        else:
                                            await user.add_roles(traveler_role)
                                verifying.close()
                                await verify_dm.send(f"Success! You have now verified `{nation_name}`. "
                                                     f"Your roles will update momentarily.")
                            else:
                                await user.add_role(traveler_role)
                                await user.remove_roles(nationstates_role, unverified_role)
                                await verify_dm.send("That is not a valid or correct verification code. "
                                                     "You have not been verified, but you may try again later.")
            await user.remove_roles(unverified_role)
            open_square = thegye_server.get_channel(674335095628365855)
            await open_square.send(f"The gods have sent us {user.mention}! Welcome, traveler, "
                                   f"and introduce yourself!")
        except Exception as error:
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            self.bot.logger.warning(msg=f"{traceback_text}")


class Verification(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot
        self.rate_limit = Ratelimiter()
        self.daily_verification = asyncio.create_task(self.daily_check())

    def sanitize_links_underscore(self, userinput: str) -> str:
        """Replaces spaces with proper, url-friendly underscores"""
        to_regex = userinput.replace(" ", "_")
        return re.sub(r"[^a-zA-Z0-9_-]", ' ', to_regex)

    async def daily_check(self):
        try:
            # establishes connection
            await self.bot.wait_until_ready()
            bot = self.bot
            conn = bot.pool
            crashchannel = bot.get_channel(835579413625569322)
            # establishes loop
            while True:
                # gets server, channels, and roles
                thegye_server = bot.get_guild(674259612580446230)
                admin_channel = thegye_server.get_channel(674285035905613825)
                thegye_role = thegye_server.get_role(674260547897917460)
                traveler_role = thegye_server.get_role(674280677268652047)
                karma_role = thegye_server.get_role(771456227674685440)
                unverified_role = thegye_server.get_role(1028144304507592704)
                cte_role = thegye_server.get_role(674284482890694657)
                wa_role = thegye_server.get_role(674283915870994442)
                nationstates_role = thegye_server.get_role(1150861314424573992)
                # sets time
                eastern = timezone('US/Eastern')
                now = datetime.now(eastern)
                # sets time to be 330 the next day
                if now.month == 12 and now.day == 31:
                    next_run = now.replace(year=now.year + 1, month=1, day=1, hour=3, minute=30, second=0)
                else:
                    # sets time to be 3:30 on the next day
                    try:
                        next_run = now.replace(day=now.day + 1, hour=3, minute=30, second=0)
                    # if there is a value error, the month is probably whacked up
                    except ValueError:
                        next_run = now.replace(day=1, month=now.month + 1, hour=3, minute=30, second=0)
                # sends the next runtime
                await crashchannel.send(f"Verification daily update waiting until "
                                        f"{next_run.strftime('%d %b %Y at %H:%M %Z%z')}")
                # gets the time to wait
                delta: timedelta = next_run - now
                # converts time to seconds
                seconds = delta.total_seconds()
                # sleeps until runtime
                await asyncio.sleep(seconds)
                # cycles through all members
                for member in thegye_server.members:
                    # skips bots
                    bot_role = thegye_server.get_role(783751789299105812)
                    if bot_role in member.roles:
                        continue
                    # skips those not attached to nationstates
                    if nationstates_role not in member.roles:
                        continue
                    # calls member information from the database
                    member_info = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''',
                                                      member.id)
                    await member.remove_roles(wa_role, thegye_role, karma_role, traveler_role, cte_role)
                    # if the member is not verified at all, remove all relevant roles and move to the next member
                    if member_info is None:
                        await member.add_roles(unverified_role)
                        continue
                    # otherwise, update roles
                    else:
                        async with aiohttp.ClientSession() as verify_session:
                            headers = {'User-Agent': 'Bassiliya'}
                            params = {'nation': member_info['main_nation']}
                            # get data
                            async with verify_session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                                          headers=headers, params=params) as nation_info:
                                await asyncio.sleep(.6)
                                if nation_info.status == 404:
                                    await member.add_roles(cte_role)
                                    continue
                                nation_info_raw = await nation_info.text()
                                nation_info_soup = BeautifulSoup(nation_info_raw, 'lxml')
                                region = nation_info_soup.region.text
                                # if the nation's region is Thegye, add the Thegye role
                                if region == "Thegye":
                                    await member.remove_roles(traveler_role, karma_role)
                                    # if the nation is in the WA, add the WA role
                                    if nation_info_soup.unstatus.text != "Non-member":
                                        await member.add_roles(wa_role)
                                    await member.add_roles(thegye_role)
                                    await member.remove_roles(cte_role)
                                    continue
                                # if the nation's region is Karma, add the Karma role
                                elif region == "Karma":
                                    await member.add_roles(karma_role)
                                    await member.remove_roles(cte_role)
                                # otherwise, add the traveler role
                                else:
                                    await member.add_roles(traveler_role)
                                    await member.remove_roles(cte_role)
                await admin_channel.send(f"{thegye_server.member_count} users checked and roles updated.")
                continue
        except Exception as error:
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            self.bot.logger.warning(msg=f"{traceback_text}")

    def cog_unload(self):
        self.daily_verification.cancel()

    verification = app_commands.Group(name="verification", description="...")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # if this is the Thegye server
        if member.guild.id == 674259612580446230:
            thegye_server = self.bot.get_guild(674259612580446230)
            unverified_role = thegye_server.get_role(1028144304507592704)
            dispatch_role = thegye_server.get_role(751113326481768479)
            gatehouse_channel = thegye_server.get_channel(674284159128043530)
            await member.add_roles(unverified_role, dispatch_role)
            welcome_message = await gatehouse_channel.send(
                f"Welcome to the official Thegye Discord server, {member.mention}!\n"
                f"Please use the dropdown menu below to select the role options "
                f"that best describe your reason for being here.")
            await welcome_message.edit(view=VerificationView(member=member, message=welcome_message, bot=self.bot))

    @verification.command(name="verify", description="Verifies a specified nation.")
    @app_commands.describe(nation_name="The name of the nation you would like to verify.")
    @app_commands.guild_only()
    async def verify(self, interaction: discord.Interaction, nation_name: str):
        # defers the interaction
        await interaction.response.defer(thinking=True)
        # establishes connection
        conn = self.bot.pool
        # establishes author
        author = interaction.user
        # creates DM
        author_message = await author.create_dm()
        # define thegye server and unverified role
        thegye_server = self.bot.get_guild(674259612580446230)
        unverified_role = thegye_server.get_role(1028144304507592704)
        thegye_role = thegye_server.get_role(674260547897917460)
        traveler_role = thegye_server.get_role(674280677268652047)
        karma_role = thegye_server.get_role(771456227674685440)
        # define and give nationstates role
        nationstates_role = thegye_server.get_role(1150861314424573992)
        await interaction.user.add_roles(nationstates_role)
        if interaction.guild is not None:
            await interaction.followup.send("Sent you a DM!")

        # checks to make sure the author is the author and the guild is a DM
        def authorcheck(message):
            return interaction.user.id == message.author.id and message.guild is None

        # checks to see if the user has already verified yet or not
        verified_check = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''', author.id)
        # if the user has no verified nations
        await author_message.send(f"**Welcome to the Shard Verification, {author.name}!** \n\n"
                                  f"To begin the verification process, please login to {nation_name}. "
                                  f"Here is a URL to your nation page: https://www.nationstates.net/nation="
                                  f"{self.sanitize_links_underscore(nation_name)}")
        # waits for the user to reply with their nation
        headers = {"User-Agent": "Bassiliya"}
        nation_exist = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={nation_name}",
                                    headers=headers)
        # if the nation does not exist, let the user know
        if nation_exist.status_code == 404:
            await author_message.send(
                f"No such nation as `{nation_name}`. Please check that you are using only the nation's"
                f" name, without the pretitle. **You will need to use the `/verify` command again.**")
            return
        # get official nation name
        nation_raw = nation_exist.text
        nation_soup = BeautifulSoup(nation_raw, 'lxml')
        nation_name = nation_soup.find('name').text
        # if the user has already verified that nation
        if verified_check is not None:
            if nation_name.lower() == verified_check['main_nation'].lower():
                return await author_message.send(
                    f"You have already verified `{nation_name}`. To view your verified nation, "
                    f"use `/view_verified`.")
        # send verification instructions via DM
        await asyncio.sleep(5)
        await author_message.send(f"Please login to {nation_name}. Once complete, head to this link and send me the "
                                  f"verification code displayed: https://www.nationstates.net/page=verify_login. "
                                  f"You may give the code displayed to an external website or tool, like me, "
                                  f"which can use it to verify that you are indeed currently logged in as this nation. "
                                  f"This is *all* I can do with it: It does not allow me to access your nation.")
        # wait for response
        try:
            code_reply = await self.bot.wait_for('message', check=authorcheck, timeout=300)
        except asyncio.TimeoutError:
            return await author_message.send("Verification timed out. Please answer me next time!")
        # define headers and parameters
        params = {'a': 'verify',
                  'nation': nation_name,
                  'checksum': code_reply.content,
                  'q': 'region+wa'}
        # start session
        async with aiohttp.ClientSession() as verify_session:
            # call for necessary data
            async with verify_session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                          headers=headers, params=params) as verifying:
                await asyncio.sleep(.6)
                # parse the verification response
                verification_raw = await verifying.text()
                verification_soup = BeautifulSoup(verification_raw, 'lxml')
                # fetch verification
                verification = verification_soup.verify.string
                # if the verification code is good
                if int(verification) == 1:
                    # if the user has no verified nation, add a new row
                    if verified_check is None:
                        await conn.execute('''INSERT INTO verified_nations(user_id, main_nation) VALUES ($1, $2);''',
                                           author.id, nation_name)
                        # if the nation's region is Thegye, add the Thegye role
                        if verification_soup.region.text == "Thegye":
                            user = thegye_server.get_member(author.id)
                            # if the nation is in the WA, add the WA role
                            if verification_soup.unstatus.text != "Non-member":
                                wa_role = thegye_server.get_role(674283915870994442)
                                await user.add_roles(wa_role)
                            await user.add_roles(thegye_role)
                            await user.remove_roles(unverified_role, traveler_role)
                        # if the nation's region is Karma, add the Karma role
                        elif verification_soup.region.text == "Karma":
                            user = thegye_server.get_member(author.id)
                            await user.add_roles(karma_role)
                            await user.remove_roles(unverified_role, traveler_role)
                        # otherwise, add the traveler role
                        else:
                            traveler_role = thegye_server.get_role(674280677268652047)
                            user = thegye_server.get_member(author.id)
                            await user.add_roles(traveler_role)
                            await user.remove_roles(unverified_role)
                    # if the user has previously verified a nation
                    else:
                        # append the verified nation to the list
                        await conn.execute('''UPDATE verified_nations SET main_nation = $1 WHERE user_id = $2;''',
                                           nation_name, author.id)
                        user = thegye_server.get_member(author.id)
                        await user.remove_roles(thegye_role, traveler_role, karma_role)
                        async with verify_session.get(
                                f"https://www.nationstates.net/cgi-bin/api.cgi?nation={nation_name}",
                                headers=headers) as nation_info:
                            await asyncio.sleep(.6)
                            nation_info_raw = await nation_info.text()
                            nation_info_soup = BeautifulSoup(nation_info_raw, 'lxml')
                            region = nation_info_soup.region.text
                            # if the nation's region is Thegye, add the Thegye role
                            if region == "Thegye":
                                await user.remove_roles(traveler_role, karma_role)
                                # if the nation is in the WA, add the WA role
                                if nation_info_soup.unstatus.text != "Non-member":
                                    wa_role = thegye_server.get_role(674283915870994442)
                                    await user.add_roles(wa_role)
                                return await user.add_roles(thegye_role)
                            # if the nation's region is Karma, add the Karma role
                            elif region == "Karma":
                                return await user.add_roles(karma_role)
                            # otherwise, add the traveler role
                            else:
                                await user.add_roles(traveler_role)
                    verifying.close()
                    return await author_message.send(f"Success! You are now verified as `{nation_name}`. "
                                                     f"Your roles will update momentarily.")
                else:
                    return await author_message.send("That is not a valid or correct verification code. "
                                                     "Please try again.")

    @verification.command(name="unverify", description="Remove your verified nation.")
    async def unverify(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # sets author
        author = interaction.user
        # remove all nations
        await conn.execute('''DELETE FROM verified_nations WHERE user_id = $1;''', author.id)
        # update roles
        thegye_server = self.bot.get_guild(674259612580446230)
        thegye_role = thegye_server.get_role(674260547897917460)
        traveler_role = thegye_server.get_role(674280677268652047)
        karma_role = thegye_server.get_role(771456227674685440)
        nationstates_role = thegye_server.get_role(1150861314424573992)
        await author.remove_roles(thegye_role, karma_role, nationstates_role)
        await author.add_roles(traveler_role)
        return await interaction.followup.send(f"Your roles have been updated accordingly. "
                                               f"All nations have been removed from your Discord account.")

    @verification.command(name="view_verified", description="Displays a list of a user's verified nation.")
    @app_commands.describe(user="Optional server member")
    async def view_verified(self, interaction: discord.Interaction, user: Optional[discord.Member]):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        if user is None:
            # get author
            author = interaction.user
            # fetches all verified nations
            verified = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''',
                                           author.id)
            if verified is None:
                return await interaction.followup.send("You do not have any verified nations. "
                                                       "Use `/verify` to verify a nation.")
            else:
                if verified['main_nation'] is not None:
                    verified_nations = f"{verified['main_nation']}"
                else:
                    return await interaction.followup.send("You have no verified nation record")
                return await interaction.followup.send(f"Verified nation of {author.name}: {verified_nations}")
        if user is not None:
            # get author
            author = user
            # fetches all verified nations
            verified = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''',
                                           author.id)
            if verified is None:
                return await interaction.followup.send(f"{user.nick} does not have any verified nations.")
            else:
                if verified['main_nation'] is not None:
                    verified_nations = f"{verified['main_nation']}"
                else:
                    return await interaction.followup.send("You have no verified nation recorded.")
                return await interaction.followup.send(f"Verified nations of {author.name}: {verified_nations}")

    @commands.command()
    @commands.is_owner()
    async def server_check(self, ctx):
        async with ctx.typing():
            # define bot
            bot = self.bot
            # establish connection
            conn = bot.pool
            # gets server, channels, and roles
            thegye_server = bot.get_guild(674259612580446230)
            thegye_role = thegye_server.get_role(674260547897917460)
            traveler_role = thegye_server.get_role(674280677268652047)
            karma_role = thegye_server.get_role(771456227674685440)
            unverified_role = thegye_server.get_role(1028144304507592704)
            cte_role = thegye_server.get_role(674284482890694657)
            wa_role = thegye_server.get_role(674283915870994442)
            # cycles through all members
            for member in thegye_server.members:
                # calls member information from the database
                member_info = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''',
                                                  member.id)
                await member.remove_roles(wa_role, thegye_role, karma_role, traveler_role, cte_role)
                bot = discord.utils.get(ctx.guild.roles, id=783751789299105812)
                if bot in member.roles:
                    continue
                # if the member is not verified at all, remove all relevant roles and move to the next member
                if member_info is None:
                    await member.add_roles(unverified_role)
                    continue
                # otherwise, update roles
                else:
                    member_nations = member_info['nations']
                    async with aiohttp.ClientSession() as verify_session:
                        for n in member_nations:
                            headers = {'User-Agent': 'Bassiliya'}
                            params = {'nation': n}
                            while True:
                                # see if there are enough available calls. if so, break the loop
                                try:
                                    await self.rate_limit.call()
                                    break
                                # if there are not enough available calls, continue the loop
                                except TooManyRequests as error:
                                    await asyncio.sleep(int(str(error)))
                                    continue
                            # get data
                            async with verify_session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                                          headers=headers, params=params) as nation_info:
                                if nation_info.status == 404:
                                    await member.add_roles(cte_role)
                                    continue
                                nation_info_raw = await nation_info.text()
                                nation_info_soup = BeautifulSoup(nation_info_raw, 'lxml')
                                region = nation_info_soup.region.text
                                # if the nation's region is Thegye, add the Thegye role
                                if region == "Thegye":
                                    await member.remove_roles(traveler_role, karma_role)
                                    # if the nation is in the WA, add the WA role
                                    if nation_info_soup.unstatus.text != "Non-member":
                                        await member.add_roles(wa_role)
                                    await member.add_roles(thegye_role)
                                    await member.remove_roles(cte_role)
                                    continue
                                # if the nation's region is Karma, add the Karma role
                                elif region == "Karma":
                                    await member.add_roles(karma_role)
                                    await member.remove_roles(cte_role)
                                # otherwise, add the traveler role
                                else:
                                    await member.add_roles(traveler_role)
                                    await member.remove_roles(cte_role)
        await ctx.send(f"{thegye_server.member_count} users checked and roles updated.")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id != 674259612580446230:
            return
        else:
            # establishes connection
            conn = self.bot.pool
            # fetches nation information
            verified = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''', member.id)
            if verified is None:
                user_nations = "*None*"
            else:
                if verified['main_nation'] is None:
                    nation_list = []
                    for n in verified['nations']:
                        nation_list.append(f"[{n}]"
                                           f"(https://www.nationstates.net/nation={self.sanitize_links_underscore(n)})")
                    user_nations = ', '.join(nation_list)
                else:
                    user_nations = f"[**{verified['main_nation']}**]" \
                                   f"(https://www.nationstates.net/nation=" \
                                   f"{self.sanitize_links_underscore(verified['main_nation'])})"
                    for n in verified['nations']:
                        if n == verified['main_nation']:
                            continue
                        user_nations += f", [{n}](https://www.nationstates.net/nation={self.sanitize_links_underscore(n)})"
            leave_channel = self.bot.get_channel(674335095628365855)
            all_roles = member.roles[1:]
            role_names = [f"<@&{r.id}>" for r in all_roles]
            roles = ', '.join(role_names[::-1])
            gold = discord.Color.gold()
            leave_embed = discord.Embed(title=f"{member.name}{member.discriminator} has departed Thegye.",
                                        color=gold)
            leave_embed.set_thumbnail(url=member.display_avatar.url)
            leave_embed.add_field(name="Joined server", value=f"<t:{round(member.joined_at.timestamp())}>")
            leave_embed.add_field(name="Roles", value=f"{roles}")
            leave_embed.add_field(name="Nations", value=f"{user_nations}", inline=False)
            await leave_channel.send(embed=leave_embed)

    @commands.command()
    @commands.is_owner()
    async def set_mains(self, ctx):
        # define pool
        conn = self.bot.pool
        # fetch all users without a main nation
        all_users = await conn.fetch('''SELECT * FROM verified_nations WHERE main_nation is NULL;''')
        # set first verified nation as main nation
        counter = 0
        for user in all_users:
            # first nation in list
            nation = user['nations'][0]
            # update user with nation as main
            await conn.execute('''UPDATE verified_nations SET main_nation = $1 WHERE user_id = $2;''',
                               nation, user['user_id'])
            counter += 1
        return await ctx.send(f"{counter} users in compliance.")


async def setup(bot: Shard):
    # define the cog and add the cog
    cog = Verification(bot)
    await bot.add_cog(cog)
