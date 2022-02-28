# recruitment 1.02

from urllib.parse import quote
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands
import discord
import asyncio
from bs4 import BeautifulSoup
import re
import asyncpg
from main import bot
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from time import perf_counter, strftime


class RecruitmentChecks(commands.CheckFailure):
    pass


def RecruitmentCheck():
    # custom check
    async def recruitmentcheck(ctx):
        if ctx.author.id == 293518673417732098:
            return True
        else:
            userroles = [role.id for role in ctx.author.roles]
            if 674339578102153216 not in userroles:
                raise RecruitmentChecks(
                    f"You are not authorized to use this command. Use `{bot.command_prefix}recruiter"
                    f"to get the required role.")
            elif ctx.channel.id != 674342850296807454:
                raise RecruitmentChecks(f"This is the wrong channel for that. Please make sure you are using only the"
                                        f"#recruitment channel")
            return True

    return commands.check(recruitmentcheck)


class Recruitment(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def sanitize_links_percent(self, url: str) -> str:
        # sanitizes links with %s
        to_regex = url.replace("%", "%25")
        return re.sub(r"(%)", '%', to_regex)

    def sanitize_links_underscore(self, userinput: str) -> str:
        # replaces user input with proper, url-friendly code
        to_regex = userinput.replace(" ", "_")
        return re.sub(r"[^a-zA-Z0-9_-]", ' ', to_regex)

    do_not_recruit = list()
    sending_to = list()
    user_sent = 0
    running = False
    recruitment_gather_object = None

    connectionstr = 'postgresql://postgres@127.0.0.1:5432'
    database = "botdb"
    password = "postgres"

    directory = r"C:\Users\jaedo\PycharmProjects\Discord Bot\\"

    async def recruitment(self, ctx, template):
        try:
            # runs the code until the stop command is given
            author = ctx.author
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
                    # puppet filter
                    for nation in newnations:
                        # searches for numbers in names
                        number_puppet = re.search("\d+", nation)
                        # if there is a number, remove that nation and add it to the do not send list
                        if number_puppet is not None:
                            if nation in self.sending_to:
                                newnations.remove(nation)
                                self.do_not_recruit.append(nation)
                        self.sending_to = [n for n in newnations]
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
            await ctx.send("Recuitment stopped. Another link may post.")
        except Exception as error:
            self.running = False
            await ctx.send("The recruitment bot has run into an issue. Recruitment has stopped.")
            print(error)

    async def still_recruiting_check(self, ctx):
        while self.running:
            # connects to database
            conn = await asyncpg.connect(self.connectionstr, database=self.database,
                                         password=self.password)
            try:
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
                    await bot.wait_for('reaction_add', timeout=180, check=check)

                except asyncio.TimeoutError:
                    # if the reaction times out, stop the code
                    self.running = False
                    self.recruitment_gather_object.cancel()
                    # updates information
                    userinfo = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', ctx.author.id)
                    await conn.execute('''UPDATE recruitment SET sent = $1, sent_this_month = $2 WHERE user_id = $3;''',
                                       (self.user_sent + userinfo['sent']),
                                       (self.user_sent + userinfo['sent_this_month']),
                                       ctx.author.id)
                    self.user_sent = 0
                    await conn.close()
                    break
            except Exception as error:
                print(error)
                await conn.close()
        return

    @commands.command()
    @commands.guild_only()
    @commands.has_role(674260547897917460)
    async def recruiter(self, ctx):
        recruiterrole = ctx.guild.get_role(848695379058360411)
        channel = bot.get_channel(674342850296807454)
        author = ctx.author
        # gets all author roles
        authorroles = list()
        for ar in ctx.message.author.roles:
            authorroles.append(ar.id)
        # if the Recruiter role is not in the author roles, will add
        if recruiterrole not in authorroles:
            await author.add_roles(recruiterrole)
            await ctx.send("Role added.")
            # sends message to new recruiter with mention
            await channel.send(f"**INSTRUCTIONS FOR BOT USE** \n- Follow the instructions for creating a template to "
                               f"send as recruitment in the pins. Once you have gotten your template, copy the ID. It "
                               f"should look something like this: `%TEMPLATE-000000%`\n- In this chat, "
                               f"type `$register [tempate]`, imputing your template ID, *without brackets*. \n- Once "
                               f"you have been registered, you may use the command `$recruit` to begin recruitment. "
                               f"\n- If you are finished recruiting, use the command `$stop` to stop recruitment. "
                               f"Wait at least 30 seconds before restarting recruitment or face the wrath of the "
                               f"Shard. \n- Every ten minutes, a you will receive a message with a reaction, "
                               f"asking if you are still recruiting. Hit the reaction within 3 minutes to continue "
                               f"recruitment. If you fail to do so, the recruitment will time out. *Wait a few "
                               f"minutes before restarting recruitment, or face the wrath of the Shard.*\n- If you "
                               f"have questions, feel free to ask Lies Kryos#1734 or Secret#1982. If you want a list of commands, "
                               f"simply type `$help Recruitment`. If you would like to re-read these instructions, "
                               f"use the `$instructions` command to review them. Happy recruiting, {author.mention}!")
        # if the Recruiter role is in the author roles, will remove
        if recruiterrole in authorroles:
            await author.remove_roles(recruiterrole)
            await ctx.send("Role removed.")

    @commands.command()
    @commands.guild_only()
    @RecruitmentCheck()
    async def recruit(self, ctx):
        # checks status
        if self.running:
            await ctx.send("Someone is already recruiting! Wait for them to finish first.")
            return
        # connects to database
        conn = await asyncpg.connect(self.connectionstr, database=self.database,
                                     password=self.password)
        author = ctx.author
        # fetches template
        recruiter = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', author.id)
        # if the user is not registered
        if recruiter is None:
            await ctx.send("User not registered.")
            await conn.close()
            return
        # gathers the template, beings the code
        template = recruiter['template']
        self.running = True
        await conn.close()
        await ctx.send("Gathering...")
        # gathers two asyncio functions together to run simultaneously
        self.recruitment_gather_object = asyncio.gather(self.recruitment(ctx, template),
                                                        self.still_recruiting_check(ctx))
        

    @commands.command()
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
        self.recruitment_gather_object.cancel()
        # connects to database
        conn = await asyncpg.connect(self.connectionstr, database=self.database,
                                     password=self.password)
        try:
            # fetches relevant user info
            userinfo = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', author.id)
            # updates relevant user info
            await conn.execute('''UPDATE recruitment SET sent = $1, sent_this_month = $2 WHERE user_id = $3;''',
                               (self.user_sent + userinfo['sent']), (self.user_sent + userinfo['sent_this_month']),
                               ctx.author.id)
            self.user_sent = 0
            await conn.close()
            return
        except Exception as error:
            await ctx.send(error)
            await conn.close()
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

    @commands.command()
    @commands.guild_only()
    @RecruitmentCheck()
    async def sent(self, ctx, *args):
        # fetches the sent amount of the specified user
        author = ctx.author
        # connects to database
        conn = await asyncpg.connect(self.connectionstr, database=self.database,
                                     password=self.password)
        # if the call is for the author
        if args == ():
            try:
                # fetches relevant user data
                userinfo = await conn.fetchrow('''SELECT sent FROM recruitment WHERE user_id = $1;''', author.id)
                sent = userinfo['sent']
                # sends amount
                await ctx.send(f"{author} has sent {sent} telegrams.")
                await conn.close()
                return
            except Exception as error:
                await ctx.send(error)
                await conn.close()
                return
        elif args != ():
            try:
                # fetches the user object via the converter
                user = ' '.join(args[:])
                user = await commands.converter.MemberConverter().convert(ctx, user)
                # connects to the database
                conn = await asyncpg.connect(self.connectionstr, database=self.database,
                                             password=self.password)
                # fetches relevant user data and sends it
                userinfo = await conn.fetchrow('''SELECT sent FROM recruitment WHERE user_id = $1;''', user.id)
                sent = userinfo['sent']
                await ctx.send(f"{user} has sent {sent} telegrams.")
                await conn.close()
                return
            except Exception as error:
                await ctx.send(error)
                await conn.close()
                return

    @commands.command(usage="<monthly? (m)>")
    @commands.guild_only()
    @RecruitmentCheck()
    async def rank(self, ctx, monthly: str = None):
        # connects to the database
        conn = await asyncpg.connect(self.connectionstr, database=self.database,
                                     password=self.password)
        try:
            # if the user wants the regular ranks
            if monthly is None:
                # fetches all user information, sorted by 'sent'
                userinfo = await conn.fetch('''SELECT * FROM recruitment 
                                            ORDER BY sent DESC
                                            LIMIT 10;''')
                ranksstr = "**__Top 10 Recruiters__**\n"
                # adds each user, by rank, to the list
                rank = 1
                for ranks in userinfo:
                    userstring = f"**{rank}.** {bot.get_user(ranks['user_id'])}: {ranks['sent']}\n"
                    ranksstr += userstring
                    rank += 1
                await ctx.send(f"{ranksstr}")
                await conn.close()
                return
            # if the user wants the sent monthly list
            elif monthly in ['m']:
                # fetches relevant user data, sorted by 'sent_this_month`
                userinfo = await conn.fetch('''SELECT * FROM recruitment ORDER BY sent_this_month DESC LIMIT 10;''')
                ranksstr = "**__Top 10 Recruiters (this month)__**\n"
                # adds each user, by rank, to the list
                rank = 1
                for ranks in userinfo:
                    userstring = f"**{rank}.** {bot.get_user(ranks['user_id'])}: {ranks['sent_this_month']}\n"
                    ranksstr += userstring
                    rank += 1
                await ctx.send(f"{ranksstr}")
                await conn.close()
                return
            else:
                await conn.close()
                raise commands.UserInputError()
        except Exception as error:
            await ctx.send(error)
            await conn.close()
            return

    @commands.command(usage='[template id]')
    @commands.guild_only()
    @RecruitmentCheck()
    async def register(self, ctx, templateid):
        author = ctx.author
        # connects to the database
        conn = await asyncpg.connect(self.connectionstr, database=self.database,
                                     password=self.password)
        try:
            # fetches data to ensure that the user doesn't exist
            exist = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', author.id)
            # if the user already exists
            if exist is not None:
                await ctx.send("You are already registered!")
                await conn.close()
                return
            # inserts data into database
            await conn.execute('''INSERT INTO recruitment(user_id, template) VALUES($1, $2);''', author.id, templateid)
            await ctx.send(f"Registered successfully with template ID: `{templateid}`.")
            await conn.close()
            return
        except Exception as error:
            await ctx.send(error)
            await conn.close()
            return

    @commands.command(usage='[template id]')
    @commands.guild_only()
    @RecruitmentCheck()
    async def edit_template(self, ctx, templateid):
        author = ctx.author
        # connects to database
        conn = await asyncpg.connect(self.connectionstr, database=self.database,
                                     password=self.password)
        try:
            # checks for user existance
            exist = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', author.id)
            # if the user does not exist
            if exist is None:
                await ctx.send("You are not registered!")
                await conn.close()
                return
            # updates the template
            await conn.execute('''UPDATE recruitment SET template = $2 WHERE user_id = $1;''', author.id, templateid)
            await ctx.send(f"Template ID for {author} set to `{templateid}` successfully.")
            await conn.close()
            return
        except Exception as error:
            await ctx.send(error)
            await conn.close()
            return

    @commands.command()
    @commands.guild_only()
    @RecruitmentCheck()
    async def view_template(self, ctx):
        author = ctx.author
        # connects to database
        conn = await asyncpg.connect(self.connectionstr, database=self.database,
                                     password=self.password)
        try:
            # fetches user data
            template = await conn.fetchrow('''SELECT template FROM recruitment WHERE user_id = $1;''', author.id)
            # if the user does not exist
            if template is None:
                await ctx.send("You are not registered!")
                await conn.close()
                return
            # sends relevant data, along with access link
            template = template['template']
            templateid = re.findall(r"\d+", template)
            templateid = list(map(int, templateid))
            await ctx.send(f"{author.name}'s template is {template}.\n"
                           f"The telegram template can be found here: "
                           f"https://www.nationstates.net/page=tg/tgid={templateid[0]}")
            await conn.close()
            return
        except Exception as error:
            await ctx.send(error)
            await conn.close()
            return

    async def monthly_recruiter(self):
        # connects to database
        conn = await asyncpg.connect(self.connectionstr, database=self.database,
                                     password=self.password)
        try:
            # fetches all user data
            top_recruiter = await conn.fetch('''SELECT * FROM recruitment ORDER BY sent_this_month;''')
            # finds the first entry and gathers user id, sent number, and sends the announcement message
            top_recruiter_user = top_recruiter[0]['user_id']
            top_recruiter_numbers = top_recruiter[0]['sent_this_month']
            announcements = bot.get_channel(835579413625569322)
            thegye = bot.get_guild(674259612580446230)
            recruiter_of_the_month_role = thegye.get_role(813953181234626582)
            user = bot.get_user(top_recruiter_user)
            announce = await announcements.send(
                f"**Congratulations to {user.mention}!**\n{user.display_name} has earned the "
                f"destinction of being this month's top recruiter! This month, they have sent "
                f"{top_recruiter_numbers} telegrams to new players. Wow! {user.display_name} has "
                f"been awarded the {recruiter_of_the_month_role.mention} role, customizable by "
                f"request. Everyone give them a round of applause!")
            await announce.add_reaction("\U0001f44f")
            # clears all sent_this_month
            await conn.execute('''UPDATE recruitment SET sent_this_month = 0;''')
            await conn.close()
            return
        except Exception as error:
            crashchannel = bot.get_channel(835579413625569322)
            await crashchannel.send(error)
            await conn.close()
            return

    async def monthly_recruiter_scheduler(self):
        # fetches channel object
        crashchannel = bot.get_channel(835579413625569322)
        try:
            # sets up asyncio scheduler
            monthlyscheduler = AsyncIOScheduler()
            # adds the job with cron designator
            monthlyscheduler.add_job(Recruitment.monthly_recruiter, CronTrigger.from_crontab('0 12 1 * *'),
                                     id="monthly recruiter")
            # starts the schedule, fetches the job information, and sends the confirmation that it has begun
            monthlyscheduler.start()
            monthlyjob = monthlyscheduler.get_job("monthly recruiter")
            await crashchannel.send(f"Monthly recruiter next run: {monthlyjob.next_run_time}")
        except Exception as error:
            await crashchannel.send(error)

    @commands.command()
    @commands.guild_only()
    async def campaign(self, ctx):
        version = 'WACU v.2.1'
        start = perf_counter()
        conn = await asyncpg.connect(self.connectionstr,
                                     database=self.database,
                                     password=self.password)
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
        await conn.close()


def setup(bot):
    async def monthly_recruiter_scheduler(bot):
        # fetches channel object
        crashchannel = bot.get_channel(835579413625569322)
        try:
            # sets up asyncio scheduler
            monthlyscheduler = AsyncIOScheduler()
            # adds the job with cron designator
            monthlyscheduler.add_job(Recruitment.monthly_recruiter, CronTrigger.from_crontab('0 12 1 * *'),
                                     id="monthly recruiter")
            # starts the schedule, fetches the job information, and sends the confirmation that it has begun
            monthlyscheduler.start()
            monthlyjob = monthlyscheduler.get_job("monthly recruiter")
            await crashchannel.send(f"Monthly recruiter next run: {monthlyjob.next_run_time}")
        except Exception as error:
            await crashchannel.send(error)
    loop = asyncio.get_running_loop()
    loop.run(monthly_recruiter_scheduler(bot=bot))
    bot.add_cog(Recruitment(bot))
