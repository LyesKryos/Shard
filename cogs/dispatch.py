# dispatch cog v 1.4
from ShardBot import Shard
import asyncio
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import re
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone


class Dispatch(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot

        async def waupdate(bot):
            crashchannel = bot.get_channel(835579413625569322)
            try:
                password = self.bot.config['dispatch_pass']
                headers = {"User-Agent": "Bassiliya @Lies Kryos#1734 on Discord",
                           "X-Password": password,
                           "X-Pin": ""}
                # all API call parameters
                params = {"nation": "royal_clerk_of_thegye",
                          "c": "dispatch",
                          "dispatchid": 1577144,
                          "dispatch": "edit",
                          "title": "World Assembly Registry",
                          "text": 0,
                          "category": "8",
                          "subcategory": "845",
                          "mode": 0,
                          "token": 0}
                # region nation call parameters
                rparams = {"region": "thegye",
                           "q": "nations"}
                # world WA nation call parameters
                waparams = {"wa": "1",
                            "q": "members"}
                # get nations
                nations = requests.get("https://www.nationstates.net/cgi-bin/api.cgi", params=rparams, headers=headers)
                await asyncio.sleep(.6)
                nsoup = BeautifulSoup(nations.text, "lxml")
                nations = nsoup.nations.text.split(":")
                nationsset = set(nations)
                # get wa members
                wa_memb = requests.get("https://www.nationstates.net/cgi-bin/api.cgi", params=waparams, headers=headers)
                await asyncio.sleep(.6)
                wasoup = BeautifulSoup(wa_memb.text, "lxml")
                members = wasoup.members.text.split(",")
                membersset = set(members)
                # intersect nations and members
                allwanations = nationsset.intersection(membersset)
                # sort alphabetically
                alpha = sorted(list(allwanations))
                # create the column entry and nation tag for all nations in the set
                sortednames = [f"[td][nation]{x}[/nation][/td]" for x in alpha]
                table = "[anchor=top][/anchor]\n[url=/region=thegye][img]https://i.ibb.co/6PgWm5y/Thegye-Banner.png[/img][" \
                        "/url][background-block=black]-\n[center][url=/page=dispatch/id=1310527][size=150][color=#FFCC00]| " \
                        "Getting Started[/url][/color][/size] [url=page=dispatch/id=1309596][size=150][color=#FFCC00]| [" \
                        "b]Government[/b][/url][/size][/color]  [url=/page=dispatch/id=1310572][size=150][color=#FFCC00]| " \
                        "Map[/url][/size][/color]  [url=/page=dispatch/id=1370630][size=150][color=#FFCC00]| Roleplay |[" \
                        "/url][/size][/color][/center]-[/background-block]\n" \
                        "\n" \
                        "[center]This page contains a table of all World Assembly nations residing in [region]Thegye" \
                        "[/region]. Please note that this dispatch is automatically updated once daily at 0200 EST." \
                        "[/center]\n[box][center][b][size=120]World Assembly Registry[/size][/b][/center][hr][table=plain]" \
                        "[tr][td]1.[/td] "
                row = 1
                # for every item in the sortednames list, add them to the string.
                for index, item in enumerate(sortednames):
                    table += item
                    # every five entries, end the row, start a new one, and up the row number
                    if index % 5 == 4:
                        table += f"[/tr][tr][td]{row + 1}.[/td] "
                        row += 1
                # add the ending to the table
                table += "[/tr][/table][/box][hr][i][size=80]Original content created by [nation=noflag]Bassiliya[/nation]. " \
                         "Do not reproduce, in whole or part, without express permission. Content updated automatically.[/i][" \
                         "/size] "
                params["text"] = table
                params["mode"] = "prepare"
                # prepare dispatch command
                dresponse = requests.post("https://www.nationstates.net/cgi-bin/api.cgi", headers=headers, data=params)
                await asyncio.sleep(.6)
                if dresponse.status_code == 409:
                    return
                dresponse_headers = dresponse.headers
                soup = BeautifulSoup(dresponse.text, "lxml")
                token = soup.success.string
                # grab the token and execute dispatch command
                params["token"] = token
                params["mode"] = "execute"
                headers["X-Pin"] = dresponse_headers["X-Pin"]
                Dispatch.xpin = dresponse_headers["X-Pin"]
                await asyncio.sleep(.6)
                execute_update = requests.post("https://www.nationstates.net/cgi-bin/api.cgi", headers=headers,
                                               data=params)
                await asyncio.sleep(.6)
                await crashchannel.send(f"{execute_update} for Thegye execute")
                channel = bot.get_channel(674285035905613825)
                await channel.send(
                    "WA Registry successfully updated!\nhttps://www.nationstates.net/page=dispatch/id=1577144")
            except Exception as error:
                await crashchannel.send(f"{error} in Thegye update")

        # async def kaupdate(bot):
        #     crashchannel = bot.get_channel(835579413625569322)
        #     try:
        #         headers = {"User-Agent": "Bassiliya @Lies Kryos#1734 on Discord",
        #                    "X-pin": Dispatch.xpin}
        #         # all API call parameters
        #         params = {"nation": "royal_clerk_of_thegye",
        #                   "c": "dispatch",
        #                   "dispatchid": 1577735,
        #                   "dispatch": "edit",
        #                   "title": "World Assembly Registry [Karma]",
        #                   "text": 0,
        #                   "category": "8",
        #                   "subcategory": "845",
        #                   "mode": 0,
        #                   "token": 0}
        #         # region nation call parameters
        #         rparams = {"region": "karma",
        #                    "q": "nations"}
        #         # world WA nation call parameters
        #         waparams = {"wa": "1",
        #                     "q": "members"}
        #         # get nations
        #         nations = requests.get("https://www.nationstates.net/cgi-bin/api.cgi", params=rparams, headers=headers)
        #         await asyncio.sleep(.6)
        #         nsoup = BeautifulSoup(nations.text, "lxml")
        #         nations = nsoup.nations.text.split(":")
        #         nationsset = set(nations)
        #         # get wa members
        #         wa_memb = requests.get("https://www.nationstates.net/cgi-bin/api.cgi", params=waparams, headers=headers)
        #         await asyncio.sleep(.6)
        #         wasoup = BeautifulSoup(wa_memb.text, "lxml")
        #         members = wasoup.members.text.split(",")
        #         membersset = set(members)
        #         # intersect nations and members
        #         allwanations = nationsset.intersection(membersset)
        #         # sort alphabetically
        #         alpha = sorted(list(allwanations))
        #         # create the column entry and nation tag for all nations in the set
        #         sortednames = [f"[td][nation]{x}[/nation][/td]" for x in alpha]
        #         table = "[center][img]https://i.imgur.com/jTBxqib.png[/img][hr][Size=200]World Assembly Registry[/center][" \
        #                 "/size][hr][box][table=plain][tr][td]1.[/td] "
        #         row = 1
        #         # for every item in the sortednames list, add them to the string.
        #         for index, item in enumerate(sortednames):
        #             table += item
        #             # every five entries, end the row, start a new one, and up the row number
        #             if index % 5 == 4:
        #                 table += f"[/tr][tr][td]{row + 1}.[/td] "
        #                 row += 1
        #         # add the ending to the table
        #         table += "[/tr][/table][/box][center][url=https://www.nationstates.net/page=dispatch/id=1391473][" \
        #                  "img]https://i.ibb.co/ZG7CMmR/Return-to-Hub.png[/img][/url][/center][hr][i][size=80]Original content " \
        #                  "by [nation=noflag]Bassiliya[/nation]. Made by request for [nation=noflag]Altino[/nation]. Do not " \
        #                  "reproduce, in whole or part, without express permission. Content automatically updated daily at " \
        #                  "0200 EST.[/i][/size] "
        #         params["text"] = table
        #         params["mode"] = "prepare"
        #         # prepare dispatch command
        #         dresponse = requests.post("https://www.nationstates.net/cgi-bin/api.cgi", headers=headers, data=params)
        #         await asyncio.sleep(.6)
        #         if dresponse.status_code == 409:
        #             return
        #         soup = BeautifulSoup(dresponse.text, "lxml")
        #         token = soup.success.string
        #         # grab the token and execute dispatch command
        #         params["token"] = token
        #         params["mode"] = "execute"
        #         await asyncio.sleep(.6)
        #         execute_update = requests.post("https://www.nationstates.net/cgi-bin/api.cgi", headers=headers,
        #                                        data=params)
        #         await asyncio.sleep(.6)
        #         await crashchannel.send(f"{execute_update} for Karma execute")
        #         channel = bot.get_channel(319961144091738112)
        #         await channel.send(
        #             "World Assembly Registry updated successfully!\nhttps://www.nationstates.net/page=dispatch/id"
        #             "=1577735")
        #     except Exception as error:
        #         await crashchannel.send(f"{error} in Karma update")

        async def daily_update(bot):
            await bot.wait_until_ready()
            crashchannel = bot.get_channel(835579413625569322)
            try:
                # define cron scheduler and timezone to run every day
                self.dispatch_updating_object = AsyncIOScheduler(timezone='US/Eastern')
                eastern = timezone("US/Eastern")
                self.dispatch_updating_object.add_job(waupdate, args=(bot,),
                                                   trigger=CronTrigger.from_crontab('5 2 * * *', timezone=eastern),
                                                   id="thegye_update",
                                                   max_instances=1)
                # self.dispatch_updating_object.add_job(kaupdate, args=(bot,),
                #                                    trigger=CronTrigger.from_crontab('20 2 * * *', timezone=eastern),
                #                                    id="karma_update",
                #                                    max_instances=1)
                # start the updating
                self.dispatch_updating_object.start()
                thegyeupdate = self.dispatch_updating_object.get_job("thegye_update")
                # post the next update time for each of the runs and set the updating to true
                self.bot.system_message += "From dispatch.py: \n"\
                                            f"Thegye update: {thegyeupdate.next_run_time}\n"
                Dispatch.dispatch_updating = True
            except Exception as error:
                await crashchannel.send(error)
        loop = bot.loop
        loop.create_task(daily_update(self.bot))

    def cog_unload(self):
        self.dispatch_updating_object.shutdown(wait=False)

    # defined variables
    dispatch_updating_object = None
    dispatch_updating = False
    xpin = 0

    def sanitize_raw(self, userinput: str) -> str:
        # replaces user input with proper, url-friendly code
        to_regex = userinput.replace("_", " ")
        return re.sub(r"[^a-zA-Z0-9_-]", ' ', to_regex)

    @commands.command()
    @commands.is_owner()
    async def dstatus(self, ctx):
        # if dispatch updating is running
        if self.dispatch_updating_object.running:
            await ctx.send("Dispatch updating is running.")
        else:
            await ctx.send("Dispatch updating is not running.")

    async def waupdate(self, bot):
        crashchannel = bot.get_channel(835579413625569322)
        headers = {"User-Agent": "Bassiliya @Lies Kryos#1734 on Discord",
                   "X-Password": "Kingsfoil4",
                   "X-Pin": ""}
        # all API call parameters
        params = {"nation": "royal_clerk_of_thegye",
                  "c": "dispatch",
                  "dispatchid": 1577144,
                  "dispatch": "edit",
                  "title": "World Assembly Registry",
                  "text": 0,
                  "category": "8",
                  "subcategory": "845",
                  "mode": 0,
                  "token": 0}
        # region nation call parameters
        rparams = {"region": "thegye",
                   "q": "nations"}
        # world WA nation call parameters
        waparams = {"wa": "1",
                    "q": "members"}
        # get nations
        nations = requests.get("https://www.nationstates.net/cgi-bin/api.cgi", params=rparams, headers=headers)
        await asyncio.sleep(.6)
        nsoup = BeautifulSoup(nations.text, "lxml")
        nations = nsoup.nations.text.split(":")
        nationsset = set(nations)
        # get wa members
        wa_memb = requests.get("https://www.nationstates.net/cgi-bin/api.cgi", params=waparams, headers=headers)
        await asyncio.sleep(.6)
        wasoup = BeautifulSoup(wa_memb.text, "lxml")
        members = wasoup.members.text.split(",")
        membersset = set(members)
        # intersect nations and members
        allwanations = nationsset.intersection(membersset)
        # sort alphabetically
        alpha = sorted(list(allwanations))
        # create the column entry and nation tag for all nations in the set
        sortednames = [f"[td][nation]{x}[/nation][/td]" for x in alpha]
        table = "[anchor=top][/anchor]\n[url=/region=thegye][img]https://i.ibb.co/6PgWm5y/Thegye-Banner.png[/img][" \
                "/url][background-block=black]-\n[center][url=/page=dispatch/id=1310527][size=150][color=#FFCC00]| " \
                "Getting Started[/url][/color][/size] [url=page=dispatch/id=1309596][size=150][color=#FFCC00]| [" \
                "b]Government[/b][/url][/size][/color]  [url=/page=dispatch/id=1310572][size=150][color=#FFCC00]| " \
                "Map[/url][/size][/color]  [url=/page=dispatch/id=1370630][size=150][color=#FFCC00]| Roleplay |[" \
                "/url][/size][/color][/center]-[/background-block]\n" \
                "\n" \
                "[center]This page contains a table of all World Assembly nations residing in [region]Thegye" \
                "[/region]. Please note that this dispatch is automatically updated once daily at 0200 EST." \
                "[/center]\n[box][center][b][size=120]World Assembly Registry[/size][/b][/center][hr][table=plain]" \
                "[tr][td]1.[/td] "
        row = 1
        # for every item in the sortednames list, add them to the string.
        for index, item in enumerate(sortednames):
            table += item
            # every five entries, end the row, start a new one, and up the row number
            if index % 5 == 4:
                table += f"[/tr][tr][td]{row + 1}.[/td] "
                row += 1
        # add the ending to the table
        table += "[/tr][/table][/box][hr][i][size=80]Original content created by [nation=noflag]Bassiliya[/nation]. " \
                 "Do not reproduce, in whole or part, without express permission. Content updated automatically.[/i][" \
                 "/size] "
        params["text"] = table
        params["mode"] = "prepare"
        # prepare dispatch command
        dresponse = requests.post("https://www.nationstates.net/cgi-bin/api.cgi", headers=headers, data=params)
        await asyncio.sleep(.6)
        await crashchannel.send(f"{dresponse} for Thegye prepatory")
        if dresponse.status_code == 409:
            raise Exception("409 response code")
        dresponse_headers = dresponse.headers
        soup = BeautifulSoup(dresponse.text, "lxml")
        token = soup.success.string
        # grab the token and execute dispatch command
        params["token"] = token
        params["mode"] = "execute"
        headers["X-Pin"] = dresponse_headers["X-Pin"]
        Dispatch.xpin = dresponse_headers["X-Pin"]
        execute_update = requests.post("https://www.nationstates.net/cgi-bin/api.cgi", headers=headers, data=params)
        await asyncio.sleep(.6)
        await crashchannel.send(f"{execute_update} for Thegye execute")
        channel = bot.get_channel(674285035905613825)
        await channel.send(
            "WA Registry successfully updated!\nhttps://www.nationstates.net/page=dispatch/id=1577144")

    # async def kaupdate(self, bot):
    #     crashchannel = bot.get_channel(835579413625569322)
    #     headers = {"User-Agent": "Bassiliya @Lies Kryos#1734 on Discord",
    #                "X-pin": Dispatch.xpin}
    #     # all API call parameters
    #     params = {"nation": "royal_clerk_of_thegye",
    #               "c": "dispatch",
    #               "dispatchid": 1577735,
    #               "dispatch": "edit",
    #               "title": "World Assembly Registry [Karma]",
    #               "text": 0,
    #               "category": "8",
    #               "subcategory": "845",
    #               "mode": 0,
    #               "token": 0}
    #     # region nation call parameters
    #     rparams = {"region": "karma",
    #                "q": "nations"}
    #     # world WA nation call parameters
    #     waparams = {"wa": "1",
    #                 "q": "members"}
    #     # get nations
    #     nations = requests.get("https://www.nationstates.net/cgi-bin/api.cgi", params=rparams, headers=headers)
    #     await asyncio.sleep(.6)
    #     nsoup = BeautifulSoup(nations.text, "lxml")
    #     nations = nsoup.nations.text.split(":")
    #     nationsset = set(nations)
    #     # get wa members
    #     wa_memb = requests.get("https://www.nationstates.net/cgi-bin/api.cgi", params=waparams, headers=headers)
    #     await asyncio.sleep(.6)
    #     wasoup = BeautifulSoup(wa_memb.text, "lxml")
    #     members = wasoup.members.text.split(",")
    #     membersset = set(members)
    #     # intersect nations and members
    #     allwanations = nationsset.intersection(membersset)
    #     # sort alphabetically
    #     alpha = sorted(list(allwanations))
    #     # create the column entry and nation tag for all nations in the set
    #     sortednames = [f"[td][nation]{x}[/nation][/td]" for x in alpha]
    #     table = "[center][img]https://i.imgur.com/jTBxqib.png[/img][hr][Size=200]World Assembly Registry[/center][" \
    #             "/size][hr][box][table=plain][tr][td]1.[/td] "
    #     row = 1
    #     # for every item in the sortednames list, add them to the string.
    #     for index, item in enumerate(sortednames):
    #         table += item
    #         # every five entries, end the row, start a new one, and up the row number
    #         if index % 5 == 4:
    #             table += f"[/tr][tr][td]{row + 1}.[/td] "
    #             row += 1
    #     # add the ending to the table
    #     table += "[/tr][/table][/box][center][url=https://www.nationstates.net/page=dispatch/id=1391473][" \
    #              "img]https://i.ibb.co/ZG7CMmR/Return-to-Hub.png[/img][/url][/center][hr][i][size=80]Original content " \
    #              "by [nation=noflag]Bassiliya[/nation]. Made by request for [nation=noflag]Altino[/nation]. Do not " \
    #              "reproduce, in whole or part, without express permission. Content automatically updated daily at " \
    #              "0200 EST.[/i][/size] "
    #     params["text"] = table
    #     params["mode"] = "prepare"
    #     # prepare dispatch command
    #     dresponse = requests.post("https://www.nationstates.net/cgi-bin/api.cgi", headers=headers, data=params)
    #     await asyncio.sleep(.6)
    #     if dresponse.status_code == 409:
    #         return
    #     soup = BeautifulSoup(dresponse.text, "lxml")
    #     token = soup.success.string
    #     # grab the token and execute dispatch command
    #     params["token"] = token
    #     params["mode"] = "execute"
    #     execute_update = requests.post("https://www.nationstates.net/cgi-bin/api.cgi", headers=headers, data=params)
    #     await asyncio.sleep(.6)
    #     await crashchannel.send(f"{execute_update} for Karma execute")
    #     channel = bot.get_channel(319961144091738112)
    #     await channel.send(
    #         "World Assembly Registry updated successfully!\nhttps://www.nationstates.net/page=dispatch/id"
    #         "=1577735")
    #     await crashchannel.send(f"{dresponse} for Karma update")

    @commands.command()
    @commands.is_owner()
    async def update_dispatches(self, ctx):
        # manually update all dispatches
        await self.waupdate(self.bot)
        # await self.kaupdate(self.bot)
        await ctx.send("All done!")


async def setup(bot):
    await bot.add_cog(Dispatch(bot))
