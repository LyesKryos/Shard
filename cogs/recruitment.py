# recruitment 1.03
from pytz import timezone

from ShardBot import Shard
from urllib.parse import quote
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands
import discord
import asyncio
from bs4 import BeautifulSoup
import re
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from time import perf_counter, strftime
from PIL import ImageColor
from customchecks import RecruitmentCheck


class Recruitment(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot

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

    do_not_recruit = list()
    sending_to = list()
    user_sent = 0
    running = False
    recruitment_gather_object = None
    directory = r"C:\Users\jaedo\PycharmProjects\Discord Bot\\"
    retention_loop = None
    monthly_loop = None

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
            await ctx.send("Recuitment stopped. Another link may post.")
        except Exception as error:
            self.running = False
            await ctx.send("The recruitment bot has run into an issue. Recruitment has stopped.")
            crashchannel = self.bot.get_channel(835579413625569322)
            await crashchannel.send(error)

    async def still_recruiting_check(self, ctx):
        while self.running:
            # connects to database
            conn = self.bot.pool
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
            except Exception as error:
                crashchannel = self.bot.get_channel(835579413625569322)
                await crashchannel.send(error)

        return

    @commands.command()
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

    @commands.command()
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
        # connects to database
        conn = self.bot.pool
        try:
            # fetches relevant user info
            userinfo = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', author.id)
            # updates relevant user info
            await conn.execute('''UPDATE recruitment SET sent = $1, sent_this_month = $2 WHERE user_id = $3;''',
                               (self.user_sent + userinfo['sent']), (self.user_sent + userinfo['sent_this_month']),
                               ctx.author.id)
            self.user_sent = 0

            self.recruitment_gather_object.cancel()
            return
        except Exception as error:
            await ctx.send(error)

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
        conn = self.bot.pool
        # if the call is for the author
        if args == ():
            try:
                # fetches relevant user data
                userinfo = await conn.fetchrow('''SELECT sent FROM recruitment WHERE user_id = $1;''', author.id)
                sent = userinfo['sent']
                # sends amount
                await ctx.send(f"{author} has sent {sent} telegrams.")

                return
            except Exception as error:
                await ctx.send(error)

                return
        elif ' '.join(args).lower() == "global":
            try:
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
            except Exception as error:
                await ctx.send(error)

                return
        elif args != ():
            try:
                # fetches the user object via the converter
                user = ' '.join(args[:])
                user = await commands.converter.MemberConverter().convert(ctx, user)
                # connects to the database
                conn = self.bot.pool  # fetches relevant user data and sends it
                userinfo = await conn.fetchrow('''SELECT sent FROM recruitment WHERE user_id = $1;''', user.id)
                sent = userinfo['sent']
                await ctx.send(f"{user} has sent {sent} telegrams.")

                return
            except Exception as error:
                await ctx.send(error)

                return

    @commands.command(usage="<monthly? (m)>")
    @commands.guild_only()
    @RecruitmentCheck()
    async def rank(self, ctx, monthly: str = None):
        # connects to the database
        conn = self.bot.pool
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
                    userstring = f"**{rank}.** {self.bot.get_user(ranks['user_id'])}: {ranks['sent']}\n"
                    ranksstr += userstring
                    rank += 1
                await ctx.send(f"{ranksstr}")

                return
            # if the user wants the sent monthly list
            elif monthly in ['m']:
                # fetches relevant user data, sorted by 'sent_this_month`
                userinfo = await conn.fetch('''SELECT * FROM recruitment ORDER BY sent_this_month DESC LIMIT 10;''')
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
        except Exception as error:
            await ctx.send(error)

            return

    @commands.command(usage='[template id]')
    @commands.guild_only()
    @RecruitmentCheck()
    async def register(self, ctx, templateid):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        try:
            # fetches data to ensure that the user doesn't exist
            exist = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', author.id)
            # if the user already exists
            if exist is not None:
                await ctx.send("You are already registered!")

                return
            # inserts data into database
            await conn.execute('''INSERT INTO recruitment(user_id, template) VALUES($1, $2);''', author.id, templateid)
            await ctx.send(f"Registered successfully with template ID: `{templateid}`.")

            return
        except Exception as error:
            await ctx.send(error)

            return

    @commands.command(usage='[template id]')
    @commands.guild_only()
    @RecruitmentCheck()
    async def edit_template(self, ctx, templateid):
        author = ctx.author
        # connects to database
        conn = self.bot.pool
        try:
            # checks for user existance
            exist = await conn.fetchrow('''SELECT * FROM recruitment WHERE user_id = $1;''', author.id)
            # if the user does not exist
            if exist is None:
                await ctx.send("You are not registered!")

                return
            # updates the template
            await conn.execute('''UPDATE recruitment SET template = $2 WHERE user_id = $1;''', author.id, templateid)
            await ctx.send(f"Template ID for {author} set to `{templateid}` successfully.")

            return
        except Exception as error:
            await ctx.send(error)

            return

    @commands.command()
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

    @commands.command()
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

    @commands.command(usage="[hex color code] [name]")
    async def customize_recruiter_role(self, ctx, color: str, *args):
        recruiter_of_the_month_role = discord.utils.get(ctx.guild.roles, id=813953181234626582)
        name = ' '.join(args)
        if recruiter_of_the_month_role not in ctx.author.roles:
            raise commands.MissingRole(recruiter_of_the_month_role)
        else:
            try:
                color = (x, y, z) = ImageColor.getrgb(color)
                rolecolor = discord.Color.from_rgb(*color)
                await recruiter_of_the_month_role.edit(color=rolecolor, name=f"{name} (Recruiter of the Month)")
                await ctx.send(f"Color changed to `{rolecolor}` and name changed to `{name}` successfully!")
            except Exception as error:
                if isinstance(error, ValueError):
                    await ctx.send("That doesn't appear to be a valid hex color code.")
                    return
                else:
                    await ctx.send(error)
                    return

    @commands.command()
    @RecruitmentCheck()
    async def retention(self, ctx):
        retention_role = discord.utils.get(ctx.guild.roles, id=950950836006187018)
        recruitment_channel = self.bot.get_channel(674342850296807454)
        if retention_role not in ctx.author.roles:
            await ctx.author.add_roles(retention_role)
            await recruitment_channel.send(f"**Welcome to the Order of Saint Julian, {ctx.author.mention}!**"
                                           f"\nYou can see our welcome telegram and exit telegram in the pins. "
                                           f"When a nation leaves or enters Thegye, you'll be notified via ping. If you"
                                           f" send a telegram to the nation, hit the \U0001f4ec emoji to let everyone"
                                           f" else know you've done so. Good luck!")
        elif retention_role in ctx.author.roles:
            await ctx.author.remove_roles(retention_role)
            await ctx.send("Role removed.")


def setup(bot):
    async def monthly_recruiter_scheduler(bot):
        # fetches channel object
        crashchannel = bot.get_channel(835579413625569322)
        try:
            # sets up asyncio scheduler
            monthlyscheduler = AsyncIOScheduler()
            eastern = timezone('US/Eastern')
            # adds the job with cron designator
            monthlyscheduler.add_job(monthly_recruiter,
                                     CronTrigger(hour=0, minute=0, day=1, timezone=eastern),
                                     args=(bot,),
                                     id="monthly recruiter")
            # starts the schedule, fetches the job information, and sends the confirmation that it has begun
            monthlyscheduler.start()
            monthlyjob = monthlyscheduler.get_job("monthly recruiter")
            await crashchannel.send(f"Monthly recruiter next run: {monthlyjob.next_run_time}")
        except Exception as error:
            await crashchannel.send(error)

    async def monthly_recruiter(bot: Shard):
        # connects to database
        conn = bot.pool
        try:
            # fetches all user data
            top_recruiter = await conn.fetch('''SELECT * FROM recruitment ORDER BY sent_this_month DESC;''')
            # finds the first entry and gathers user id, sent number, and sends the announcement message
            top_recruiter_user = top_recruiter[0]['user_id']
            top_recruiter_numbers = top_recruiter[0]['sent_this_month']
            announcements = bot.get_channel(674602527333023747)
            thegye = bot.get_guild(674259612580446230)
            recruiter_of_the_month_role = thegye.get_role(813953181234626582)
            for members in thegye.members:
                await members.remove_roles(recruiter_of_the_month_role)
            user = bot.get_user(top_recruiter_user)
            monthly_total = 0
            for s in top_recruiter:
                monthly_total += s['sent_this_month']
            await recruiter_of_the_month_role.edit(color=discord.Color.light_grey(), name="Recruiter of the Month")
            announce = await announcements.send(
                f"**Congratulations to {user.mention}!**\n{user.display_name} has earned the "
                f"distinction of being this month's top recruiter! This month, they have sent "
                f"{top_recruiter_numbers} telegrams to new players. Wow! {user.display_name} has "
                f"been awarded the {recruiter_of_the_month_role.mention} role, customizable by "
                f"request. Everyone give them a round of applause!\n In total, {monthly_total:,} telegrams have been "
                f"sent by our wonderful recruiters this month!")
            await announce.add_reaction("\U0001f44f")
            # clears all sent_this_month
            await conn.execute('''UPDATE recruitment SET sent_this_month = 0;''')
            return
        except Exception as error:
            crashchannel = bot.get_channel(835579413625569322)
            await crashchannel.send(error)
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
                            notif = await recruitment_channel.send(f"A nation has departed, {notifrole.mention}!"
                                                                   f"\nhttps://www.nationstates.net/nation={n}")
                            await notif.add_reaction("\U0001f4ec")
                    Recruitment.all_nations = set(recruitssoup.nations.text.split(':'))
                    await asyncio.sleep(300)
                    continue
        except Exception as error:
            await crashchannel.send(f"`{error}` in retention module.")
    loop = asyncio.get_event_loop()
    Recruitment.monthly_loop=loop.create_task(monthly_recruiter_scheduler(bot))
    Recruitment.retention_loop=loop.create_task(retention(bot))
    bot.add_cog(Recruitment(bot))
