# Shard Verification 0.1b
import traceback
from datetime import datetime, timedelta
import discord.channel
from ShardBot import Shard
import asyncio
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import re
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
import aiohttp
from typing import Union, Optional


class Verification(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot

        self.daily_verification = asyncio.create_task(self.daily_check())

    async def daily_check(self):
        try:
            # establishes connection
            bot = self.bot
            await bot.wait_until_ready()
            conn = bot.pool
            crashchannel = bot.get_channel(835579413625569322)
            eastern = timezone('US/Eastern')
            now = datetime.now(eastern)
            # sets time to be midnight on the next month's first day
            next_run = now.replace(day=now.day + 1, hour=3, minute=30, second=0)
            # sends the next runtime
            await crashchannel.send(f"Verification daily update waiting until "
                                    f"{next_run.strftime('%H:%M %Z%z')}")
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
                # sets time
                eastern = timezone('US/Eastern')
                now = datetime.now(eastern)
                # sets time to be 330 the next day
                next_run = now.replace(day=now.day + 1, hour=3, minute=30, second=0)
                # gets the time to wait
                delta: timedelta = next_run - now
                # converts time to seconds
                seconds = delta.total_seconds()
                # sleeps until runtime
                await asyncio.sleep(seconds)
                # cycles through all members
                for member in thegye_server.members:
                    # if member is a bot
                    if member.bot:
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
                        member_nations = member_info['nations']
                        async with aiohttp.ClientSession() as verify_session:
                            for n in member_nations:
                                headers = {'User-Agent': 'Bassiliya'}
                                params = {'nation': n}
                                # get data
                                async with verify_session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                                              headers=headers, params=params) as nation_info:
                                    await asyncio.sleep(.6)
                                    if nation_info.status == 404:
                                        await member.add_roles(cte_role)
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

    @commands.command(brief="Verifies a nation.")
    async def verify(self, ctx):
        # establishes connection
        conn = self.bot.pool
        # establishes author
        author = ctx.author
        # creates DM
        author_message = await author.create_dm()
        # define thegye server and unverified role
        thegye_sever = self.bot.get_guild(674259612580446230)
        unverified_role = thegye_sever.get_role(1028144304507592704)
        if ctx.guild is not None:
            await ctx.send("Sent you a DM!")

        # checks to make sure the author is the author and the guild is a DM
        def authorcheck(message):
            return ctx.author.id == message.author.id and message.guild is None

        # checks to see if the user has already verified yet or not
        verified_check = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''', author.id)
        # if the user has no verified nations
        if verified_check is None:
            # sends DM to initiate verification
            await author_message.send(f"**Welcome to the Shard Verification, {author}!** \n\n"
                                      f"To begin the verification process, please enter your nation's **name**, "
                                      f"without the pretitle. For example, if your nation appears as `The Holy Empire "
                                      f"of Bassiliya`, please only enter `Bassiliya`.")
        # if the user does have some verified nation(s)
        else:
            # sends DM to initiate verification
            await author_message.send(f"**Welcome back to the Shard Verification, {author}!** \n\n"
                                      f"To begin the verification process, please enter your nation's **name**, "
                                      f"without the pretitle. Please verify a nation that you have not "
                                      f"previously verified. For example, if your nation appears as `The Holy Empire "
                                      f"of Bassiliya`, please only enter `Bassiliya`.")
        # waits for the user to reply with their nation
        try:
            nation_reply = await self.bot.wait_for('message', check=authorcheck, timeout=300)
        except asyncio.TimeoutError:
            return await author_message.send("Verification timed out. Please answer me next time!")
        # assigns nation name
        nation_name = nation_reply.content
        # if the user decides to cancel the process
        if nation_name.lower() == 'stop' or nation_name.lower() == 'cancel' or nation_name.lower() == 'skip':
            return await author_message.send("Verification cancelled.")
        # checks for the nation's existence
        headers = {"User-Agent": "Bassiliya"}
        nation_exist = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={nation_name}",
                                    headers=headers)
        # if the nation does not exist, let the user know
        if nation_exist.status_code == 404:
            await author_message.send(
                f"No such nation as `{nation_name}`. Please check that you are using only the nation's"
                f" name, without the pretitle.")
            return
        # get official nation name
        nation_raw = nation_exist.text
        nation_soup = BeautifulSoup(nation_raw, 'lxml')
        nation_name = nation_soup.find('name').text
        # if the user has already verified that nation
        if verified_check is not None:
            if nation_name.lower() in [n.lower() for n in verified_check['nations']]:
                return await author_message.send(
                    f"You have already verified `{nation_name}`. To view your verified nations, "
                    f"use `$view_verified`.")
        # send verification instructions via DM
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
                        await conn.execute('''INSERT INTO verified_nations(user_id, nations) VALUES ($1, $2);''',
                                           author.id, [nation_name])
                        # if the nation's region is Thegye, add the Thegye role
                        if verification_soup.region.text == "Thegye":
                            thegye_role = thegye_sever.get_role(674260547897917460)
                            user = thegye_sever.get_member(author.id)
                            # if the nation is in the WA, add the WA role
                            if verification_soup.unstatus.text != "Non-member":
                                wa_role = thegye_sever.get_role(674283915870994442)
                                await user.add_roles(wa_role)
                            await user.add_roles(thegye_role)
                            await user.remove_roles(unverified_role)
                        # if the nation's region is Karma, add the Karma role
                        elif verification_soup.region.text == "Karma":
                            thegye_sever = self.bot.get_guild(674259612580446230)
                            karma_role = thegye_sever.get_role(771456227674685440)
                            user = thegye_sever.get_member(author.id)
                            await user.add_roles(karma_role)
                            await user.remove_roles(unverified_role)
                        # otherwise, add the traveler role
                        else:
                            thegye_sever = self.bot.get_guild(674259612580446230)
                            traveler_role = thegye_sever.get_role(674280677268652047)
                            user = thegye_sever.get_member(author.id)
                            await user.add_roles(traveler_role)
                            await user.remove_roles(unverified_role)
                    # if the user has previously verified a nation
                    else:
                        # append the verified nation to the list
                        await conn.execute('''UPDATE verified_nations SET nations = nations || $1
                        WHERE user_id = $2;''', [nation_name], author.id)
                        all_nations = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''',
                                                          author.id)
                        thegye_sever = self.bot.get_guild(674259612580446230)
                        thegye_role = thegye_sever.get_role(674260547897917460)
                        traveler_role = thegye_sever.get_role(674280677268652047)
                        karma_role = thegye_sever.get_role(771456227674685440)
                        user = thegye_sever.get_member(author.id)
                        await user.remove_roles(thegye_role, traveler_role, karma_role)
                        for n in all_nations['nations']:
                            async with verify_session.get(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={n}",
                                                          headers=headers) as nation_info:
                                await asyncio.sleep(.6)
                                nation_info_raw = await nation_info.text()
                                nation_info_soup = BeautifulSoup(nation_info_raw, 'lxml')
                                region = nation_info_soup.region.text
                                # if the nation's region is Thegye, add the Thegye role
                                if region == "Thegye":
                                    await user.remove_roles(traveler_role, karma_role)
                                    await author_message.send(f"Success! You have now verified `{nation_name}`. "
                                                              f"Your roles will update momentarily. "
                                                              f"If you would like to set your main nation, "
                                                              f"use the `$set_main` command to do so.")
                                    # if the nation is in the WA, add the WA role
                                    if nation_info_soup.unstatus.text != "Non-member":
                                        wa_role = thegye_sever.get_role(674283915870994442)
                                        await user.add_roles(wa_role)
                                    return await user.add_roles(thegye_role)
                                # if the nation's region is Karma, add the Karma role
                                elif region == "Karma":
                                    await user.add_roles(karma_role)
                                # otherwise, add the traveler role
                                else:
                                    await user.add_roles(traveler_role)
                    verifying.close()
                    return await author_message.send(f"Success! You have now verified `{nation_name}`. "
                                                     f"Your roles will update momentarily. "
                                                     f"If you would like to set your main nation, "
                                                     f"use the `$set_main` command to do so.")
                else:
                    return await author_message.send("That is not a valid or correct verification code. "
                                                     "Please try again.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # if this is the Thegye server
        if member.guild.id == 674259612580446230:
            thegye_sever = self.bot.get_guild(674259612580446230)
            user = thegye_sever.get_member(member.id)
            unverified_role = thegye_sever.get_role(1028144304507592704)
            await user.add_roles(unverified_role)
            # define channels
            open_square = thegye_sever.get_channel(674335095628365855)
            gatehouse = thegye_sever.get_channel(674284159128043530)
            await gatehouse.send(f"{user.mention}, please check your DMs to start the verification process!\n"
                                 f"If you have any issues, be sure to let a Gatekeeper know.")
            # establish connection
            conn = self.bot.pool
            # search for existing nations
            previously_verified = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''',
                                                      member.id)
            if previously_verified is not None:
                thegye_role = thegye_sever.get_role(674260547897917460)
                traveler_role = thegye_sever.get_role(674280677268652047)
                karma_role = thegye_sever.get_role(771456227674685440)
                cte_role = thegye_sever.get_role(572456164399251490)
                await user.remove_roles(thegye_role, traveler_role, karma_role, unverified_role)
                # start session and define headers
                headers = {"User-Agent": "Bassiliya"}
                async with aiohttp.ClientSession() as verify_session:
                    for n in previously_verified['nations']:
                        async with verify_session.get(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={n}",
                                                      headers=headers) as nation_info:
                            await asyncio.sleep(.6)
                            if nation_info.status == 404:
                                await user.add_roles(cte_role)
                                return await open_square.send(f"The gods have sent us {member.mention}! "
                                                              f"Welcome, traveler, and introduce yourself!")
                            nation_info_raw = await nation_info.text()
                            nation_info_soup = BeautifulSoup(nation_info_raw, 'lxml')
                            region = nation_info_soup.region.text
                            nation_name = nation_info_soup.nation.text
                            # insert new user into database
                            await conn.execute('''INSERT INTO verified_nations(user_id, nations) VALUES($1, $2);''',
                                               user.id, [nation_name])
                            # if the nation's region is Thegye, add the Thegye role
                            if region == "Thegye":
                                await user.remove_roles(traveler_role, karma_role)
                                await open_square.send(f"The gods have sent us {member.mention}! Welcome, traveler, "
                                                       f"and introduce yourself!")
                                # if the nation is in the WA, add the WA role
                                if nation_info_soup.unstatus.text != "Non-member":
                                    wa_role = thegye_sever.get_role(674283915870994442)
                                    await user.add_roles(wa_role)
                                return await user.add_roles(thegye_role)
                            # if the nation's region is Karma, add the Karma role
                            elif region == "Karma":
                                await user.add_roles(karma_role)
                            # otherwise, add the traveler role
                            else:
                                await user.add_roles(traveler_role)
                await open_square.send(f"The gods have sent us {member.mention}! Welcome, traveler, "
                                       f"and introduce yourself!")
            else:
                # creates DM
                member_message = await member.create_dm()
                try:
                    await member_message.send(f"**Welcome to the Thegye server, {member}!** \n\n"
                                              f"This is your quick invitation to verify your NationStates nation. If your "
                                              f"nation is currently residing in Thegye, "
                                              f"you will be assigned the Thegye role. If your nation is not currently "
                                              f"residing in Thegye, you will be assigned the Traveler role. "
                                              f"If you do not verify any nation, you will be assigned "
                                              f"the Unverified role and be unable to access the majority of the server.\n\n"
                                              f"To begin the verification process, please enter your nation's **name**, "
                                              f"without the pretitle. For example, if your nation appears as "
                                              f"`The Holy Empire of Bassiliya`, please only enter `Bassiliya`. "
                                              f"If you would like to skip verification, "
                                              f"enter \"SKIP\" instead of your nation name.")
                except discord.Forbidden:
                    return await gatehouse.send(f"{user.mention}, I can't DM you! This could be for a few reasons: \n\n"
                                                f"1. You have me blocked. Sad. \U0001f614 \n"
                                                f"2. You are no longer in this server or any server we share. "
                                                f"*Come back!*\n"
                                                f"3. You accept DMs only from users you have in your Friends list. "
                                                f"In order to allow me to DM you, go to `Settings > Privacy & Safety > "
                                                f"Server Privacy Defaults` and toggle **ON** the "
                                                f"`Allow direct messages from server members.\n\n"
                                                f"Once you have completed that step, please use the `$verify` "
                                                f"command again to complete the verification process. ")

                def authorcheck(message):
                    return member.id == message.author.id and message.guild is None

                # waits for the user to reply with their nation
                try:
                    nation_reply = await self.bot.wait_for('message', check=authorcheck, timeout=300)
                except asyncio.TimeoutError:
                    await open_square.send(f"The gods have sent us {member.mention}! Welcome, traveler, "
                                           f"and introduce yourself!")
                    return await member_message.send("Verification timed out. Please answer me next time!")
                # assigns nation name
                nation_name = nation_reply.content
                if nation_name.lower() == 'skip':
                    await open_square.send(f"The gods have sent us {member.mention}! Welcome, traveler, "
                                           f"and introduce yourself!")
                    return await member_message.send("Verification cancelled.")
                # checks for the nation's existence
                headers = {"User-Agent": "Bassiliya"}
                nation_exist = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={nation_name}",
                                            headers=headers)
                # if the nation does not exist, let the user know
                if nation_exist.status_code == 404:
                    await open_square.send(f"The gods have sent us {member.mention}! Welcome, traveler, "
                                           f"and introduce yourself!")
                    return await member_message.send(
                        f"No such nation as `{nation_name}`. Please check that you are using only the nation's"
                        f" name, without the pretitle.")
                # get official nation name
                nation_raw = nation_exist.text
                nation_soup = BeautifulSoup(nation_raw, 'lxml')
                nation_name = nation_soup.find('name').text
                # send verification instructions via DM
                await member_message.send(
                    f"Please login to {nation_name}. Once complete, head to this link and send the "
                    f"verification code displayed: https://www.nationstates.net/page=verify_login. "
                    f"You may give the code below to an external website, which can use it to verify "
                    f"that you are indeed currently logged in as this nation. "
                    f"This is *all* I can do with it: It does not allow me to access your nation.")
                # wait for response
                try:
                    code_reply = await self.bot.wait_for('message', check=authorcheck, timeout=300)
                except asyncio.TimeoutError:
                    await open_square.send(f"The gods have sent us {member.mention}! Welcome, traveler, "
                                           f"and introduce yourself!")
                    return await member_message.send("Verification timed out. Please answer me next time!")
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
                        region = verification_soup.region.string
                        # if the verification code is good
                        if int(verification) == 1:
                            # define roles
                            thegye_role = thegye_sever.get_role(674260547897917460)
                            traveler_role = thegye_sever.get_role(674280677268652047)
                            karma_role = thegye_sever.get_role(771456227674685440)
                            # since the user has no verified nation, add a new row
                            await conn.execute(
                                '''INSERT INTO verified_nations(user_id, nations) VALUES ($1, $2);''',
                                member.id, [nation_name])
                            # if the nation's region is Thegye, add the Thegye role
                            if region == "Thegye":
                                await user.remove_roles(traveler_role, karma_role)
                                await member_message.send(f"Success! You have now verified `{nation_name}`. "
                                                          f"Your roles will update momentarily. "
                                                          f"If you would like to set your main nation, "
                                                          f"use the `$set_main` command to do so.")
                                await user.add_roles(thegye_role)
                                # if the nation is in the WA, add the WA role
                                if verification_soup.unstatus.text != "Non-member":
                                    wa_role = thegye_sever.get_role(674283915870994442)
                                    await user.add_roles(wa_role)
                                await user.remove_roles(unverified_role)
                                return await open_square.send(f"The gods have sent us {member.mention}! "
                                                              f"Welcome, traveler, and introduce yourself!")
                            # if the nation's region is Karma, add the Karma role
                            elif region == "Karma":
                                await user.add_roles(karma_role)
                            # otherwise, add the traveler role
                            else:
                                await user.add_roles(traveler_role)
                            await user.remove_roles(unverified_role)
                            await open_square.send(f"The gods have sent us {member.mention}! Welcome, traveler, "
                                                   f"and introduce yourself!")
                        else:
                            await open_square.send(f"The gods have sent us {member.mention}! Welcome, traveler, "
                                                   f"and introduce yourself!")
                            return await member_message.send("That is not a valid or correct verification code. "
                                                             "Please try again.")

    @commands.command(brief="Remove a nation from your verified list.")
    async def unverify(self, ctx, *, args):
        # establish connection
        conn = self.bot.pool
        # sets author
        author = ctx.author
        # fetches nation information
        nation_check = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''',
                                           author.id)
        # if the user has no verified nations, return
        if nation_check is None:
            return await ctx.send("You have no nations registered.")
        # if the nation specified is not in the list
        if args.lower() not in [n.lower() for n in nation_check['nations']]:
            return await ctx.send("That nation is not registered.")
        # get the real nation name
        async with aiohttp.ClientSession() as verify_session:
            # headers and params
            headers = {'User-Agent': 'Bassiliya'}
            params = {'nation': args}
            # get data
            async with verify_session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                          headers=headers, params=params) as nation_info:
                await asyncio.sleep(.6)
                # parse name
                nation_info_response = await nation_info.text()
                nation_info_soup = BeautifulSoup(nation_info_response, 'lxml')
                nation_name = nation_info_soup.find('name').text
                # remove name
                await conn.execute('''UPDATE verified_nations SET nations = array_remove(nations, $1) 
                WHERE user_id = $2;''', nation_name, author.id)
                all_nations = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''',
                                                  author.id)
                thegye_sever = self.bot.get_guild(674259612580446230)
                thegye_role = thegye_sever.get_role(674260547897917460)
                traveler_role = thegye_sever.get_role(674280677268652047)
                karma_role = thegye_sever.get_role(771456227674685440)
                unverified_role = thegye_sever.get_role(1028144304507592704)
                wa_role = thegye_sever.get_role(674283915870994442)
                user = thegye_sever.get_member(author.id)
                await user.remove_roles(thegye_role, traveler_role, karma_role, wa_role)
                if all_nations['nations'] is not None:
                    for n in all_nations['nations']:
                        async with verify_session.get(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={n}",
                                                      headers=headers) as nation_info:
                            await asyncio.sleep(.6)
                            nation_info_raw = await nation_info.text()
                            nation_info_soup = BeautifulSoup(nation_info_raw, 'lxml')
                            region = nation_info_soup.region.text
                            # if the nation's region is Thegye, add the Thegye role
                            if region == "Thegye":
                                # if the nation is in the WA, add the WA role
                                if nation_info_soup.unstatus.text != "Non-member":
                                    await user.add_roles(wa_role)
                                await user.remove_roles(traveler_role, karma_role)
                                await ctx.send(f"You have successfully removed {nation_name} from your verified list. "
                                               f"Your roles have updated appropriately.")
                                return await user.add_roles(thegye_role)
                            # if the nation's region is Karma, add the Karma role
                            elif region == "Karma":
                                await user.add_roles(karma_role)
                            # otherwise, add the traveler role
                            else:
                                await user.add_roles(traveler_role)
                else:
                    await user.add_roles(unverified_role)
        return await ctx.send(f"You have successfully removed {nation_name} from your verified list. "
                              f"Your roles have updated appropriately.")

    @commands.command(brief="Displays a list of all verified nations.", aliases=['vv'])
    async def view_verified(self, ctx, *, user: Optional[discord.Member] = None):
        # establish connection
        conn = self.bot.pool
        if user is None:
            # get author
            author = ctx.author
            # fetches all verified nations
            verified = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''',
                                           author.id)
            if verified is None:
                return await ctx.send("You do not have any verified nations. Use `$verify` to verify a nation.")
            else:
                if verified['main_nation'] is not None:
                    verified_nations = f"**{verified['main_nation']}**"
                    for n in verified['nations']:
                        if n == verified['main_nation']:
                            continue
                        verified_nations += f", {n}"
                else:
                    verified_nations = ", ".join(verified['nations'])
                return await ctx.send(f"Verified nations of {author.name}: {verified_nations}")
        if user is not None:
            # get author
            author = user
            # fetches all verified nations
            verified = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''',
                                           author.id)
            if verified is None:
                return await ctx.send(f"{user.nick} does not have any verified nations.")
            else:
                if verified['main_nation'] is not None:
                    verified_nations = f"**{verified['main_nation']}**"
                    for n in verified['nations']:
                        if n == verified['main_nation']:
                            continue
                        verified_nations += f", {n}"
                else:
                    verified_nations = ", ".join(verified['nations'])
                return await ctx.send(f"Verified nations of {author.name}: {verified_nations}")

    @commands.command(brief="Sets a previously verified nation as the main nation.")
    @commands.guild_only()
    async def set_main(self, ctx, *, args: str):
        # establish connection
        conn = self.bot.pool
        # get author
        author = ctx.author
        # set nation variable
        nation = args
        # checks if nation is already verified and returns if not
        nation_info = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''',
                                          author.id)
        # if the user has no verified nations
        if nation_info is None:
            return await ctx.send("You do not have any verified nations. Use the `$verify` command to "
                                  "verify a nation first.")
        # if the nation is not previously verified
        if nation.lower() not in [n.lower() for n in nation_info['nations']]:
            return await ctx.send(f"`{nation}` is not a verified nation associated with your account.")
        # if the nation is already the main nation
        if nation_info['main_nation'] is not None:
            if nation.lower() == nation_info['main_nation'].lower():
                return await ctx.send(f"{nation_info['main_nation']} is already your main nation.")
        # set the nation as the main nation
        headers = {'User-Agent': 'Bassiliya'}
        nation_exist = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={nation}",
                                    headers=headers)
        # get official nation name
        nation_raw = nation_exist.text
        nation_soup = BeautifulSoup(nation_raw, 'lxml')
        nation_name = nation_soup.find('name').text
        # update the database
        await conn.execute('''UPDATE verified_nations SET main_nation = $1 WHERE user_id = $2;''',
                           nation_name, author.id)
        return await ctx.send(f"Success! {nation_name} is now your main nation.")

    @commands.command()
    @commands.is_owner()
    async def server_check(self, ctx):
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
            # if member is a bot
            if member.bot:
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
                member_nations = member_info['nations']
                async with aiohttp.ClientSession() as verify_session:
                    for n in member_nations:
                        headers = {'User-Agent': 'Bassiliya'}
                        params = {'nation': n}
                        # get data
                        async with verify_session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                                      headers=headers, params=params) as nation_info:
                            await asyncio.sleep(.6)
                            if nation_info.status == 404:
                                await member.add_roles(cte_role)
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


async def setup(bot: Shard):
    # define the cog and add the cog
    cog = Verification(bot)
    await bot.add_cog(cog)
