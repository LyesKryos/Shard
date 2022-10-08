# Shard Verification 0.1b
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


class Verification(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot

    @commands.command(brief="Verifies a nation.")
    async def verify(self, ctx):
        # establishes connection
        conn = self.bot.pool
        # establishes author
        author = ctx.author
        # creates DM
        author_message = await author.create_dm()

        def authorcheck(message):
            return ctx.author.id == message.author.id and message.guild is None

        # sends DM to initiate verification
        await author_message.send(f"**Welcome to the Thegye server, {author}!** \n\n"
                                  f"This is your quick invitation to verify your NationStates nation. If your nation is "
                                  f"currently residing in Thegye, you will be assigned the Thegye role. If your nation is"
                                  f" not currently residing in Thegye, you will be assigned the Traveler role. "
                                  f"If you do not verify any nation, you will be assigned the Unverified role and be unable"
                                  f" to access the majority of the server.\n\n"
                                  f"To begin the verification process, please enter your nation's **name**, "
                                  f"without the pretitle. For example, if your nation appears as `The Holy Empire of Bassiliya`,"
                                  f" please only enter `Bassiliya`. If you would like to skip verification, enter \"SKIP\" "
                                  f"instead of your nation name.")
        # waits for the user to reply with their nation
        try:
            nation_reply = await self.bot.wait_for('message', check=authorcheck, timeout=300)
        except asyncio.TimeoutError:
            return await author_message.send("Verification timed out. Please answer me next time!")
        # assigns nation name
        nation_name = nation_reply.content
        if nation_name.lower() == 'skip':
            return
        # checks for the nation's existence
        nation_exist = requests.get(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={nation_name.lower()}")
        # if the nation does not exist, let the user know
        if nation_exist.status_code == 404:
            await author_message.send(
                f"No such nation as `{nation_name}`. Please check that you are using only the nation's"
                f" name, without the pretitle.")
            return
        # send verification instructions via DM
        await author_message.send(f"Please login to {nation_name}. Once complete, head to this link and send the "
                                  f"verification code displayed: https://www.nationstates.net/page=verify_login. "
                                  f"You may give the code below to an external website, which can use it to verify that you are"
                                  f" indeed currently logged in as this nation. This is *all* I can do with it: "
                                  f"It does not allow me to access your nation.")
        # wait for response
        try:
            code_reply = await self.bot.wait_for('message', check=authorcheck, timeout=300)
        except asyncio.TimeoutError:
            return await author_message.send("Verification timed out. Please answer me next time!")
        # define headers and parameters
        headers = {"User-Agent": "Bassiliya"}
        params = {'a': 'verify',
                  'nation': nation_name.lower(),
                  'checksum': code_reply,
                  'q': 'region'}
        # start session
        async with aiohttp.ClientSession() as verify_session:
            # call for necessary data
            async with verify_session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                          headers=headers, params=params) as verifying:
                # parse the verification response
                verification_raw = await verifying.text()
                verification_soup = BeautifulSoup(verification_raw, 'lxml')
                # fetch verification
                verification = verification_soup.verify.string
                # if the verification code is goood
                if int(verification) == 1:
                    # pull the nation info if the user has already verified a nation
                    nation = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''', author.id)
                    # if the user has no verified nation, add a new row
                    if nation is None:
                        await conn.execute('''INSERT INTO verified_nations(user_id, nations) VALUES ($1, $2);''',
                                           author.id, nation_name)
                    else:
                        # if the user already has the nation verified, return
                        nation_check = await conn.fetchrow('''SELECT nations FROM verified_nations 
                        WHERE user_id = $1;''', author.id)
                        nation_check = [n.lower() for n in nation_check]
                        if nation_name in nation_check:
                            await author_message.send("You have already verified that nation. "
                                                      "To view a list of your verified nations, use `$view_verified`.")
                            return
                        # append the verified nation to the list
                        await conn.execute('''UPDATE verified_nations SET nations = nations || $1 
                        WHERE user_id = $2;''', nation_name, author.id)
                    await author_message.send(f"Success! You have now verified `{nation_name}`. "
                                              f"Your roles will update momentarily. If you would like to set your "
                                              f"main nation, use the `$set_main` command to do so.")
                    verifying.close()
                    # if the nation's region is Thegye, add the Thegye role
                    if verification_soup.region.text == "Thegye":
                        thegye_sever = self.bot.get_guild(674259612580446230)
                        thegye_role = thegye_sever.get_role(674260547897917460)
                        await author.add_roles(thegye_role)
                    # if the nation's region is Karma, add the Karma role
                    if verification_soup.region.text == "Karma":
                        thegye_sever = self.bot.get_guild(674259612580446230)
                        karma_role = thegye_sever.get_role(771456227674685440)
                        await author.add_roles(karma_role)
                    # otherwise, add the traveler role
                    else:
                        thegye_sever = self.bot.get_guild(674259612580446230)
                        traveler_role = thegye_sever.get_role(674280677268652047)
                        await author.add_roles(traveler_role)
                    return


async def setup(bot: Shard):
    # define the cog and add the cog
    cog = Verification(bot)
    await bot.add_cog(cog)
