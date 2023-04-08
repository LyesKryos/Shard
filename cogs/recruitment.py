# recruitment 1.1
import math
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from discord import app_commands
from pytz import timezone

from ShardBot import Shard
from urllib.parse import quote
from discord.ext import commands, tasks
import discord
import asyncio
from bs4 import BeautifulSoup
import re
import aiohttp
from time import perf_counter, strftime
from PIL import ImageColor
from customchecks import RecruitmentCheck, TooManyRequests
import traceback
import os

from ratelimiter import Ratelimiter


class Recruitment(commands.Cog):

    def __init__(self, bot: Shard):
        self.rate_limit = Ratelimiter()
        self.bot = bot
        self.db_error = False

        def error_log(error):
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            self.bot.logger.warning(msg=f"{traceback_text}")

        # define testing channel

        async def monthly_recruiter(bot):
            await bot.wait_until_ready()
            crashchannel = bot.get_channel(835579413625569322)
            eastern = timezone('US/Eastern')
            now = datetime.now(eastern)
            # sets time to be midnight on the next month's first day
            next_first = now.replace(day=1, hour=0, minute=0, second=0) + relativedelta(months=1)
            await crashchannel.send(f"Monthly recruiter waiting until "
                                    f"{next_first.strftime('%a, %d %b %Y at %H:%M %Z%z')}")
            while True:
                # define now
                eastern = timezone('US/Eastern')
                now = datetime.now(eastern)
                # sets time to be midnight on the next month's first day
                next_first = now.replace(day=1, hour=0, minute=0, second=0) + relativedelta(months=1)
                # waits until the next runtime
                await discord.utils.sleep_until(next_first)
                # connects to database
                conn = bot.pool
                # fetches all user data
                top_recruiter = await conn.fetch('''SELECT * FROM recruitment ORDER BY sent_this_month DESC;''')
                # finds the first entry and gathers user id, sent number, and sends the announcement message
                top_recruiter_user = top_recruiter[0]['user_id']
                top_recruiter_numbers = top_recruiter[0]['sent_this_month']
                announcements = bot.get_channel(674602527333023747)
                thegye = bot.get_guild(674259612580446230)
                # adds the role to the user and removes it from any other user that previously had it
                recruiter_of_the_month_role = thegye.get_role(813953181234626582)
                for members in thegye.members:
                    await members.remove_roles(recruiter_of_the_month_role)
                user = thegye.get_member(top_recruiter_user)
                await user.add_roles(recruiter_of_the_month_role)
                # calculates the monthly total for all recruitment telegrams
                monthly_total = 0
                for s in top_recruiter:
                    monthly_total += s['sent_this_month']
                # give recruiter of the month 500 thaler
                await conn.execute('''UPDATE rbt_users SET funds = funds + 500 WHERE user_id = $1;''',
                                   user.id)
                await conn.execute('''UPDATE funds SET current_funds = current_funds - 500
                WHERE name = 'General Fund';''')
                # resets the role
                await recruiter_of_the_month_role.edit(color=discord.Color.light_grey(),
                                                       name="Recruiter of the Month")
                # send the announcement
                announce = await announcements.send(
                    f"**Congratulations to {user.mention}!**\n{user.display_name} has earned the "
                    f"distinction of being this month's top recruiter! This month, they have sent "
                    f"{top_recruiter_numbers} telegrams to new players. Wow! {user.display_name} has "
                    f"been awarded the {recruiter_of_the_month_role.mention} role, customizable by "
                    f"request. {user.display_name} has also received a bonus of 500 thaler!"
                    f"Everyone give them a round of applause!\nIn total, {monthly_total:,} telegrams have been "
                    f"sent by our wonderful recruiters this month!")
                await announce.add_reaction("\U0001f44f")
                # clears all sent_this_month
                await conn.execute('''UPDATE recruitment SET sent_this_month = 0;''')
                continue

        async def retention(bot):
            # wait for the bot to be ready
            await bot.wait_until_ready()
            # define channels
            recruitment_channel = bot.get_channel(674342850296807454)
            crashchannel = bot.get_channel(835579413625569322)
            thegye_server = bot.get_guild(674259612580446230)
            notifrole = thegye_server.get_role(950950836006187018)
            # let the crash channel know
            await crashchannel.send("Starting retention loop.")
            try:
                # connect to the API
                async with aiohttp.ClientSession() as session:
                    headers = {"User-Agent": "Bassiliya"}
                    params = {'q': 'nations',
                              'region': 'thegye'}
                    async with session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                           headers=headers, params=params) as recruitsresp:
                        nations = await recruitsresp.text()
                        # ratelimiter
                        while True:
                            # see if there are enough available calls. if so, break the loop
                            try:
                                await self.rate_limit.call()
                                break
                            # if there are not enough available calls, continue the loop
                            except TooManyRequests as error:
                                await asyncio.sleep(int(str(error)))
                                continue
                    # parse out current nations and set
                    citizen_soup = BeautifulSoup(nations, 'lxml')
                    self.all_nations = set(citizen_soup.nations.text.split(':'))
                    while True:
                        async with session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                               headers=headers, params=params) as recruitsresp:
                            nations = await recruitsresp.text()
                            # ratelimiter
                            while True:
                                # see if there are enough available calls. if so, break the loop
                                try:
                                    await self.rate_limit.call()
                                    break
                                # if there are not enough available calls, continue the loop
                                except TooManyRequests as error:
                                    await asyncio.sleep(int(str(error)))
                                    continue
                        # parse out new recruits
                        new_nations_soup = BeautifulSoup(nations, 'lxml')
                        # if the site is down, continue after 15 minutes
                        try:
                            crashcheck = new_nations_soup.nations.text
                        except AttributeError:
                            await crashchannel.send(f"Database error. Retrying in 15 minutes.")
                            await asyncio.sleep(900)
                            continue
                        # the new nations are set and parsed
                        self.new_nations = set(new_nations_soup.nations.text.split(':')).difference(
                            self.all_nations)
                        # parses departed nations
                        departed_nations = self.all_nations.difference(set(new_nations_soup.nations.text.split(':')))
                        # for every new nation, send a notification
                        if self.new_nations:
                            for n in self.new_nations:
                                notif = await recruitment_channel.send(
                                    f"A new nation has arrived, {notifrole.mention}!"
                                    f"\nhttps://www.nationstates.net/nation={n}")
                                await notif.add_reaction("\U0001f4ec")
                        # for every nation in departed nations, send notification
                        if departed_nations:
                            for n in departed_nations:
                                async with session.get(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={n}",
                                                       headers=headers) as exist:
                                    # ratelimiter
                                    while True:
                                        # see if there are enough available calls. if so, break the loop
                                        try:
                                            await self.rate_limit.call()
                                            break
                                        # if there are not enough available calls, continue the loop
                                        except TooManyRequests as error:
                                            await asyncio.sleep(int(str(error)))
                                            continue
                                    try:
                                        exist.raise_for_status()
                                    except Exception:
                                        continue
                                # define and send notification
                                notif = await recruitment_channel.send(f"A nation has departed, {notifrole.mention}!"
                                                                       f"\nhttps://www.nationstates.net/nation={n}")
                                await notif.add_reaction("\U0001f4ec")
                        # set all nations to the new nations and sleep 5 minutes
                        self.all_nations = set(new_nations_soup.nations.text.split(':'))
                        await asyncio.sleep(300)
                        continue
            except Exception as error:
                await crashchannel.send(f"`{error}` in retention module.")
                error_log(error)

        async def world_assembly_notification(bot):
            try:
                # wait until the bot is ready
                await bot.wait_until_ready()
                # define channels
                wa_pings = bot.get_channel(676437972819640357)
                crashchannel = bot.get_channel(835579413625569322)
                thegye_server = bot.get_guild(674259612580446230)
                wa_role = thegye_server.get_role(674283915870994442)
                # notify crash channel
                await crashchannel.send("Starting WA notification loop.")
                # connect to API
                async with aiohttp.ClientSession() as session:
                    headers = {"User-Agent": "Bassiliya"}
                    params = {'q': 'nations',
                              'region': 'thegye'}
                    waparams = {'wa': '1',
                                'q': 'members'}
                    async with session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                           headers=headers, params=params) as nationsresp:
                        nations = await nationsresp.text()
                        # ratelimiter
                        while True:
                            # see if there are enough available calls. if so, break the loop
                            try:
                                await self.rate_limit.call()
                                break
                            # if there are not enough available calls, continue the loop
                            except TooManyRequests as error:
                                await asyncio.sleep(int(str(error)))
                                continue
                    # parse out nations
                    nationsoup = BeautifulSoup(nations, 'lxml')
                    try:
                        nations = set(nationsoup.nations.text.split(':'))
                    except AttributeError:
                        await crashchannel.send(f"Database error on WA .")
                    async with session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                           headers=headers, params=waparams) as membersresp:
                        members = await membersresp.text()
                        # ratelimiter
                        while True:
                            # see if there are enough available calls. if so, break the loop
                            try:
                                await self.rate_limit.call()
                                break
                            # if there are not enough available calls, continue the loop
                            except TooManyRequests as error:
                                await asyncio.sleep(int(str(error)))
                                continue
                    # parse out wa members
                    membersoup = BeautifulSoup(members, 'lxml')
                    members = set(membersoup.members.text.split(','))
                    self.all_wa = nations.intersection(members)
                    # start loop
                    while True:
                        async with session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                               headers=headers, params=params) as nationsresp:
                            nations = await nationsresp.text()
                            # ratelimiter
                            while True:
                                # see if there are enough available calls. if so, break the loop
                                try:
                                    await self.rate_limit.call()
                                    break
                                # if there are not enough available calls, continue the loop
                                except TooManyRequests as error:
                                    await asyncio.sleep(int(str(error)))
                                    continue
                        # parse out nations
                        nationsoup = BeautifulSoup(nations, 'lxml')
                        try:
                            nations = set(nationsoup.nations.text.split(':'))
                        except AttributeError:
                            await crashchannel.send(f"Database error. Retrying in 15 minutes.")
                            await asyncio.sleep(900)
                            continue
                        async with session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                               headers=headers, params=waparams) as membersresp:
                            members = await membersresp.text()
                            # ratelimiter
                            while True:
                                # see if there are enough available calls. if so, break the loop
                                try:
                                    await self.rate_limit.call()
                                    break
                                # if there are not enough available calls, continue the loop
                                except TooManyRequests as error:
                                    await asyncio.sleep(int(str(error)))
                                    continue
                        membersoup = BeautifulSoup(members, 'lxml')
                        members = nations.intersection(set(membersoup.members.text.split(',')))
                        # find new WA members
                        self.new_wa = members.difference(self.all_wa)
                        # if there are no new members, check back in 30 seconds
                        if len(members) == len(self.new_wa):
                            await asyncio.sleep(30)
                            continue
                        # if there are new wa members
                        if self.new_wa:
                            # for each new member, send notification
                            for n in Recruitment.new_wa:
                                wa_notif = await wa_pings.send(f"New World Assembly nation, {wa_role.mention}!"
                                                               f"\nPlease endorse: https://www.nationstates.net/nation={n}.")
                                await wa_notif.add_reaction("\U0001f310")
                        self.all_wa = members
                        await asyncio.sleep(300)
                        continue
            except Exception as error:
                error_log(error)

        # create 24/7 tasks
        self.monthly_recruiter = asyncio.create_task(monthly_recruiter(bot))
        self.retention = asyncio.create_task(retention(bot))
        self.world_assembly_notification = asyncio.create_task(world_assembly_notification(bot))

    def sanitize_links_percent(self, url: str) -> str:
        # sanitizes links with %s
        to_regex = url.replace("%", "%25")
        return re.sub(r"(%)", '%', to_regex)

    def sanitize_links_underscore(self, userinput: str) -> str:
        # replaces user input with proper, url-friendly code
        to_regex = userinput.replace(" ", "_")
        return re.sub(r"[^a-zA-Z0-9_-]", ' ', to_regex)

    def cog_unload(self):
        # stop the running tasks
        self.monthly_recruiter.cancel()
        self.retention.cancel()
        self.world_assembly_notification.cancel()

    # cog variables
    do_not_recruit = list()
    sending_to = list()
    all_nations = set()
    new_nations = set()
    all_wa = set()
    new_wa = set()
    user_sent = 0
    running = False
    recruitment_gather_object = None
    loops_gather_object = None

    async def recruitment_program(self, user,
                                  channel: discord.Interaction.channel, template):
        try:
            # runs the code until the stop command is given
            author = user
            # self.api_loop.cancel()
            while self.running:
                # call headers
                headers = {"User-Agent": "Bassiliya"}
                # make API call for newnations shard
                async with aiohttp.ClientSession() as session:
                    newnationsparams = {'q': 'newnations'}
                    async with session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                           headers=headers, params=newnationsparams) as nnresp:
                        await asyncio.sleep(.6)
                        newnationsraw = await nnresp.text()
                    # after the list is called, the xml is parsed and the list is made
                    nnsoup = BeautifulSoup(newnationsraw, "lxml")
                    newnations_prefilter = set(nnsoup.newnations.string.split(","))
                    # filters out any do not send to nations
                    newnations_post_filter = list(newnations_prefilter.difference(set(self.do_not_recruit)))
                    # grabs only the first eight
                    newnations = newnations_post_filter[0:8]
                    non_puppets = list()
                    # puppet filter
                    for nation in newnations:
                        # searches for numbers in names
                        number_puppet = re.search("\d+", nation)
                        # if there is a number, remove that nation and add it to the do not send list
                        if not number_puppet:
                            non_puppets.append(nation)
                            self.do_not_recruit.append(nation)
                    self.sending_to = [n for n in non_puppets]
                    # if there are no nations in the list, pause for 30 seconds and then restart the loop
                    if len(self.sending_to) == 0:
                        await asyncio.sleep(30)
                        continue
                    # for all the nations, add them to the string
                    recruit_string = ','.join(self.sending_to)
                    # parse the string to make it sanitized for the url
                    url = self.sanitize_links_percent(
                        f"https://www.nationstates.net/page=compose_telegram?tgto={recruit_string};"
                        f"message={template}")
                    # send the url and mention the author
                    await channel.send(f'{author.mention} [{len(self.sending_to)} nation(s)] {url}')
                    # if there is only one nation in the queue, and extra 15 seconds is waited
                    if len(self.sending_to) == 1:
                        await asyncio.sleep(15)
                    # adds the number of nations sent to
                    self.user_sent += len(self.sending_to)
                    # sleeps for 10 per nation
                    await asyncio.sleep(len(self.sending_to) * 10)
                    # adds the recruited nations to the do not send list and cleans up the lists
                    self.do_not_recruit += self.sending_to
                    self.sending_to.clear()
            return
        except asyncio.CancelledError:
            try:
                # establish connection
                conn = self.bot.pool
                # set running = false
                self.running = False
                # update relevant tables
                await conn.execute('''UPDATE recruitment SET sent = sent + $1, sent_this_month = sent_this_month + $1
                 WHERE user_id = $2;''', self.user_sent, user.id)
                await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                                   math.floor(self.user_sent / 2), user.id)
                await conn.execute('''UPDATE funds SET current_funds = current_funds - $1 WHERE name = 'General Fund';''',
                                   math.floor(self.user_sent / 2))
                await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                                   user.id, 'payroll', f"Earned \u20B8{math.floor(self.user_sent / 2)} from "
                                                       f"recruitment.")
                self.user_sent = 0
                # send end message
                await channel.send("Recruitment stopped. Another link may post.")
            except Exception as error:
                etype = type(error)
                trace = error.__traceback__
                lines = traceback.format_exception(etype, error, trace)
                traceback_text = ''.join(lines)
                self.bot.logger.warning(msg=f"{traceback_text}")
        except Exception as error:
            conn = self.bot.pool
            self.running = False
            # update relevant tables
            await conn.execute('''UPDATE recruitment SET sent = sent + $1, sent_this_month = sent_this_month + $1
             WHERE user_id = $2;''', self.user_sent, user.id)
            await conn.execute('''UPDATE rbt_users SET funds = funds + $1 WHERE user_id = $2;''',
                               math.floor(self.user_sent / 2), user.id)
            await conn.execute('''UPDATE funds SET current_funds = current_funds - $1 WHERE name = 'General Fund';''',
                               math.floor(self.user_sent / 2))
            await conn.execute('''INSERT INTO rbt_user_log VALUES($1,$2,$3);''',
                               user.id, 'payroll', f"Earned \u20B8{math.floor(self.user_sent / 2)} from "
                                                   f"recruitment.")
            await channel.send("The recruitment bot has run into an issue. Recruitment has stopped.")
            self.user_sent = 0
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            self.bot.logger.warning(msg=f"{traceback_text}")

    async def still_recruiting_check(self, user, channel):
        while self.running:
            # sleep for 10 minutes
            await asyncio.sleep(5)
            if self.running is False:
                break
            # sends message. if the reaction is hit, recruitment continues
            msg = await channel.send(f"Still recruiting,{user.mention}? "
                                     f"Hit the reaction within 3 minutes to continue.")
            await msg.add_reaction("\U0001f4e8")

            def check(reaction, user):
                return user == user and str(reaction.emoji) == "\U0001f4e8"

            try:
                # if reaction is hit, do nothing
                await self.bot.wait_for('reaction_add', timeout=5, check=check)

            except asyncio.TimeoutError:
                # if the reaction times out, stop the code
                self.recruitment_gather_object.cancel()
                break

    # creates recruitment group
    recruitment = app_commands.Group(name="recruitment", description="...")

    @recruitment.command(name="recruiter", description="Adds or removes the recruiter role.")
    @app_commands.guild_only()
    @app_commands.checks.has_role(674260547897917460)
    async def recruiter(self, interaction: discord.Interaction):
        # defer interation
        await interaction.response.defer(thinking=False)
        # define role, channel, and author
        recruiterrole = interaction.guild.get_role(674339578102153216)
        channel = self.bot.get_channel(674342850296807454)
        author = interaction.user
        # if the Recruiter role is not in the author roles, will add
        if recruiterrole not in author.roles:
            await author.add_roles(recruiterrole)
            await interaction.followup.send("Role added.")
            # sends message to new recruiter with mention
            await channel.send(f"**INSTRUCTIONS FOR BOT USE** \n- Follow the instructions for creating a template to "
                               f"send as recruitment in the pins. Once you have gotten your template, copy the ID. It "
                               f"should look something like this: `%TEMPLATE-000000%`\n- In this chat, "
                               f"type `$register [tempate]`, imputing your template ID, *without brackets*. \n- Once "
                               f"you have been registered, you may use the command `$recruit` to begin recruitment. "
                               f"\n- If you are finished recruiting, use the command `$stop` to stop recruitment. "
                               f"Another link may post.\n- Every ten minutes, a you will receive a message with a "
                               f"reaction asking if you are still recruiting. Hit the reaction within 3 minutes to continue "
                               f"recruitment. If you fail to do so, the recruitment will time out.\n- If you "
                               f"have questions, feel free to ask Lies Kryos#1734 or Secret#1982. If you want a list of commands, "
                               f"simply type `$help Recruitment`. If you would like to re-read these instructions, "
                               f"use the `$instructions` command to review them. Happy recruiting, {author.mention}!")
        # if the Recruiter role is in the author roles, will remove
        if recruiterrole in author.roles:
            await author.remove_roles(recruiterrole)
            await interaction.followup.send("Role removed.")

    @recruitment.command(name="recruit", description="Starts recruitment.")
    @app_commands.guild_only()
    @RecruitmentCheck()
    async def recruit(self, interaction: discord.Interaction):
        # defers interaction
        await interaction.response.defer(thinking=False)
        # checks status
        if self.running:
            waiting = discord.utils.get(interaction.guild.emojis, name="itsaguywaiting")
            already = await interaction.followup.send("Someone is already recruiting! Wait for them to finish first.")
            await already.add_reaction(waiting)
            return
        # connects to database
        conn = self.bot.pool
        author = interaction.user
        # fetches template
        recruiter = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', author.id)
        # if the user is not registered
        if recruiter is None:
            await interaction.followup.send("User not registered.")
            return
        # gathers the template, beings the code
        template = recruiter['template']
        self.running = True
        self.user_sent = 0
        user = interaction.user
        channel = interaction.channel
        # gathers two asyncio functions together to run simultaneously
        await interaction.followup.send("Gathering...")
        self.recruitment_gather_object = asyncio.gather(self.recruitment_program(user=user,
                                                                                 channel=channel, template=template),
                                                        self.still_recruiting_check(user=user,
                                                                                    channel=channel))

    @recruitment.command(name="stop", description="Stops recruitment.")
    @app_commands.guild_only()
    @RecruitmentCheck()
    async def stop(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=False)
        # if the recruitment is not running
        if self.running is False:
            return await interaction.followup.send("Recruitment is not running.")
        # delete thinking
        message = await interaction.followup.send("Stopping...")
        await interaction.followup.delete_message(message.id)
        # sets the running to false, quitting the loops
        self.running = False
        self.recruitment_gather_object.cancel()
        return

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def rstatus(self, ctx):
        # checks the status of the code
        if self.running is True:
            await ctx.send("Recruitment is running.")
        elif self.running is False:
            await ctx.send("Recruitment is not running.")

    @recruitment.command(name="sent", description="Displays the amount of sent telegrams of a specified user")
    @app_commands.guild_only()
    @RecruitmentCheck()
    async def sent(self, interaction: discord.Interaction, user: discord.User = None, global_sent: bool = None):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # connects to database
        conn = self.bot.pool
        # if the call is for the author
        if user is None:
            author = interaction.user
            # fetches relevant user data
            userinfo = await conn.fetchrow('''SELECT sent FROM recruitment WHERE user_id = $1;''', author.id)
            sent = userinfo['sent']
            if sent is None:
                await interaction.followup.send("You are not registered.")
            # sends amount
            await interaction.followup.send(f"{author} has sent {sent:,} telegrams.")
            return
        else:
            # connects to the database
            conn = self.bot.pool  # fetches relevant user data and sends it
            userinfo = await conn.fetchrow('''SELECT sent FROM recruitment WHERE user_id = $1;''', user.id)
            sent = userinfo['sent']
            if sent is None:
                await interaction.followup.send(f"{user.display_name} is not registered.")
                return
            await interaction.followup.send(f"{user} has sent {sent:,} telegrams.")
        if global_sent is True:
            # fetches relevant data
            allsent = await conn.fetch('''SELECT sent, sent_this_month FROM recruitment;''')
            totalsent = 0
            monthlytotal = 0
            for s in allsent:
                totalsent += s['sent']
                monthlytotal += s['sent_this_month']
            # sends amount
            await interaction.followup.send(
                f"A total of {totalsent:,} telegrams have been sent.\nA total of {monthlytotal:,} telegrams "
                f"have been sent this month.")
            return

    @recruitment.command(name="rank", description="Displays the all time or monthly ranks.")
    @app_commands.guild_only()
    @RecruitmentCheck()
    async def rank(self, interaction: discord.Interaction, monthly: bool = None):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # connects to the database
        conn = self.bot.pool
        # if the user wants the regular ranks
        if monthly is None:
            # fetches all user information, sorted by 'sent'
            userinfo = await conn.fetch('''SELECT * FROM recruitment WHERE sent > 0
                                        ORDER BY sent DESC
                                        LIMIT 10;''')
            ranksstr = "**__Top 10 Recruiters__**\n"
            # adds each user, by rank, to the list
            rank = 1
            for ranks in userinfo:
                userstring = f"**{rank}.** {self.bot.get_user(ranks['user_id'])}: {ranks['sent']:,}\n"
                ranksstr += userstring
                rank += 1
            return await interaction.followup.send(f"{ranksstr}")
        # if the user wants the sent monthly list
        if monthly is True:
            # fetches relevant user data, sorted by 'sent_this_month`
            userinfo = await conn.fetch('''SELECT * FROM recruitment WHERE sent_this_month > 0 
            ORDER BY sent_this_month DESC LIMIT 10;''')
            ranksstr = "**__Top 10 Recruiters (this month)__**\n"
            # adds each user, by rank, to the list
            rank = 1
            for ranks in userinfo:
                userstring = f"**{rank}.** {self.bot.get_user(ranks['user_id'])}: {ranks['sent_this_month']:,}\n"
                ranksstr += userstring
                rank += 1
            return await interaction.followup.send(f"{ranksstr}")

    @recruitment.command(name="register", description="Registers a user and a template")
    @app_commands.guild_only()
    @RecruitmentCheck()
    async def register(self, interaction: discord.Interaction, template_id: str):
        # defer interaction
        await interaction.response.defer(thinking=True)
        author = interaction.user
        # connects to the database
        conn = self.bot.pool
        # fetches data to ensure that the user doesn't exist
        exist = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', author.id)
        # if the user already exists
        if exist is not None:
            return await interaction.followup.send("You are already registered!")
        # inserts data into database
        await conn.execute('''INSERT INTO recruitment(user_id, template) VALUES($1, $2);''', author.id, template_id)
        await interaction.followup.send(f"Registered successfully with template ID: `{template_id}`.")

    @recruitment.command(name="edit_template", description="Edits an existing template.")
    @app_commands.guild_only()
    @RecruitmentCheck()
    async def edit_template(self, interaction: discord.Interaction, template_id: str):
        # defer response
        await interaction.response.defer(thinking=True)
        author = interaction.user
        # connects to database
        conn = self.bot.pool
        # checks for user existance
        exist = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', author.id)
        # if the user does not exist
        if exist is None:
            await interaction.followup.send("You are not registered!")
            return
        # updates the template
        await conn.execute('''UPDATE recruitment SET template = $2 WHERE user_id = $1;''', author.id, template_id)
        await interaction.followup.send(f"Template ID for {author} set to `{template_id}` successfully.")

    @recruitment.command(name="view_template", description="Displays a user's template")
    @app_commands.guild_only()
    @RecruitmentCheck()
    async def view_template(self, interaction: discord.Interaction):
        # defer response
        await interaction.response.defer(thinking=True)
        author = interaction.user
        # connects to database
        conn = self.bot.pool
        try:
            # fetches user data
            template = await conn.fetchrow('''SELECT template FROM recruitment WHERE user_id = $1;''', author.id)
            # if the user does not exist
            if template is None:
                return await interaction.followup.send("You are not registered!")
            # sends relevant data, along with access link
            template = template['template']
            templateid = re.findall(r"\d+", template)
            templateid = list(map(int, templateid))
            await interaction.followup.send(f"{author.name}'s template is {template}.\n"
                           f"The telegram template can be found here: "
                           f"https://www.nationstates.net/page=tg/tgid={templateid[0]}")
            return
        except Exception as error:
            self.error_handler(error)

    @commands.command(brief="Generates a WA campaign")
    @commands.guild_only()
    async def campaign(self, ctx):
        version = 'WACU v.2.1'
        start = perf_counter()
        conn = self.bot.pool
        regions = await conn.fetchrow('''SELECT * FROM wacu WHERE server_id = $1;''', ctx.guild.id)
        if regions is None:
            await ctx.send("This server has no authorized campaign.")
        # pull all nations from Thegye that are in the WA
        nations = await conn.fetch('''SELECT name, endorsements FROM nation_dump 
                                    WHERE region = $1 and wa_member = True;''', regions['region'])
        # creates the dicts, one for tracking all endorsements received and all outgoing endorsements missing
        all_endorsements = dict()
        all_endos_missing = dict()
        # for all the items in the database call, record their current endorsements
        for nation in nations:
            # list comprehension to sanitize all the dump data and then input all the data into all_endorsements
            endorsements = [self.sanitize_links_underscore(n.lower()) for n in nation['endorsements']]
            all_endorsements.update({self.sanitize_links_underscore(nation['name'].lower()): endorsements})
        # for every nation in the record
        for nation in all_endorsements:
            # the list of nations missing and needing to be endorsed
            endos_missing = list()
            # for every nation within the all_endorsements dict, pull their endorsement list
            for targeted_nation in all_endorsements:
                # if the initial nation is not in the endorsement list of the current target
                if nation not in all_endorsements[targeted_nation]:
                    # and that current target is not the same as the initial nation
                    if targeted_nation != nation:
                        # add the current target to the list
                        endos_missing.append(targeted_nation)
            # once all the comprehension is done, add the entire list to the dict and move to the next target
            all_endos_missing.update({nation: endos_missing})
        urls = dict()
        for nation in all_endos_missing:
            all_targets = [n for n in all_endos_missing[nation]]
            tgbody = regions['telegram_template']
            for n in all_targets:
                tgbody += f"[nation]{n}[/nation]"
            tgbody += "[/spoiler]"
            if len(all_targets) != 0:
                telegramurl = f"https://www.nationstates.net/page=compose_telegram?tgto={nation};message={quote(tgbody)}"
                urls.update({nation: telegramurl})
        htmlstring = str()
        for telegram in urls:
            # generates the link to the html code
            htmlcode = f"<a href=\"{urls[telegram]}\" id={telegram} target=\"_blank\" onclick=\"striketext(id)\">{self.sanitize_links_underscore(telegram).title()}  </a><br>\n"
            # adds the html to the end of the string
            htmlstring += htmlcode
        htmlfile = "<!DOCTYPE html>\n" \
                   f"<!UPDATED: {strftime('%Y-%m-%d %H:%M:%S')}>\n" \
                   f"<!VERSION: {version}>\n" \
                   "<html lang=\"en\">\n" \
                   "<head>\n" \
                   "<meta charset=\"UTF-8\">\n" \
                   f"<title>{regions['region'].title()} Endorsement Campaign</title>\n" \
                   "</head>\n" \
                   "<body style=\"line-height:200%; background-color:#FFFDD0; font-family:'Courier New';\">\n" \
                   "<script>\nfunction striketext(id) {\n" \
                   "  document.getElementById(id).style.textDecoration=\"line-through\";}\n</script>\n" \
                   f"{htmlstring}\n" \
                   "</body>\n" \
                   "</html>\n" \
            # writes the html to a file
        with open(fr"{self.directory}{regions['region'].lower()}_endo_campaign.html", "w+") as writefile:
            writefile.write(htmlfile)
        with open(fr"{self.directory}{regions['region'].lower()}_endo_campaign.html", "r") as campaign:
            async with ctx.channel.typing():
                await ctx.send(file=discord.File(campaign, f"{regions['region'].lower()}_endo_campaign.html"))

    @commands.command(usage="[hex color code] [name]",
                      brief="Allows the Recruiter of the Month to customize their role")
    async def customize_recruiter_role(self, ctx, color: str, *args):
        # check to see if the author has the proper role
        recruiter_of_the_month_role = discord.utils.get(ctx.guild.roles, id=813953181234626582)
        name = ' '.join(args)
        # if they do not, return the error
        if recruiter_of_the_month_role not in ctx.author.roles:
            raise commands.MissingRole(recruiter_of_the_month_role)
        else:
            try:
                # get the color, catch any color input errors, and change the role name and color
                color = (x, y, z) = ImageColor.getrgb(color)
                rolecolor = discord.Color.from_rgb(*color)
                await recruiter_of_the_month_role.edit(color=rolecolor, name=f"{name} (Recruiter of the Month)")
                await ctx.send(f"Color changed to `{rolecolor}` and name changed to `{name}` successfully!")
            except ValueError:
                await ctx.send("That doesn't appear to be a valid hex color code.")
                return

    @commands.command(brief="Adds or removes the retention role")
    @RecruitmentCheck()
    async def retention(self, ctx):
        # get the retention role and channel
        retention_role = discord.utils.get(ctx.guild.roles, id=950950836006187018)
        recruitment_channel = self.bot.get_channel(674342850296807454)
        # add the role if the author does not already have it and send instruction message
        if retention_role not in ctx.author.roles:
            await ctx.author.add_roles(retention_role)
            await recruitment_channel.send(f"**Welcome to the Order of Saint Julian, {ctx.author.mention}!**"
                                           f"\nYou can see our welcome telegram and exit telegram in the pins. "
                                           f"When a nation leaves or enters Thegye, you'll be notified via ping. If you"
                                           f" send a telegram to the nation, hit the \U0001f4ec emoji to let everyone"
                                           f" else know you've done so. Good luck!")
        # remove the role from the author if they already have it
        elif retention_role in ctx.author.roles:
            await ctx.author.remove_roles(retention_role)
            await ctx.send("Role removed.")


async def setup(bot):
    cog = Recruitment(bot)
    await bot.add_cog(cog)
