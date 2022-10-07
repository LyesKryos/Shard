# recruitment 1.1
from datetime import datetime
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
from customchecks import RecruitmentCheck
import traceback
import os


class Recruitment(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot
        self.db_error = False

        fd = os.open(os.devnull, os.O_RDWR)
        # NB: even if stdin is closed, fd >= 0
        os.dup2(fd, 1)
        os.dup2(fd, 2)
        if fd > 2:
            os.close(fd)

        def error_log(error):
            etype = type(error)
            trace = error.__traceback__
            lines = traceback.format_exception(etype, error, trace)
            traceback_text = ''.join(lines)
            self.bot.logger.warning(msg=f"{traceback_text}")

        async def monthly_recruiter_scheduler(bot):
            await bot.wait_until_ready()
            # fetches channel object
            crashchannel = bot.get_channel(835579413625569322)
            while True:
                # sets up asyncio scheduler
                eastern = timezone('US/Eastern')
                # identifies now
                now = datetime.now(eastern)
                next_month = now.month + 1
                runtime = now.replace(day=1, month=next_month, hour=0, minute=0, second=0)
                await crashchannel.send(
                    f"Monthly recruiter next run: {runtime.strftime('%a, %d %b %Y at %H:%M:%S %Z%z')}")
                await discord.utils.sleep_until(runtime)
                await monthly_recruiter(bot)
                continue

        async def monthly_recruiter(bot):
            await bot.wait_until_ready()
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
            # resets the role
            await recruiter_of_the_month_role.edit(color=discord.Color.light_grey(),
                                                   name="Recruiter of the Month")
            # send the announcement
            announce = await announcements.send(
                f"**Congratulations to {user.mention}!**\n{user.display_name} has earned the "
                f"distinction of being this month's top recruiter! This month, they have sent "
                f"{top_recruiter_numbers} telegrams to new players. Wow! {user.display_name} has "
                f"been awarded the {recruiter_of_the_month_role.mention} role, customizable by "
                f"request. Everyone give them a round of applause!\nIn total, {monthly_total:,} telegrams have been "
                f"sent by our wonderful recruiters this month!")
            await announce.add_reaction("\U0001f44f")
            # clears all sent_this_month
            await conn.execute('''UPDATE recruitment SET sent_this_month = 0;''')
            self.monthly_recruiter_notification = True
            return

        async def retention(bot):
            await bot.wait_until_ready()
            crashchannel = bot.get_channel(835579413625569322)
            recruitment_channel = bot.get_channel(674342850296807454)
            thegye_server = bot.get_guild(674259612580446230)
            notifrole = discord.utils.get(thegye_server.roles, id=950950836006187018)
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"User-Agent": "Bassiliya"}
                    params = {'q': 'nations',
                              'region': 'thegye'}
                    async with session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                           headers=headers, params=params) as recruitsresp:
                        recruits = await recruitsresp.text()
                        await asyncio.sleep(.6)
                    recruitssoup = BeautifulSoup(recruits, 'lxml')
                    Recruitment.all_nations = set(recruitssoup.nations.text.split(':'))
                    while True:
                        async with session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                               headers=headers, params=params) as recruitsresp:
                            recruits = await recruitsresp.text()
                            await asyncio.sleep(.6)
                        recruitssoup = BeautifulSoup(recruits, 'lxml')
                        crashcheck = recruitssoup.nations.text
                        if re.search("Database Connection Error", crashcheck):
                            await crashchannel.send("Error: `NationStates Database Connection Error`"
                                                    "\nWaiting 15 minutes and retrying.")
                            bot.db_error = True
                            await asyncio.sleep(900)
                            continue
                        else:
                            bot.db_error = False
                        Recruitment.new_nations = set(recruitssoup.nations.text.split(':')).difference(
                            Recruitment.all_nations)
                        departed_nations = Recruitment.all_nations.difference(set(recruitssoup.nations.text.split(':')))
                        if Recruitment.new_nations:
                            for n in Recruitment.new_nations:
                                notif = await recruitment_channel.send(
                                    f"A new nation has arrived, {notifrole.mention}!"
                                    f"\nhttps://www.nationstates.net/nation={n}")
                                await notif.add_reaction("\U0001f4ec")
                        if departed_nations:
                            for n in departed_nations:
                                async with session.get(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={n}",
                                                       headers=headers) as exist:
                                    try:
                                        exist.raise_for_status()
                                    except Exception:
                                        continue
                                notif = await recruitment_channel.send(f"A nation has departed, {notifrole.mention}!"
                                                                       f"\nhttps://www.nationstates.net/nation={n}")
                                await notif.add_reaction("\U0001f4ec")
                        Recruitment.all_nations = set(recruitssoup.nations.text.split(':'))
                        await asyncio.sleep(300)
                        continue
            except Exception as error:
                await crashchannel.send(f"`{error}` in retention module.")
                error_log(error)

        async def world_assembly_notification(bot):
            try:
                await bot.wait_until_ready()
                wa_pings = bot.get_channel(676437972819640357)
                thegye_server = bot.get_guild(674259612580446230)
                wa_role = discord.utils.get(thegye_server.roles, id=674283915870994442)
                async with aiohttp.ClientSession() as session:
                    headers = {"User-Agent": "Bassiliya"}
                    params = {'q': 'nations',
                              'region': 'thegye'}
                    waparams = {'wa': '1',
                                'q': 'members'}
                    async with session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                           headers=headers, params=params) as nationsresp:
                        nations = await nationsresp.text()
                        await asyncio.sleep(.6)
                    nationsoup = BeautifulSoup(nations, 'lxml')
                    nations = set(nationsoup.nations.text.split(':'))
                    async with session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                           headers=headers, params=waparams) as membersresp:
                        members = await membersresp.text()
                        await asyncio.sleep(.6)
                    membersoup = BeautifulSoup(members, 'lxml')
                    members = set(membersoup.members.text.split(','))
                    Recruitment.all_wa = nations.intersection(members)
                    while True:
                        headers = {"User-Agent": "Bassiliya"}
                        params = {'q': 'nations',
                                  'region': 'thegye'}
                        waparams = {'wa': '1',
                                    'q': 'members'}
                        async with session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                               headers=headers, params=params) as nationsresp:
                            nations = await nationsresp.text()
                            await asyncio.sleep(.6)
                        nationsoup = BeautifulSoup(nations, 'lxml')
                        nations = set(nationsoup.nations.text.split(':'))
                        async with session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                               headers=headers, params=waparams) as membersresp:
                            members = await membersresp.text()
                            await asyncio.sleep(.6)
                        membersoup = BeautifulSoup(members, 'lxml')
                        members = nations.intersection(set(membersoup.members.text.split(',')))
                        Recruitment.new_wa = members.difference(Recruitment.all_wa)
                        if len(members) == len(Recruitment.new_wa):
                            await asyncio.sleep(30)
                            continue
                        if Recruitment.new_wa:
                            for n in Recruitment.new_wa:
                                wa_notif = await wa_pings.send(f"New World Assembly nation, {wa_role.mention}!"
                                                               f"\nPlease endorse: https://www.nationstates.net/nation={n}.")
                                await wa_notif.add_reaction("\U0001f310")
                        Recruitment.all_wa = members
                        await asyncio.sleep(300)
                        continue
            except Exception as error:
                error_log(error)

        @tasks.loop(seconds=180)
        async def api_recruitment():
            try:
                headers = {'User-Agent': 'Bassiliya'}
                params = {'client': '85eb458e',
                          'tgid': '25352330',
                          'key': 'b777d3383626'}
                async with aiohttp.ClientSession() as session:
                    newnationsparams = {'q': 'newnations'}
                    async with session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                           headers=headers, params=newnationsparams) as nnresp:
                        await asyncio.sleep(.6)
                        newnationsraw = await nnresp.text()
                        nnresp.close()
                    # after the list is called, the xml is parsed and the list is made
                    nnsoup = BeautifulSoup(newnationsraw, "lxml")
                    newnations_prefilter = set(nnsoup.newnations.string.split(","))
                    for nation in newnations_prefilter:
                        # searches for numbers in names
                        number_puppet = re.search("\d+", nation)
                        # if there is a number, remove that nation and add it to the do not send list
                        if number_puppet:
                            self.do_not_recruit.append(nation)
                    # filters out any do not send to nations
                    newnations_post_filter = list(newnations_prefilter.difference(set(self.do_not_recruit)))
                    # grabs only the first nation to send a telegram to
                    newnation = newnations_post_filter[0]
                    sending_to = newnation
                    params.update({'to': sending_to})
                    async with session.get('https://www.nationstates.net/cgi-bin/api.cgi?a=sendTG',
                                           headers=headers, params=params) as api_send:
                        await asyncio.sleep(.6)
                        if api_send.status != 200:
                            crash_channel = self.bot.get_channel(835579413625569322)
                            await crash_channel.send("API telegram sending error.")
                            if api_send.status == 429:
                                retry_after = await api_send.json()
                                await crash_channel.send(retry_after)
                            raise Exception(f"API received faulty response code: {api_send.status}\n{api_send.text}")
                        api_send.close()
                        return
            except Exception as error:
                error_log(error)


        loop = bot.loop
        self.monthly_loop = loop.create_task(monthly_recruiter_scheduler(bot))
        self.retention_loop = loop.create_task(retention(bot))
        self.world_assembly_notification_loop = loop.create_task(world_assembly_notification(bot))
        self.api_recruitment = api_recruitment
        self.api_recruitment.start()


    def sanitize_links_percent(self, url: str) -> str:
        # sanitizes links with %s
        to_regex = url.replace("%", "%25")
        return re.sub(r"(%)", '%', to_regex)

    def sanitize_links_underscore(self, userinput: str) -> str:
        # replaces user input with proper, url-friendly code
        to_regex = userinput.replace(" ", "_")
        return re.sub(r"[^a-zA-Z0-9_-]", ' ', to_regex)

    def cog_unload(self):
        self.retention_loop.cancel()
        self.monthly_loop.cancel()
        self.world_assembly_notification_loop.cancel()
        self.api_recruitment.cancel()
        # self.api_loop.cancel()

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

    async def recruitment(self, ctx, template):
        try:
            # runs the code until the stop command is given
            author = ctx.author
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
                    await ctx.send(f'{author.mention} {url}')
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
            await ctx.send("Recruitment stopped. Another link may post.")
            conn = self.bot.pool
            self.running = False
            userinfo = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', ctx.author.id)
            await conn.execute('''UPDATE recruitment SET sent = $1, sent_this_month = $2 WHERE user_id = $3;''',
                               (self.user_sent + userinfo['sent']),
                               (self.user_sent + userinfo['sent_this_month']),
                               ctx.author.id)
        except Exception:
            conn = self.bot.pool
            self.running = False
            await ctx.send("The recruitment bot has run into an issue. Recruitment has stopped.")
            userinfo = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', ctx.author.id)
            await conn.execute('''UPDATE recruitment SET sent = $1, sent_this_month = $2 WHERE user_id = $3;''',
                               (self.user_sent + userinfo['sent']),
                               (self.user_sent + userinfo['sent_this_month']),
                               ctx.author.id)
            self.user_sent = 0
            crashchannel = self.bot.get_channel(835579413625569322)
            await crashchannel.send(f"```{traceback.format_exc()}```")

    async def still_recruiting_check(self, ctx):
        while self.running:
            # connects to database
            conn = self.bot.pool
            # sleep for 10 minutes
            await asyncio.sleep(600)
            if self.running is False:
                break
            # sends mesage. if the reaction is hit, recruitment continues
            msg = await ctx.send(f"Still recruiting,{ctx.author.mention}? Hit the reaction within 3 minutes to "
                                 f"continue.")
            await msg.add_reaction("\U0001f4e8")

            def check(reaction, user):
                return user == ctx.message.author and str(reaction.emoji) == "\U0001f4e8"

            try:
                # if reaction is hit, do nothing
                await self.bot.wait_for('reaction_add', timeout=180, check=check)

            except asyncio.TimeoutError:
                # if the reaction times out, stop the code
                self.running = False
                # updates information
                userinfo = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', ctx.author.id)
                await conn.execute('''UPDATE recruitment SET sent = $1, sent_this_month = $2 WHERE user_id = $3;''',
                                   (self.user_sent + userinfo['sent']),
                                   (self.user_sent + userinfo['sent_this_month']),
                                   ctx.author.id)
                self.user_sent = 0
                self.recruitment_gather_object.cancel()

                break

    @commands.command(brief="Adds or removes the recruiter role")
    @commands.guild_only()
    @commands.has_role(674260547897917460)
    async def recruiter(self, ctx):
        recruiterrole = ctx.guild.get_role(674339578102153216)
        channel = self.bot.get_channel(674342850296807454)
        author = ctx.author
        # gets all author roles
        authorroles = list()
        for ar in ctx.message.author.roles:
            authorroles.append(ar.id)
        # if the Recruiter role is not in the author roles, will add
        if recruiterrole.id not in authorroles:
            await author.add_roles(recruiterrole)
            await ctx.send("Role added.")
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
        if recruiterrole.id in authorroles:
            await author.remove_roles(recruiterrole)
            await ctx.send("Role removed.")

    @commands.command(brief="Begins the recruitment process")
    @commands.guild_only()
    @RecruitmentCheck()
    async def recruit(self, ctx):
        # checks status
        if self.running:
            waiting = discord.utils.get(ctx.guild.emojis, name="itsaguywaiting")
            already = await ctx.send("Someone is already recruiting! Wait for them to finish first.")
            await already.add_reaction(waiting)
            return
        # connects to database
        conn = self.bot.pool
        author = ctx.author
        # fetches template
        recruiter = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', author.id)
        # if the user is not registered
        if recruiter is None:
            await ctx.send("User not registered.")
            return
        # gathers the template, beings the code
        template = recruiter['template']
        self.running = True
        await ctx.send("Gathering...")
        # gathers two asyncio functions together to run simultaneously
        self.recruitment_gather_object = asyncio.gather(self.recruitment(ctx, template),
                                                        self.still_recruiting_check(ctx))

    @commands.command(brief="Stops the recruitment process")
    @commands.guild_only()
    @RecruitmentCheck()
    async def stop(self, ctx):
        # if the recruitment is not running
        if self.running is False:
            await ctx.send("Recruitment is not running.")
            return
        author = ctx.author
        # sets the running to false, quitting the loops
        self.running = False
        # connects to database
        conn = self.bot.pool
        # fetches relevant user info
        userinfo = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', author.id)
        # updates relevant user info
        await conn.execute('''UPDATE recruitment SET sent = $1, sent_this_month = $2 WHERE user_id = $3;''',
                           (self.user_sent + userinfo['sent']), (self.user_sent + userinfo['sent_this_month']),
                           ctx.author.id)
        self.user_sent = 0
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
        if self.monthly_loop:
            await ctx.send("Recruiter of the Month running.")
        elif not self.monthly_loop:
            await ctx.send("Recruiter of the Month not running.")
        if self.retention_loop:
            await ctx.send("Retention running.")
        elif not self.retention_loop:
            await ctx.send("Retention not running.")
        if self.world_assembly_notification_loop:
            await ctx.send("WA notification running.")
        elif not self.world_assembly_notification_loop:
            await ctx.send("WA notification not running.")

    @commands.command(brief="Starts the API recruitment loop.")
    @commands.is_owner()
    async def api_start(self, ctx):
        # starts API loop
        await self.api_recruitment.start()
        await asyncio.sleep(3)
        if self.api_recruitment.is_running():
            await ctx.send("API loop running!")
        else:
            await ctx.send("API loop failed to start.")

    @commands.command(brief="Stops the API recruitment loop.")
    @commands.is_owner()
    async def api_stop(self, ctx):
        # stops API loop
        self.api_recruitment.cancel()
        await asyncio.sleep(3)
        if self.api_recruitment.is_running():
            await ctx.send("API loop is still running!")
        else:
            await ctx.send("API loop cancelled.")

    @commands.command(usage="<(user, global)>",
                      brief="Displays sent information for a specified user, the requesting user, or all sent telegrams")
    @commands.guild_only()
    @RecruitmentCheck()
    async def sent(self, ctx, *, args=None):
        # fetches the sent amount of the specified user
        author = ctx.author
        # connects to database
        conn = self.bot.pool
        # if the call is for the author
        if args is None:
            # fetches relevant user data
            userinfo = await conn.fetchrow('''SELECT sent FROM recruitment WHERE user_id = $1;''', author.id)
            sent = userinfo['sent']
            if sent is None:
                await ctx.send("You are not registered.")
            # sends amount
            await ctx.send(f"{author} has sent {sent} telegrams.")
            return
        elif args == "global":
            # fetches relevant user data
            allsent = await conn.fetch('''SELECT sent, sent_this_month FROM recruitment;''')
            totalsent = 0
            monthlytotal = 0
            for s in allsent:
                totalsent += s['sent']
                monthlytotal += s['sent_this_month']
            # sends amount
            await ctx.send(
                f"A total of {totalsent:,} telegrams have been sent.\nA total of {monthlytotal:,} telegrams "
                f"have been sent this month.")
            return
        elif args is not None:
            # fetches the user object via the converter
            user = args
            user = await commands.converter.MemberConverter().convert(ctx, user)
            # connects to the database
            conn = self.bot.pool  # fetches relevant user data and sends it
            userinfo = await conn.fetchrow('''SELECT sent FROM recruitment WHERE user_id = $1;''', user.id)
            sent = userinfo['sent']
            if sent is None:
                await ctx.send(f"{user.display_name} is not registered.")
                return
            await ctx.send(f"{user} has sent {sent} telegrams.")

    @commands.command(usage="<m>", brief="Displays the all time or monthly ranks")
    @commands.guild_only()
    @RecruitmentCheck()
    async def rank(self, ctx, monthly: str = None):
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
                userstring = f"**{rank}.** {self.bot.get_user(ranks['user_id'])}: {ranks['sent']}\n"
                ranksstr += userstring
                rank += 1
            await ctx.send(f"{ranksstr}")

            return
        # if the user wants the sent monthly list
        elif monthly in ['m', 'month', 'monthly']:
            # fetches relevant user data, sorted by 'sent_this_month`
            userinfo = await conn.fetch('''SELECT * FROM recruitment WHERE sent_this_month > 0 
            ORDER BY sent_this_month DESC LIMIT 10;''')
            ranksstr = "**__Top 10 Recruiters (this month)__**\n"
            # adds each user, by rank, to the list
            rank = 1
            for ranks in userinfo:
                userstring = f"**{rank}.** {self.bot.get_user(ranks['user_id'])}: {ranks['sent_this_month']}\n"
                ranksstr += userstring
                rank += 1
            await ctx.send(f"{ranksstr}")
            return
        else:
            raise commands.UserInputError()

    @commands.command(usage='[template id]', brief="Registers a user and a template")
    @commands.guild_only()
    @RecruitmentCheck()
    async def register(self, ctx, templateid):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # fetches data to ensure that the user doesn't exist
        exist = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', author.id)
        # if the user already exists
        if exist is not None:
            await ctx.send("You are already registered!")
            return
        # inserts data into database
        await conn.execute('''INSERT INTO recruitment(user_id, template) VALUES($1, $2);''', author.id, templateid)
        await ctx.send(f"Registered successfully with template ID: `{templateid}`.")

    @commands.command(usage='[template id]', brief="Edits an existing template")
    @commands.guild_only()
    @RecruitmentCheck()
    async def edit_template(self, ctx, templateid):
        author = ctx.author
        # connects to database
        conn = self.bot.pool
        # checks for user existance
        exist = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', author.id)
        # if the user does not exist
        if exist is None:
            await ctx.send("You are not registered!")
            return
        # updates the template
        await conn.execute('''UPDATE recruitment SET template = $2 WHERE user_id = $1;''', author.id, templateid)
        await ctx.send(f"Template ID for {author} set to `{templateid}` successfully.")

    @commands.command(brief="Displays a user's template")
    @commands.guild_only()
    @RecruitmentCheck()
    async def view_template(self, ctx):
        author = ctx.author
        # connects to database
        conn = self.bot.pool
        try:
            # fetches user data
            template = await conn.fetchrow('''SELECT template FROM recruitment WHERE user_id = $1;''', author.id)
            # if the user does not exist
            if template is None:
                await ctx.send("You are not registered!")

                return
            # sends relevant data, along with access link
            template = template['template']
            templateid = re.findall(r"\d+", template)
            templateid = list(map(int, templateid))
            await ctx.send(f"{author.name}'s template is {template}.\n"
                           f"The telegram template can be found here: "
                           f"https://www.nationstates.net/page=tg/tgid={templateid[0]}")
            return
        except Exception as error:
            await ctx.send(error)

            return

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
    await bot.wait_until_ready()

    await bot.add_cog(Recruitment(bot))
