# cnc v1.0

from ShardBot import Shard
import discord
from discord.ext import commands, tasks
import asyncio
from random import randint, uniform, choice, randrange, sample
from battlesim import calculations
import math
import datetime
from PIL import Image, ImageColor, ImageDraw
from base64 import b64encode
import requests
from time import sleep, localtime, time, strftime, perf_counter
import os
from customchecks import modcheck, SilentFail, WrongInput
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
import traceback


class CNC(commands.Cog):

    def __init__(self, bot: Shard):
        self.map_directory = r"/root/Documents/Shard/CNC/Map Files"
        self.interaction_directory = r"/root/Documents/Shard/CNC/Interaction Files/"
        self.bot = bot

    def cog_unload(self):
        # stop the running turnloop
        self.turn_loop.cancel()
        # cancel the running turn task
        self.turn_task.cancel()

    turn_task = None
    banned_colors = ["#000000", "#ffffff", "#808080", "#0071BC", "#0084E2", "#2BA5E2"]

    async def cog_check(self, ctx):
        if ctx.author.id in [293518673417732098]:
            return True
        else:
            if ctx.guild is None:
                aroles = list()
                thegye = ctx.bot.get_guild(674259612580446230)
                member = thegye.get_member(ctx.author.id)
                for ar in member.roles:
                    aroles.append(ar.id)
                if 674260547897917460 not in aroles:
                    raise SilentFail
            elif ctx.guild is not None:
                aroles = list()
                if ctx.guild.id == 674259612580446230:
                    for ar in ctx.author.roles:
                        aroles.append(ar.id)
                    if 674260547897917460 not in aroles:
                        raise SilentFail
            conn = self.bot.pool
            blacklist = await conn.fetchrow('''SELECT * FROM blacklist WHERE user_id = $1 AND active = True;''',
                                            ctx.author.id)
            if blacklist is not None:
                if blacklist['end_time'] is None:
                    if blacklist['status'] == "mute":
                        raise SilentFail
                    if blacklist['status'] == "ban":
                        raise SilentFail
                if blacklist['end_time'] < datetime.datetime.now():
                    await conn.execute(
                        '''UPDATE blacklist SET active = False WHERE user_id = $1 AND end_time = $2;''',
                        ctx.author.id, blacklist['end_time'])
            else:
                return True

    def map_color(self, province, province_cord, hexcode, release: bool = False):
        province_cord = ((int(province_cord[0])), (int(province_cord[1])))
        try:
            color = ImageColor.getrgb(hexcode)
        except ValueError:
            return ValueError("Hex code issue")
        map = Image.open(fr"{self.map_directory}/Maps/wargame_provinces.png").convert("RGBA")
        prov = Image.open(fr"{self.map_directory}/Province Layers/{province}.png").convert("RGBA")
        width = prov.size[0]
        height = prov.size[1]
        cord = (province_cord[0], province_cord[1])
        for x in range(0, width):
            for y in range(0, height):
                data = prov.getpixel((x, y))
                if data != color:
                    if data != (0, 0, 0, 0):
                        prov.putpixel((x, y), color)
        if release is True:
            color = ImageColor.getrgb("#808080")
            for x in range(0, prov.size[0]):
                for y in range(0, prov.size[1]):
                    data = prov.getpixel((x, y))
                    if data != color:
                        if data != (0, 0, 0, 0):
                            prov.putpixel((x, y), color)
        prov = prov.convert("RGBA")
        map.paste(prov, box=cord, mask=prov)
        map.save(fr"{self.map_directory}/Maps/wargame_provinces.png")

    def occupy_color(self, province, province_cord, occupy_color, owner_color):
        province_cord = ((int(province_cord[0])), (int(province_cord[1])))
        try:
            occupyer = ImageColor.getrgb(occupy_color)
            owner = ImageColor.getrgb(owner_color)
        except ValueError:
            return ValueError("Hex code issue")
        map = Image.open(fr"{self.map_directory}/Maps/wargame_provinces.png").convert("RGBA")
        prov = Image.open(fr"{self.map_directory}/Province Layers/{province}.png").convert("RGBA")
        prov_draw = ImageDraw.Draw(prov)
        width = prov.size[0]
        height = prov.size[1]
        cord = (province_cord[0], province_cord[1])
        space = 20
        not_colored = list()
        for x in range(0, width):
            for y in range(0, height):
                pixel = prov.getpixel((x, y))
                if pixel == (0, 0, 0, 0):
                    not_colored.append((x, y))
                else:
                    prov.putpixel((x, y), owner)
        for x in range(0, 2 * width, space):
            prov_draw.line([x, 0, x - width, height], width=5, fill=occupyer)
        for pix in not_colored:
            prov.putpixel(pix, (0, 0, 0, 0))
        map.paste(prov, box=cord, mask=prov)
        map.save(fr"{self.map_directory}/Maps/wargame_provinces.png")

    def add_ids(self):
        bmap = Image.open(fr"{self.map_directory}/Maps/wargame_provinces.png").convert("RGBA")
        ids = Image.open(fr"{self.map_directory}/Maps/wargame numbers.png").convert("RGBA")
        bmap.paste(ids, box=(0, 0), mask=ids)
        bmap.save(fr"{self.map_directory}/Maps/wargame_nations_map.png")

    # ---------------------User Commands------------------------------

    @commands.command(brief="Displays information about the CNC system.")
    @commands.guild_only()
    async def cnc_info(self, ctx):
        conn = self.bot.pool
        data = await conn.fetchrow('''SELECT data_value FROM cnc_data WHERE data_name = $1;''', "turns")
        infoembed = discord.Embed(title="Command And Conquest System", color=discord.Color.dark_red(),
                                  description="This is the condensed information about the CNC system. "
                                              "For more information, including commands, see the CNC Dispatch here:"
                                              " https://www.nationstates.net/page=dispatch/id=1641083")
        infoembed.add_field(name="About",
                            value="The Command and Conquest system is a simulated battle royale between "
                                  "the various nations of Thegye. It is non-roleplay and is meant to be "
                                  "an entertaining strategy game. The system makes used of combat "
                                  "between armies, international relationships and intrigue, "
                                  "resources, and more to bring players a fun and immersive experience. "
                                  "The system is hosted on Shard, a purpose-built bot. For more "
                                  "information about the Command and Conquer system, make sure to check "
                                  "out the dispatch and use the command "
                                  f" `{self.bot.command_prefix}help CNC`.", inline=False)
        infoembed.add_field(name="Turns", value=f"It is currently turn {data['data_value']}.")
        infoembed.add_field(name="Questions?",
                            value="Contact the creator: Lies Kryos#1734\n"
                                  "Contact a moderator: Lies Kryos#1734, [Insert_Person_Here]#6003")
        infoembed.set_thumbnail(url="https://i.ibb.co/gTpHmgq/Command-Conquest-symbol.png")
        await ctx.send(embed=infoembed)

    @commands.command(brief="Displays the turn count.")
    @commands.guild_only()
    async def cnc_turn(self, ctx):
        # sets up asyncio scheduler
        turnscheduler = AsyncIOScheduler()
        eastern = timezone('US/Eastern')
        # adds the job with cron designator
        turnscheduler.add_job(print,
                              CronTrigger.from_crontab("0 */6 * * *", timezone=eastern),
                              args=("",),
                              id="turn")
        # starts the schedule, fetches the job information, and sends the confirmation that it has begun
        turnscheduler.start()
        turnjob = turnscheduler.get_job("turn")
        conn = self.bot.pool
        data = await conn.fetchrow('''SELECT data_value FROM cnc_data WHERE data_name = $1;''', "turns")
        await ctx.send(f"It is currently turn #{data['data_value']}. "
                       f"Next turn is <t:{math.floor(turnjob.next_run_time.timestamp())}:R>")

    @commands.command(usage="[nation name] #[hexadecimal color id] <focus (m,e,s)>", brief="Registers a new nation")
    @commands.guild_only()
    async def cnc_register(self, ctx, nationame: str, color: str, focus: str = None):
        userid = ctx.author.id
        # connects to the database
        conn = self.bot.pool
        # checks to see if the user is registered
        registered = await conn.fetch('''SELECT * FROM cncusers;''')
        for u in registered:
            # if the user is already registered
            if userid == u["user_id"]:
                await ctx.send(
                    f"{ctx.author.name} is already registered! Use `$cnc_view` to view your registered nation.")
                return
            elif nationame.lower() == u['username'].lower():
                await ctx.send(
                    f"{nationame} is an already registered nation name! Please choose a different username.")
                return
        # checks the focus and ensures proper reading
        focuses = ['m', 'e', 's']
        if focus is not None:
            if focus.lower() not in focuses:
                raise Exception("That is not a valid focus. Please use only m, e, or s.")
        else:
            focus = "None"
        if color in self.banned_colors:
            await ctx.send("That color is a reserved color. Please pick another color.")
            return
        colors = [u['usercolor'] for u in registered]
        if color in colors:
            await ctx.send("That color is already taken by another user. Please pick another color.")
            return
        try:
            ImageColor.getrgb(color)
        except ValueError:
            await ctx.send("That doesn't appear to be a valid hex color code.")
            return
        # inserts the users id into the databases
        await conn.execute(
            '''INSERT INTO cncusers (user_id, username, usercolor, provinces_owned, resources, 
            focus, undeployed, moves) VALUES ($1, $2, $3, $4, $5, $6, $7, $8);''',
            userid, nationame, color, [0], randint(9000, 10000), focus.lower(), 0, 5)
        allnations = await conn.fetch('''SELECT username FROM cncusers;''')
        allnations = [n['username'] for n in allnations]
        for n in allnations:
            if n == nationame:
                continue
            await conn.execute('''INSERT INTO relations(name, nation) VALUES($1, $2);''', nationame, n)
            await conn.execute('''INSERT INTO relations(name, nation) VALUES($1, $2);''', n, nationame)
        file = open(f"{self.interaction_directory}{userid}.txt", "w")
        file.close()
        await ctx.send(f"{ctx.author.name} has registered {nationame} in the Command and Conquer System!")

    @commands.command(usage="<nation name or Discord username>", aliases=['cncv'],
                      brief="Displays information about a nation")
    async def cnc_view(self, ctx, *, args=None):
        # connects to the database
        conn = self.bot.pool
        nationname = args
        if nationname is None:
            # if the nationame is left blank, the author id is used to find the nation information
            author = ctx.author
            registeredusers = await conn.fetch('''SELECT user_id FROM cncusers;''')
            registeredlist = list()
            # makes a list of the registered users
            for users in registeredusers:
                registeredlist.append(users["user_id"])
            # checks the author id against the list of registered users
            if author.id not in registeredlist:
                await ctx.send(f"{ctx.author} does not appear to be registered.")
                return
            # grabs the nation information
            userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
            # sets the color properly
            if userinfo["usercolor"] == "":
                color = discord.Color.random()
                colorvalue = "No color set."
            else:
                color = discord.Color(int(userinfo["usercolor"].lstrip('#'), 16))
                colorvalue = color
            # grabs all provinces owned by the nation and makes them into a pretty list
            if len(userinfo["provinces_owned"]) != 1:
                provinceslist = userinfo["provinces_owned"]
                if 0 in provinceslist:
                    provinceslist.remove(0)
                provinceslist.sort()
                provinces = ', '.join(str(i) for i in provinceslist)
                total_troops = 0
                total_troops_raw = await conn.fetchrow('''SELECT sum(troops::int) FROM provinces 
                WHERE occupier_id = $1;''', author.id)
                total_troops += total_troops_raw['sum']
                total_troops += userinfo['undeployed']
            else:
                provinceslist = []
                provinces = "None"
                total_troops = userinfo['undeployed']
            # sets focus
            if userinfo['focus'] == "m":
                focus = "Military"
            elif userinfo['focus'] == "e":
                focus = "Economy"
            elif userinfo['focus'] == "s":
                focus = "Strategy"
            else:
                focus = "None"
            # fetches relations information
            relations = await conn.fetch('''SELECT nation, relation FROM relations WHERE name = $1;''',
                                         userinfo['username'])
            alliances = list()
            wars = list()
            for r in relations:
                if r['relation'] == 'war':
                    wars.append(r)
                if r['relation'] == 'alliance':
                    alliances.append(r)
            if len(wars) != 0:
                wars.sort()
                wars = ', '.join(str(w['nation']) for w in wars)
            else:
                wars = "None"
            if len(alliances) != 0:
                alliances.sort()
                alliances = ', '.join(str(a['nation']) for a in alliances)
            else:
                alliances = "None"
            if userinfo['capital'] == 0:
                capital = "None"
            else:
                capital = f"Province #{userinfo['capital']}"
            # creates the embed item
            cncuserembed = discord.Embed(title=userinfo["username"], color=color,
                                         description=f"Registered nation of {self.bot.get_user(userinfo['user_id']).name}.")
            cncuserembed.add_field(name=f"Territory (Total: {len(provinceslist)})", value=provinces, inline=False)
            cncuserembed.add_field(name="Total Troops", value=f"{total_troops:,}")
            cncuserembed.add_field(name="Undeployed Troops", value=f"{userinfo['undeployed']:,}")
            cncuserembed.add_field(name="Resources", value=f"\u03FE{userinfo['resources']:,}")
            cncuserembed.add_field(name="National Focus", value=focus)
            cncuserembed.add_field(name="Color", value=colorvalue)
            cncuserembed.add_field(name="Action Points", value=userinfo['moves'])
            cncuserembed.add_field(name="Capital", value=capital)
            cncuserembed.add_field(name="Alliances", value=alliances)
            cncuserembed.add_field(name="Wars", value=wars)
            await ctx.send(embed=cncuserembed)
        else:
            registeredusers = await conn.fetch('''SELECT username, user_id FROM cncusers;''')
            registeredlist = list()
            id_list = list()
            snowflake = False
            try:
                user = await commands.converter.MemberConverter().convert(ctx, nationname)
                snowflake = True
            except commands.BadArgument:
                pass
            # makes a list of the registered users
            for users in registeredusers:
                registeredlist.append(users["username"].lower())
                id_list.append(users['user_id'])
            # checks for user snowflake and the list of registered users
            if snowflake is False:
                if nationname.lower() not in registeredlist:
                    await ctx.send(f"{nationname} does not appear to be registered.")
                    return
                else:
                    nation = await conn.fetchrow('''SELECT * FROM cncusers WHERE lower(username) = $1;''',
                                                 nationname.lower())
            else:
                if user.id not in id_list:
                    await ctx.send(f"{user.display_name} does not appear to be registered.")
                    return
                else:
                    nation = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''',
                                                 user.id)
            # sets the color properly
            if nation["usercolor"] == "":
                color = discord.Color.random()
                colorvalue = "No color set."
            else:
                color = discord.Color(int(nation["usercolor"].lstrip('#'), 16))
                colorvalue = color
            total_troops = 0
            # grabs all provinces  owned by the nation and makes them into a pretty list
            if len(nation["provinces_owned"]) != 1:
                provinceslist = nation["provinces_owned"]
                if 0 in provinceslist:
                    provinceslist.remove(0)
                provinceslist.sort()
                provinces = ', '.join(str(p) for p in provinceslist)
                p_total_troops = await conn.fetchrow(
                    '''SELECT SUM(troops::int) FROM provinces WHERE occupier_id = $1;''',
                    nation['user_id'])
                total_troops += p_total_troops['sum']
            else:
                provinceslist = []
                provinces = "None"
            total_troops += nation['undeployed']
            # sets focus
            if nation['focus'] == "m":
                focus = "Military"
            elif nation['focus'] == "e":
                focus = "Economy"
            elif nation['focus'] == "s":
                focus = "Strategy"
            elif nation['focus'] == "none":
                focus = "None"
            # fetches relations information
            relations = await conn.fetch('''SELECT nation, relation FROM relations WHERE name = $1;''',
                                         nation['username'])
            alliances = list()
            wars = list()
            for r in relations:
                if r['relation'] == 'war':
                    wars.append(r)
                if r['relation'] == 'alliance':
                    alliances.append(r)
            if len(wars) != 0:
                wars.sort()
                wars = ', '.join(str(w['nation']) for w in wars)
            else:
                wars = "None"

            if len(alliances) != 0:
                alliances.sort()
                alliances = ', '.join(str(a['nation']) for a in alliances)
            else:
                alliances = "None"
            if nation['capital'] == 0:
                capital = "None"
            else:
                capital = f"Province #{nation['capital']}"
            # creates the embed item
            cncuserembed = discord.Embed(title=nation["username"], color=color,
                                         description=f"Registered nation of {self.bot.get_user(nation['user_id']).name}.")
            cncuserembed.add_field(name=f"Territory (Total: {len(provinceslist)})", value=provinces, inline=False)
            cncuserembed.add_field(name="Total Troops", value=f"{total_troops:,}")
            cncuserembed.add_field(name="Undeployed Troops", value=f"{nation['undeployed']:,}")
            cncuserembed.add_field(name="Resources", value=f"\u03FE{nation['resources']}")
            cncuserembed.add_field(name="National Focus", value=focus)
            cncuserembed.add_field(name="Color", value=colorvalue)
            cncuserembed.add_field(name="Action Points", value=nation['moves'])
            cncuserembed.add_field(name="Capital", value=capital)
            cncuserembed.add_field(name="Alliances", value=alliances)
            cncuserembed.add_field(name="Wars", value=wars)
            await ctx.send(embed=cncuserembed)

    @commands.command(aliases=['cncdv'], brief="Displays detailed information about a nation, privately")
    async def cnc_detailed_view(self, ctx):
        # connects to the database
        conn = self.bot.pool
        author = ctx.author
        registeredusers = await conn.fetch('''SELECT user_id FROM cncusers;''')
        registeredlist = list()
        # makes a list of the registered users
        for users in registeredusers:
            registeredlist.append(users["user_id"])
        # checks the author id against the list of registered users
        if author.id not in registeredlist:
            await ctx.send(f"{ctx.author} does not appear to be registered.")
            return
        # grabs the nation information
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        # sets the color properly
        if userinfo["usercolor"] == "":
            color = discord.Color.random()
            colorvalue = "No color set."
        else:
            color = discord.Color(int(userinfo["usercolor"].lstrip('#'), 16))
            colorvalue = color
        # grabs all provinces owned by the nation and makes them into a pretty list
        if len(userinfo["provinces_owned"]) != 1:
            provinceslist = userinfo["provinces_owned"]
            if 0 in provinceslist:
                provinceslist.remove(0)
            provinceslist.sort()
            provinces = ', '.join(str(i) for i in provinceslist)
            total_troops = 0
            total_troops = 0
            total_troops_raw = await conn.fetchrow('''SELECT sum(troops::int) FROM provinces 
            WHERE occupier_id = $1;''', author.id)
            total_troops += total_troops_raw['sum']
            total_troops += userinfo['undeployed']
        else:
            provinceslist = []
            provinces = "None"
            total_troops = userinfo['undeployed']
        # sets focus
        if userinfo['focus'] == "m":
            focus = "Military"
        elif userinfo['focus'] == "e":
            focus = "Economy"
        elif userinfo['focus'] == "s":
            focus = "Strategy"
        elif userinfo['focus'] == "none":
            focus = "None"
        # fetches relations information
        relations = await conn.fetch('''SELECT * FROM relations WHERE name = $1;''',
                                     userinfo['username'])
        if relations:
            alliances = list()
            wars = list()
            trade_list = list()
            for r in relations:
                if r['relation'] == 'war':
                    wars.append(r)
                if r['relation'] == 'alliance':
                    alliances.append(r)
            if len(wars) != 0:
                wars.sort()
                wars = ', '.join(str(w['nation']) for w in wars)
            else:
                wars = "None"
            if len(alliances) != 0:
                alliances.sort()
                alliances = ', '.join(str(a['nation']) for a in alliances)
            else:
                alliances = "None"
        else:
            alliances = "None"
            wars = "None"
        outgoing_routes = await conn.fetch('''SELECT * FROM interactions WHERE type = 'trade' AND active = True AND 
        sender_id = $1;''', author.id)
        routes_dict = dict()
        routes = ''
        route_number = 0
        for t in outgoing_routes:
            routes_dict.update({t['recipient']: 0})
        for t in outgoing_routes:
            routes_dict[t['recipient']] += 1
            route_number += 1
        for t in routes_dict:
            routes += f"{t} ({routes_dict[t]}), "
        routes = routes[:-2]
        max_manpower = 3000
        manpower_mod = userinfo['public_services'] / 100
        max_manpower_raw = await conn.fetchrow('''SELECT sum(manpower::int) FROM provinces WHERE owner_id = $1;''',
                                               author.id)
        if max_manpower_raw['sum'] is None:
            max_manpower_raw = 0
        else:
            max_manpower_raw = max_manpower_raw['sum']
        max_manpower += max_manpower_raw
        added_manpower = math.ceil(max_manpower * manpower_mod)
        # creates the embed item
        cncuserembed = discord.Embed(title=userinfo["username"], color=color,
                                     description=f"Registered nation of "
                                                 f"{self.bot.get_user(userinfo['user_id']).name}.")
        cncuserembed.add_field(name=f"Territory (Total: {len(provinceslist)})", value=provinces, inline=False)
        cncuserembed.add_field(name="Total Troops", value=f"{total_troops:,}")
        cncuserembed.add_field(name="Undeployed Troops", value=f"{userinfo['undeployed']:,}")
        cncuserembed.add_field(name="Resources", value=f"\u03FE{userinfo['resources']:,}")
        cncuserembed.add_field(name="National Focus", value=focus)
        cncuserembed.add_field(name="Color", value=colorvalue)
        cncuserembed.add_field(name="Action Points", value=userinfo['moves'])
        cncuserembed.add_field(name="Alliances", value=alliances)
        cncuserembed.add_field(name="Wars", value=wars)
        cncuserembed.add_field(name="National Unrest", value=str(userinfo['national_unrest']))
        cncuserembed.add_field(name="City/Port/Fort Limit",
                               value=f"City Limit: {userinfo['citylimit'][1]}\n"
                                     f"Port Limit: {userinfo['portlimit'][1]}\n"
                                     f"Fort Limit: {userinfo['fortlimit'][1]}")
        cncuserembed.add_field(name="Trade Route Overview",
                               value=f"Outgoing Routes: {userinfo['trade_routes'][0]}\n"
                                     f"Incoming Routes: {userinfo['trade_routes'][1]}\n"
                                     f"Active Routes ({route_number}): {routes}\n"
                                     f"Max Routes: {userinfo['trade_routes'][2]}")
        cncuserembed.add_field(name="Manpower/Manpower Limit",
                               value=f"{userinfo['manpower']:,}/{userinfo['maxmanpower']:,}")
        cncuserembed.add_field(name="Manpower Increase", value=f"{added_manpower:,}")
        cncuserembed.add_field(name="Economic Status",
                               value=f"Taxation Rate: {userinfo['taxation']}%\n"
                                     f"Military Upkeep: {userinfo['military_upkeep']}%\n"
                                     f"Public Services: {userinfo['public_services']}%")
        if ctx.guild is not None:
            await ctx.send("Sent!")
        await author.send(embed=cncuserembed)

    @commands.command(aliases=['cncva'], brief="Displays information about all nations")
    @commands.guild_only()
    async def cnc_view_all(self, ctx):
        # connects to the database
        conn = self.bot.pool
        registeredusers = await conn.fetch('''SELECT * FROM cncusers;''')
        viewallembed = discord.Embed(title="Registered Nations and Users", color=discord.Color.dark_red(),
                                     description="This is list up to date with all users, ids, and information")
        viewallembed.set_thumbnail(url="https://i.ibb.co/gTpHmgq/Command-Conquest-symbol.png")
        for users in [userids['user_id'] for userids in registeredusers]:
            individualinformation = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', users)
            user = self.bot.get_user(individualinformation['user_id'])
            viewallembed.add_field(name=f"__{individualinformation['username']}__",
                                   value=f"**Discord Username:** {user.display_name}\n"
                                         f"**Color:** {individualinformation['usercolor']}")
        await ctx.send(embed=viewallembed)

    @commands.command(aliases=['cncsv'],
                      brief="Displays detailed information about all provinces a nation owns, privately")
    async def cnc_strategic_view(self, ctx):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # if the nationame is left blank, the author id is used to find the nation information
        registeredusers = await conn.fetch('''SELECT user_id FROM cncusers;''')
        registeredlist = list()
        # makes a list of the registered users
        for users in registeredusers:
            registeredlist.append(users["user_id"])
        # checks the author id against the list of registered users
        if author.id not in registeredlist:
            await ctx.send(f"{ctx.author} does not appear to be registered.")
            return
        # pulls the specified nation data
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        provinces = list(userinfo['provinces_owned'])
        if 0 in provinces:
            provinces.remove(0)
        provinces.sort()
        # gets user's color in Discord format
        color = discord.Color(int(userinfo["usercolor"].lstrip('#'), 16))
        colorvalue = color
        # creates embed
        sv_emebed = discord.Embed(title=f"{userinfo['username']} - Strategic View",
                                  description="A strategic overlook at all troop placements and provinces.",
                                  color=colorvalue)
        # counts off numbers
        province_number = 0
        for p in provinces:
            # fetches province information, adds it to the embed, and increases the count
            provinceinfo = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', p)
            sv_emebed.add_field(name=f"**Province #{p}**",
                                value=f"Troops: {provinceinfo['troops']:,}\nTrade Value: {provinceinfo['trade_value']}"
                                      f"\nManpower: {provinceinfo['manpower']:,}\nUnrest: {provinceinfo['unrest']}")
            province_number += 1
            # if there are 15 provinces queued, send the embed, clear it, and start over
            # (unless this is the last set)
            if province_number % 15 == 0 and province_number != len(provinces):
                await author.send(embed=sv_emebed)
                sv_emebed.clear_fields()
                continue
            # if the maximum provinces have been reached, send the final set
            if province_number == len(provinces):
                await author.send(embed=sv_emebed)
                if ctx.guild is not None:
                    await ctx.send("Sent!")
                return

    @commands.command(aliases=['cncgp'], brief="Displays list of top 10 great powers and their scores")
    @commands.guild_only()
    async def cnc_great_powers(self, ctx):
        conn = self.bot.pool
        powers = await conn.fetch('''SELECT * FROM cncusers ORDER BY great_power_score DESC LIMIT 10;''')
        power = 1
        power_string = ""
        for p in powers:
            if p['great_power_score'] > 50:
                power_string += f"`{power}. {p['username']}"
                spaces = 60 - len(f"`{power}. {p['username']}")
                for s in range(spaces):
                    power_string += " "
                power_string += f"` `{p['great_power_score']}`\n"
                power += 1
            else:
                for n in range(4 - power):
                    power_string += f"`{power}. "
                    for n in range(60 - len(f"`{power}. ")):
                        power_string += " "
                    power_string += f"` `50`\n"
                    power += 1
                power_string += f"`{power}. {p['username']}"
                spaces = 60 - len(f"`{power}. {p['username']}")
                for s in range(spaces):
                    power_string += " "
                power_string += f"` `{p['great_power_score']}`\n"
                power += 1
        gpembed = discord.Embed(title="Great Power List",
                                description=power_string)
        await ctx.send(embed=gpembed)

    @commands.command(usage="[nation name] <reason>", brief="Completely removes a user from the CNC system. Owner only")
    @commands.is_owner()
    async def cnc_remove(self, ctx, nationname: str, reason: str = None):
        # loop for thread
        loop = asyncio.get_running_loop()
        # connects to the database
        conn = self.bot.pool
        # grabs user information
        users = await conn.fetch('''SELECT username FROM cncusers;''')
        # makes a list of users
        userlist = list()
        for user in users:
            userlist.append(user["username"].lower())
        # checks to see if the nation is registered
        if nationname.lower() not in userlist:
            await ctx.send(f"The user `{nationname}` does not appear to be registered.")
            return
        # grabs all nation information
        nationamesave = await conn.fetchrow('''SELECT username FROM cncusers WHERE lower(username) = $1;''',
                                            nationname.lower())
        # grabs the user id
        user_info = await conn.fetchrow('''SELECT * FROM cncusers WHERE lower(username) = $1;''',
                                        nationname.lower())
        # deletes the user and sends them a DM with the notification
        await conn.execute('''DELETE FROM cncusers WHERE lower(username) = $1;''', nationname.lower())
        # updates province and map information
        for province in user_info['provinces_owned']:
            await conn.execute('''UPDATE provinces  SET owner_id = 0, owner = '', troops = 0 WHERE id = $1;''',
                               province)
            color = "#808080"
            cord = await conn.fetchrow('''SELECT cord FROM provinces WHERE id = $1;''', province)
            await loop.run_in_executor(None, self.map_color, province, cord['cord'][0:2], color, True)
        # updates relations information
        await conn.execute('''DELETE FROM relations WHERE name = $1 or nation = $1;''', nationname.lower())
        await ctx.send("Deletion complete.")
        user = self.bot.get_user(user_info["user_id"])
        if reason is None:
            reason = "Your registered Command and Conquest account has been terminated for an unlisted reason. " \
                     "If you have further questions, contact a moderator."
        await user.send(
            f"Your registered Command and Conquer account, {nationamesave['username']}, "
            f"has been deleted by moderator {ctx.author} for the following reason:```{reason}```")

    @commands.command(usage="[item being edited (color or focus)]", brief="Changes a nation's registered color")
    @commands.guild_only()
    async def cnc_edit(self, ctx, editing: str):
        loop = asyncio.get_running_loop()
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # grabs all the user info
        usereditinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        # if the author is not registered
        if usereditinfo is None:
            await ctx.send(f"{author} is not registered.")
            return
        # if the color is being edited
        if editing.lower() == "color":
            await ctx.send("What would you like your new color to be? Include the # with your color code.")

            def authorcheck(message):
                return ctx.author == message.author and ctx.channel == message.channel

            # waits for a reply
            try:
                colorreply = await self.bot.wait_for('message', check=authorcheck, timeout=60)
            # if 60 seconds pass, timeout
            except asyncio.TimeoutError:
                return await ctx.send("Timed out. Please answer me next time!")
            # makes sure color is not banned or taken
            registered = await conn.fetch('''SELECT * FROM cncusers;''')
            if colorreply.content.lower() in self.banned_colors:
                await ctx.send("That color is a reserved color. Please pick another color.")
                return
            colors = [u['usercolor'].lower() for u in registered]
            if colorreply.content.lower() in colors:
                await ctx.send("That color is already taken by another user. Please pick another color.")
                return
            try:
                ImageColor.getrgb(colorreply.content)
            except ValueError:
                await ctx.send("That doesn't appear to be a valid hex color code.")
                return
            # updates map with colors
            user = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
            for p in user['provinces_owned'][1:]:
                cord = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', p)
                cord = (x, y) = (cord['cord'][0], cord['cord'][1])
                await loop.run_in_executor(None, self.map_color, p, cord, colorreply.content)
            await conn.execute('''UPDATE cncusers SET usercolor = $1 WHERE user_id = $2;''', colorreply.content,
                               author.id)
            await ctx.send(f"Success! Your new color is {colorreply.content}.")
            return
        # if the focus is being edited
        if editing.lower() == "focus":
            await ctx.send("What would you like your new nation focus to be?")

            def authorcheck(message):
                return ctx.author == message.author and ctx.channel == message.channel

            # wait for a reply
            try:
                focusreply = await self.bot.wait_for('message', check=authorcheck, timeout=60)
            # if 60 seconds pass, timeout
            except asyncio.TimeoutError:
                return await ctx.send("Timed out. Please answer me next time!")
            # if the content is not in the proper format
            if focusreply.content.lower() not in ["m", "e", "s"]:
                raise commands.UserInputError
            # execute the information
            await conn.execute('''UPDATE cncusers SET focus = $1 WHERE user_id = $2;''', focusreply.content.lower(),
                               author.id)
            if focusreply.content.lower() == "m":
                focus = "`military`"
            if focusreply.content.lower() == "e":
                focus = "`economy`"
            if focusreply.content.lower() == "s":
                focus = "`strategy`"
            await ctx.send(f"Success! Your new focus is {focus}.")
            return
        else:
            # if the editing argument is not the proper argument
            await ctx.send(f"`{editing}` is not a viable option for this command!")
            return

    # ---------------------Province Commands------------------------------

    @commands.command(usage="[province id]", aliases=['cncp'], brief="Displays information about a specified province")
    async def cnc_province(self, ctx, provinceid: int):
        # connects to the database
        conn = self.bot.pool
        # ensures province existence
        provinces = await conn.fetch('''SELECT id FROM provinces;''')
        provinces = [p['id'] for p in provinces]
        if provinceid not in provinces:
            await ctx.send("No such province.")
            return
        # fetches province information
        province = dict(await conn.fetchrow('''SELECT * FROM provinces  WHERE id = $1;''', provinceid))
        # fetches terrain name and color information
        terrain = await conn.fetchrow('''SELECT name, color FROM terrains WHERE id = $1;''', province['terrain'])
        # if there is no province owner
        if province['owner'] == '':
            owner = "None"
            occupier = "None"
        else:
            owner = province['owner']
            occupier = province['occupier']
        # sorts the bordering
        borderinglist = province['bordering']
        borderinglist.sort()
        bordering = ', '.join(str(b) for b in borderinglist)
        # gets the color set
        color = discord.Color(int(terrain["color"].lstrip('#'), 16))
        # checks for river presence
        if province['river'] is not False:
            riverstring = ", River"
        else:
            riverstring = ''
        # sets up the structures
        structures = []
        if province['port'] is True:
            structures.append('Port')
        if province['fort'] is True:
            structures.append('Fort')
        if province['city'] is True:
            structures.append('City')
        structlist = ', '.join(s for s in structures)
        if len(structures) == 0:
            structlist = "None"
        # creates the embed object
        provinceembed = discord.Embed(title=f"{province['name']} (Province #{province['id']})", color=color)
        provinceembed.add_field(name="Terrain", value=terrain['name'] + riverstring)
        provinceembed.add_field(name="Structures", value=structlist)
        provinceembed.add_field(name="Bordering Provinces", value=bordering)
        provinceembed.add_field(name="Core Owner", value=owner)
        provinceembed.add_field(name="Occupying Nation", value=occupier)
        provinceembed.add_field(name="Troops Present", value=f"{province['troops']:,}")
        provinceembed.add_field(name="Local Unrest", value=str(province['unrest']))
        provinceembed.add_field(name="Trade Value", value=province['trade_value'])
        provinceembed.add_field(name="Manpower", value=f"{province['manpower']:,}")
        provinceembed.set_thumbnail(url="https://i.ibb.co/gTpHmgq/Command-Conquest-symbol.png")
        # sets the proper coastline
        if province['coast'] is True:
            coastline = "Yes"
        else:
            coastline = "No"
        provinceembed.add_field(name="Coastline", value=coastline)
        await ctx.send(embed=provinceembed)

    @commands.command(usage="[province id]", brief="Releases a specified province")
    @commands.guild_only()
    async def cnc_release(self, ctx, provinceid: int):
        loop = asyncio.get_running_loop()
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # fetches all user ids
        allusers = await conn.fetch('''SELECT user_id, username FROM cncusers''')
        alluserids = list()
        allusernames = list()
        for id in allusers:
            alluserids.append(id['user_id'])
        for names in allusers:
            allusernames.append(names['username'].lower())
        # ensures author registration
        if author.id not in alluserids:
            await ctx.send(f"{author} not registered.")
            return
        # fetches all province ids
        allprovinces = await conn.fetch('''SELECT id FROM provinces''')
        allids = list()
        for pid in allprovinces:
            allids.append(pid['id'])
        # ensures province validity
        if provinceid not in allids:
            await ctx.send(f"Location id `{provinceid}` is not a valid ID.")
            return
        # fetches user info
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        # fetches province information
        provinceinfo = await conn.fetchrow('''SELECT * FROM provinces  WHERE id = $1;''', provinceid)
        if provinceinfo['owner_id'] != author.id and provinceinfo['occupier_id'] != author.id:
            await ctx.send(f"{userinfo['username']} does not own and occupy province #{provinceid}.")
            return
        # clears province and return troops to owner, removes province from owner, places native troops
        terrain = provinceinfo['terrain']
        troops = 0
        if terrain == 0:
            troops = randrange(1000, 3000)
        if terrain == 1:
            troops = randrange(500, 1000)
        if terrain == 2:
            troops = randrange(1000, 3000)
        if terrain == 5:
            troops = randrange(200, 500)
        if terrain == 7:
            troops = randrange(200, 500)
        if terrain == 9:
            troops = randrange(100, 300)
        ownedlist = userinfo['provinces_owned']
        ownedlist.remove(provinceid)
        await conn.execute('''UPDATE provinces SET owner = '', owner_id = 0, occupier = '', occupier_id = 0,
         troops = $2 WHERE id = $1;''', provinceid, troops)
        await conn.execute('''UPDATE cncusers SET undeployed = $1, provinces_owned = $2 WHERE user_id = $3;''',
                           (userinfo['undeployed'] + provinceinfo['troops']), ownedlist, author.id)
        await ctx.send(
            f"Province #{provinceid} has been released. Natives have retaken control of the province.")
        color = await conn.fetchrow('''SELECT color FROM terrains WHERE id = $1;''', provinceinfo['terrain'])
        await loop.run_in_executor(None, self.map_color, provinceid, provinceinfo['cord'][0:2], color['color'],
                                   True)

    @commands.command(usage="[province id] [name]", brief="Renames a province.")
    @commands.guild_only()
    async def cnc_rename_province(self, ctx, provinceid: int, name: str):
        conn = self.bot.pool
        province = await conn.fetchrow('''SELECT owner_id FROM provinces WHERE id = $1;''', provinceid)
        if province is None:
            await ctx.send(f"`{provinceid}` is not a valid province ID.")
            return
        elif province['owner_id'] != ctx.author.id:
            await ctx.send("You can only rename provinces that you own!")
            return
        await conn.execute('''UPDATE provinces SET name = $1 WHERE id = $2;''', name, provinceid)
        await ctx.send(f"Province #{provinceid} is now {name}!")

    @commands.command(usage="[province id] <deployed force>",
                      aliases=['cncd'], brief="Deploys a number of troops to a specified province")
    @commands.guild_only()
    async def cnc_deploy(self, ctx, location: int, amount: int = None):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # fetches all users
        allusers = await conn.fetch('''SELECT user_id FROM cncusers;''')
        alluserids = list()
        for id in allusers:
            alluserids.append(id['user_id'])
        # checks if author is registered
        if author.id not in alluserids:
            await ctx.send(f"{author} not registered.")
            return
        # fetches all province ids
        allprovinces = await conn.fetch('''SELECT id FROM provinces;''')
        allids = list()
        for x in allprovinces:
            allids.append(x['id'])
        # ensures valid id
        if location not in allids:
            await ctx.send(f"`{location}` is not a valid location ID.")
            return
        # fetches user and province info
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        userprovinces = userinfo['provinces_owned']
        userundeployed = userinfo['undeployed']
        provinceinfo = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', location)
        # ensures location ownership
        if provinceinfo['occupier_id'] != author.id:
            await ctx.send(
                f"{userinfo['username']} does not own Province #{location} and cannot deploy troops there.")
            return
        # ensures troop sufficiency
        if amount is not None:
            if amount > userundeployed:
                await ctx.send(f"{userinfo['username']} does not have {amount} undeployed troops.")
                return
        # updates all user and province information
        if amount is None:
            amount = userundeployed
        await conn.execute('''UPDATE cncusers SET undeployed = $1 WHERE user_id = $2;''',
                           (userundeployed - amount),
                           author.id)
        await conn.execute('''UPDATE provinces SET troops = $1 WHERE id = $2;''',
                           (provinceinfo['troops'] + amount),
                           location)
        await ctx.send(f"{userinfo['username']} has successfully deployed {amount} troops to Province #{location}.")

    @commands.command(usage="[province id] [recipient nation]",
                      brief="Transfers a province to another nation's control")
    @commands.guild_only()
    async def cnc_transfer(self, ctx, provinceid: int, recipient: str):
        loop = asyncio.get_running_loop()
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # fetches all user ids
        allusers = await conn.fetch('''SELECT user_id, username FROM cncusers''')
        alluserids = list()
        allusernames = list()
        for id in allusers:
            alluserids.append(id['user_id'])
        for names in allusers:
            allusernames.append(names['username'].lower())
        # ensures author registration
        if author.id not in alluserids:
            await ctx.send(f"{author} not registered.")
            return
        # ensures recipient existance
        if recipient.lower() not in allusernames:
            await ctx.send(f"`{recipient}` not registered.")
            return
        # fetches all province ids
        allprovinces = await conn.fetch('''SELECT id FROM provinces''')
        allids = list()
        for pid in allprovinces:
            allids.append(pid['id'])
        # ensures province validity
        if provinceid not in allids:
            await ctx.send(f"Location id `{provinceid}` is not a valid ID.")
            return
        # fetches user info
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        # fetches province information
        provinceinfo = await conn.fetchrow('''SELECT * FROM provinces  WHERE id = $1;''', provinceid)
        # ensures province ownership
        if provinceinfo['owner_id'] != author.id and provinceinfo['occupier_id'] != author.id:
            await ctx.send(f"{userinfo['username']} does not own and occupy province #{provinceid}.")
            return
        # clears province and return troops to owner, removes province from owner
        ownedlist = userinfo['provinces_owned']
        ownedlist.remove(provinceid)
        await conn.execute('''UPDATE provinces  SET troops = 0 WHERE id = $1;''', provinceid)
        await conn.execute('''UPDATE cncusers SET undeployed = $1, provinces_owned = $2 WHERE user_id = $3;''',
                           (userinfo['undeployed'] + provinceinfo['troops']), ownedlist, author.id)
        # adds province to recipient
        recipientinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE lower(username) = $1;''',
                                            recipient.lower())
        recipientowned = recipientinfo['provinces_owned']
        recipientowned.append(provinceid)
        await conn.execute('''UPDATE cncusers SET provinces_owned = $1 WHERE lower(username) = $2;''',
                           recipientowned, recipient.lower())
        # sets province owner info
        await conn.execute('''UPDATE provinces  SET owner = $1, owner_id = $2, occupier = $1, occupier_id = $2
         WHERE id = $3;''',
                           recipientinfo['username'], recipientinfo['user_id'], provinceid)
        await ctx.send(
            f"Province #{provinceid} transferred to the ownership of {recipientinfo['username']} "
            f"by {userinfo['username']}. All {provinceinfo['troops']} troops in province #{provinceid} "
            f"have withdrawn.")
        await loop.run_in_executor(None, self.map_color, provinceid, provinceinfo['cord'][0:2],
                                   recipientinfo['usercolor'])

    # ---------------------Interaction Commands------------------------------

    @commands.command(usage="<offer id>", aliases=['cncvi'],
                      brief="Displays information about a specific interaction or all interactions")
    async def cnc_view_interaction(self, ctx, interactionid: int = None):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        if interactionid is None:
            with open(f"{self.interaction_directory}{author.id}.txt", "rb") as file:
                await author.send(file=discord.File(file, f"Interactions Log for {author.id}.txt"))
                if ctx.guild is not None:
                    await ctx.send("Sent!")
                return
        interaction = await conn.fetchrow('''SELECT * FROM interactions WHERE id = $1;''', interactionid)
        if interaction is None:
            await ctx.send("No such interaction.")
            return
        if interaction['sender_id'] != author.id and interaction['recipient_id'] != author.id:
            await ctx.send("You are not authorized to view that offer.")
            return
        upload = False
        if len(interaction['terms']) > 1024:
            terms = "See File Upload"
            upload = True
        else:
            terms = interaction['terms']
        embed = discord.Embed(title=f"Interaction #{interaction['id']}",
                              description=f"An declaration of {interaction['type']} from {interaction['sender']}.")
        embed.add_field(name="Interaction Type", value=f"{interaction['type'].title()}")
        embed.add_field(name="Sender", value=f"{interaction['sender']}")
        embed.add_field(name="Recipient", value=f"{interaction['recipient']}")
        embed.add_field(name="Terms", value=f"{terms}", inline=False)
        embed.add_field(name="Active", value=f"{interaction['active']}")
        await ctx.send(embed=embed)
        if upload is True:
            with open(f"{self.interaction_directory}{interaction['id']}.txt", "r") as file:
                await ctx.send(file=discord.File(file, f"{interaction['id']}.txt"))

    @commands.command(usage="[offer id]", brief="Displays a specific offer with information")
    async def cnc_offer(self, ctx, offerid: int):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        offer = await conn.fetchrow('''SELECT * FROM pending_interactions WHERE id = $1;''', offerid)
        if offer is None:
            await ctx.send("No such pending offer.")
            return
        if offer['sender_id'] != author.id and offer['recipient_id'] != author.id:
            await ctx.send("You are not authorized to view that offer.")
            return
        upload = False
        if len(offer['terms']) > 1024:
            terms = "See File Upload"
            upload = True
        else:
            terms = offer['terms']
        embed = discord.Embed(title=f"Offer #{offer['id']}",
                              description=f"An offer of {offer['type']} from {offer['sender']}.")
        embed.add_field(name="Offer Type", value=f"{offer['type'].title()}")
        embed.add_field(name="Sender", value=f"{offer['sender']}")
        embed.add_field(name="Terms", value=f"{terms}", inline=False)
        await ctx.send(embed=embed)
        if upload is True:
            with open(f"{self.interaction_directory}{offer['id']}.txt", "r") as file:
                await ctx.send(file=discord.File(file, f"{offer['id']}.txt"))

    @commands.command(usage="[interaction id] [interaction (accept, reject, cancel)]", aliases=['cnci'],
                      brief="Allows for interacting with a proposed interaction")
    async def cnc_interaction(self, ctx, interactionid: int, interaction: str):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        if interaction == "accept" or interaction == "reject":
            # fetches interaction information
            pending_int = await conn.fetchrow('''SELECT * FROM pending_interactions WHERE id = $1;''',
                                              interactionid)
            # checks for existence
            if pending_int is None:
                await ctx.send("No such pending interaction.")
                return
            # checks for authority
            if pending_int['recipient_id'] != author.id:
                await ctx.send("You are not authorized to accept or reject that interaction.")
                return
            if interaction.lower() == "accept":
                # update all the relevant information into interactions
                await conn.execute('''INSERT INTO interactions(id, type, sender, sender_id, recipient, 
                recipient_id, terms) SELECT id, type, sender, sender_id, recipient, recipient_id, terms 
                FROM pending_interactions WHERE id = $1;''', interactionid)
                await conn.execute('''  UPDATE interactions SET active = True WHERE id = $1;''', interactionid)
                await conn.execute('''DELETE FROM pending_interactions WHERE id = $1;''', interactionid)
                # if a peace treaty, cancel war, return occupied provinces, and color map
                if pending_int['type'] == 'peace':
                    await conn.execute('''UPDATE interactions SET active = False WHERE id = $1;''',
                                       interactionid)
                    await conn.execute(
                        '''UPDATE interactions SET active = False WHERE type = 'war' AND sender = $1 AND 
                        recipient = $2;''', pending_int['sender'], pending_int['recipient'])
                    sender_occupied = await conn.fetch(
                        '''SELECT * FROM provinces WHERE occupier = $1 AND owner = $2;''',
                        pending_int['sender'], pending_int['recipient'])
                    recip_occupied = await conn.fetch(
                        '''SELECT * FROM provinces WHERE occupier = $2 AND owner = $1;''',
                        pending_int['sender'], pending_int['recipient'])
                    await conn.execute('''UPDATE relations SET relation = 'peace' WHERE (nation = $1 AND name = $2) OR
                    (nation = $2 AND name = $1);''', pending_int['sender'], pending_int['recipient'])
                    if sender_occupied:
                        owner_color = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1;''',
                                                          pending_int['recipient'])
                        owner_color = owner_color['usercolor']
                        for p in sender_occupied:
                            await self.bot.loop.run_in_executor(None, self.map_color, p['id'], p['cord'], owner_color)
                            await conn.execute('''UPDATE provinces SET occupier = $1, occupier_id = $2 WHERE id = $3;''',
                                               p['owner'], p['owner_id'], p['id'])
                    if recip_occupied:
                        owner_color = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1;''',
                                                          pending_int['sender'])
                        owner_color = owner_color['usercolor']
                        for p in recip_occupied:
                            await self.bot.loop.run_in_executor(None, self.map_color, p['id'], p['cord'], owner_color)
                            await conn.execute('''UPDATE provinces SET occupier = $1, occupier_id = $2 WHERE id = $3;''',
                                               p['owner'], p['owner_id'], p['id'])
                # if trade, update user information
                if pending_int['type'] == 'trade':
                    senderinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''',
                                                     pending_int['sender_id'])
                    recipinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''',
                                                    pending_int['recipient_id'])
                    sender_trs = senderinfo['trade_routes']
                    sender_trs[0] += 1
                    recip_trs = recipinfo['trade_routes']
                    recip_trs[1] += 1
                    await conn.execute('''UPDATE cncusers SET trade_routes = $1 WHERE user_id = $2;''',
                                       sender_trs, senderinfo['user_id'])
                    await conn.execute('''UPDATE cncusers SET trade_routes = $1 WHERE user_id = $2;''',
                                       recip_trs, recipinfo['user_id'])
                # updates interaction files
                interaction_text = f"Offer #{pending_int['id']} of {pending_int['type']}.\nSent by: " \
                                   f"{pending_int['sender']}\nAccepted by: {pending_int['recipient']}" \
                                   f"\n**Terms**\n{pending_int['terms']}\n" \
                                   f"Accepted: {strftime('%D', localtime(time()))}"
                with open(f"{self.interaction_directory}{pending_int['sender_id']}.txt", "r+") as file:
                    oldcontent = file.read()
                    file.seek(0, 0)
                    file.write(interaction_text.rstrip('\r\n') + '\n' + oldcontent)
                with open(f"{self.interaction_directory}{pending_int['recipient_id']}.txt", "r+") as file:
                    oldcontent = file.read()
                    file.seek(0, 0)
                    file.write(interaction_text.rstrip('\r\n') + '\n' + oldcontent)
                # get user object and send message
                sender = self.bot.get_user(pending_int['sender_id'])
                await sender.send(
                    f"{pending_int['recipient']} has accepted your offer of a(n) {pending_int['type']}. "
                    f"To view this, use `$cnc_view_interaction {interactionid}`.")
                await ctx.send("Accepted.")
            if interaction.lower() == "reject":
                # removes terms file
                if os.path.exists(f"{self.interaction_directory}{interactionid}.txt"):
                    os.remove(f"{self.interaction_directory}{interactionid}.txt")
                # remove pending interaction
                await conn.execute('''DELETE FROM pending_interactions WHERE id = $1;''', interactionid)
                sender = self.bot.get_user(pending_int['sender_id'])
                await sender.send(
                    f"{pending_int['recipient']} has rejected your offer of a(n) {pending_int['type']}.")
                await ctx.send("Rejected.")
        elif interaction.lower() == "cancel":
            # fetches interaction data
            interact = await conn.fetchrow('''SELECT * FROM interactions WHERE id = $1;''', interactionid)
            # checks for existence
            if interact is None:
                await ctx.send("No such interaction.")
                return
            # ensures correct type
            if interact['type'] == 'war':
                await ctx.send("Only alliances and treaties can be cancelled. Wars must be resolved through using "
                               "the peace command.")
                return
            # ensures authority
            if (interact['recipient_id'] != author.id) and (interact['sender_id'] != author.id) and (
                    not self.bot.is_owner(author)):
                await ctx.send("You are not authorized to cancel that interaction.")
                return
            sender = interact['sender']
            recipient = interact['recipient']
            # updates relation and interaction data
            if interact['type'] == 'alliance':
                await conn.execute(
                    '''UPDATE relations SET relation = 'peace' WHERE name = $1 AND nation = $2;''',
                    sender, recipient)
                await conn.execute(
                    '''UPDATE relations SET relation = 'peace' WHERE name = $1 AND nation = $2;''',
                    recipient, sender)
            # removes trade routes and information
            elif interact['type'] == 'trade':
                await conn.execute('''UPDATE relations SET trade = False WHERE name = $1 AND nation = $2
                    OR name = $2 AND nation = $1;''',
                                   sender, recipient)
                trade_interaction = await conn.fetchrow('''SELECT * FROM interactions WHERE type = 'trade' AND 
                active = True AND sender = $1 AND recipient = $2 OR sender = $2 AND recipient = $1;''',
                                                        sender, recipient)
                trade_sender = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1;''',
                                                   trade_interaction['sender'])
                trade_recipient = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1;''',
                                                      trade_interaction['recipient'])
                trade_sender_routes = trade_sender['trade_routes']
                trade_sender_routes[0] -= 1
                trade_recip_routes = trade_recipient['trade_routes']
                trade_recip_routes[1] -= 1
                await conn.execute('''UPDATE cncusers SET trade_routes = $1 WHERE username = $2;''',
                                   trade_sender_routes, trade_sender['username'])
                await conn.execute('''UPDATE cncusers SET trade_routes = $1 WHERE username = $2;''',
                                   trade_recip_routes, trade_recipient['username'])
            await conn.execute('''UPDATE interactions SET active = False WHERE id = $1;''', interactionid)
            await ctx.send(f"{interact['type'].title()} between {sender} and {recipient} canceled.")
            # DMs relevant parties
            sender = self.bot.get_user(interact['sender_id'])
            await sender.send(f"Your {interact['type']} with {recipient} has been terminated.")
            recipient = self.bot.get_user(interact['recipient_id'])
            await recipient.send(f"Your {interact['type']} with {sender} has been terminated.")
        else:
            raise commands.UserInputError

    @commands.command(brief="Displays all pending interactions and offers")
    async def cnc_view_pending(self, ctx):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        interactions = await conn.fetch(
            '''SELECT * FROM pending_interactions WHERE sender_id = $1 or recipient_id = $1;''', author.id)
        if not interactions:
            await ctx.send("No pending interactions found.")
            return
        interactions_text = ''
        for i in interactions:
            text = f"Offer of `{i['type']}` from `{i['sender']}` to `{i['recipient']}` pending. " \
                   f"`{self.bot.command_prefix}cnc_offer {i['id']}`.\n"
            interactions_text += text
        await author.send(interactions_text)
        if ctx.guild is not None:
            await ctx.send("Sent!")

    @commands.command(usage="[nation],, [terms]", brief="Sends an alliance offer to a nation")
    async def cnc_alliance(self, ctx, *, args):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        data = args.split(',,')
        if len(data) != 2:
            raise WrongInput
        rrecipient = data[0]
        text = data[1]
        text = text.lstrip(' ')
        # fetches all user ids
        allusers = await conn.fetch('''SELECT user_id, username FROM cncusers;''')
        alluserids = list()
        allusernames = list()
        for id in allusers:
            alluserids.append(id['user_id'])
        for names in allusers:
            allusernames.append(names['username'].lower())
        # ensures author registration
        if author.id not in alluserids:
            await ctx.send(f"{author} not registered.")
            return
        # ensures recipient existance
        if rrecipient.lower() not in allusernames:
            await ctx.send(f"`{rrecipient}` not registered.")
            return
        # checks for existing active alliance
        interactions = await conn.fetch(
            '''SELECT * FROM interactions WHERE type = 'alliance' AND active = True AND sender_id = $1;''',
            author.id)
        for inter in interactions:
            if (inter['recipient'].lower() == rrecipient.lower() and inter['sender_id'] == author.id) or (
                    inter['recipient_id'] == author.id and inter['sender'] == rrecipient.lower()):
                await ctx.send(
                    f"An alliance with `{rrecipient}` already exists. "
                    f"To view, use $cnc_view_interaction {inter['id']}")
                return
        # fetches user information
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        # checks for enough action points
        if userinfo['moves'] <= 0:
            await ctx.send("You do not have enough action points for that!")
            return
        rinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE lower(username) = $1;''', rrecipient.lower())
        if userinfo['great_power'] and rinfo['great_power']:
            await ctx.send("Great Powers cannot be allied.")
            return
        aid = ctx.message.id
        atype = "alliance"
        sender = userinfo['username']
        sender_id = author.id
        recipient = rinfo['username']
        recipient_id = rinfo['user_id']
        terms = text
        if sender == recipient:
            await ctx.send("You cannot ally with yourself.")
            return
        # creates interaction text file
        with open(f"{self.interaction_directory}{aid}.txt", "w") as afile:
            afile.write(terms)
        # inserts information into pending interactions
        await conn.execute('''INSERT INTO pending_interactions (id, type, sender, sender_id, recipient,
                recipient_id, terms) VALUES($1, $2, $3, $4, $5, $6, $7);''', aid, atype, sender, sender_id,
                           recipient,
                           recipient_id, terms)
        # sends DM
        rsend = self.bot.get_user(recipient_id)
        await rsend.send(
            f"{sender} has sent an alliance offer to {recipient}. To view the terms, type "
            f"`{self.bot.command_prefix}cnc_offer {aid}`. To accept or reject, use "
            f"`{self.bot.command_prefix}cnc_interaction {aid} [accept/reject]`.")
        await ctx.send(f"Alliance offer sent to {recipient}.")

    @commands.command(usage="[recipient],, <goal>", brief="Declares war on a nation")
    @commands.guild_only()
    async def cnc_declare(self, ctx, *args):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # consolidates terms
        rawdata = ' '.join(args[:])
        data = rawdata.split(',,')
        rrecipient = data[0]
        if len(data) == 1:
            text = "None"
        else:
            text = data[1]
            text = text.lstrip(' ')
        # fetches all user ids
        allusers = await conn.fetch('''SELECT user_id, username FROM cncusers''')
        alluserids = list()
        allusernames = list()
        for id in allusers:
            alluserids.append(id['user_id'])
        for names in allusers:
            allusernames.append(names['username'].lower())
        # ensures author registration
        if author.id not in alluserids:
            await ctx.send(f"{author} not registered.")
            return
        # ensures recipient existance
        if rrecipient.lower() not in allusernames:
            await ctx.send(f"`{rrecipient}` not registered.")
            return
        # ensures prior peace
        interactions = await conn.fetch(
            '''SELECT * FROM interactions WHERE type = 'war' AND active = True AND sender_id = $1;''', author.id)
        for inter in interactions:
            if (inter['recipient'].lower() == rrecipient.lower() and inter['sender_id'] == author.id) or (
                    inter['recipient_id'] == author.id and inter['sender'] == rrecipient.lower()):
                await ctx.send(
                    f"A war with `{rrecipient}` already exists. To view, use `$cnc_view_interaction {inter['id']}`")
                return
        # fetches user information
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        if userinfo['moves'] <= 0:
            await ctx.send("You do not have enough action points for that!")
            return
        rinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE lower(username) = $1;''', rrecipient.lower())
        aid = ctx.message.id
        atype = "war"
        sender = userinfo['username']
        sender_id = author.id
        recipient = rinfo['username']
        recipient_id = rinfo['user_id']
        terms = text
        # ensures no self declarations
        if sender == recipient:
            await ctx.send("You cannot declare war on yourself.")
            return
        # ensures no alliance
        alliance = await conn.fetchrow('''SELECT * FROM relations WHERE name = $1 AND nation = $2;''',
                                       sender, recipient)
        if alliance['relation'] == 'war':
            await ctx.send(
                f"It is not possible to declare war on {recipient} when you are already at war with them!")
            return
        elif alliance['relation'] != 'peace':
            await ctx.send(f"It is not possible to declare war on {recipient} when you have an alliance with them!")
            return
        # creates text file for terms
        with open(f"{self.interaction_directory}{aid}.txt", "w") as afile:
            afile.write(terms)
        # inserts information into interactions
        await conn.execute('''INSERT INTO interactions (id, type, sender, sender_id, recipient,
                recipient_id, terms, active) VALUES($1, $2, $3, $4, $5, $6, $7, $8);''', aid, atype, sender,
                           sender_id,
                           recipient,
                           recipient_id, terms, True)
        # updates relations and trade routes
        await conn.execute('''UPDATE relations SET relation = 'war' WHERE name = $1 AND nation = $2
                                    OR name = $2 AND nation = $1;''',
                           sender, recipient)
        trade_interactions = await conn.fetch('''SELECT * FROM interactions WHERE (type = 'trade' AND 
                                active = True) AND (sender = $1 AND recipient = $2 OR sender = $2 AND recipient = $1);''',
                                              sender, recipient)
        for t in trade_interactions:
            await conn.execute('''UPDATE interactions SET active = False WHERE id = $1;''', t['id'])
            trade_sender = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1;''',
                                               t['sender'])
            trade_recipient = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1;''',
                                                  t['recipient'])
            trade_sender['trade_routes'][0] -= 1
            trade_recipient['trade_routes'][1] -= 1
            trade_sender_routes = trade_sender['trade_routes']
            trade_recip_routes = trade_recipient['trade_routes']
            await conn.execute('''UPDATE cncusers SET trade_routes = $1 WHERE username = $2;''',
                               trade_sender_routes, trade_sender['username'])
            await conn.execute('''UPDATE cncusers SET trade_routes = $1 WHERE username = $2;''',
                               trade_recip_routes, trade_recipient['username'])
            # subtracts action point
            await conn.execute('''UPDATE cncusers SET moves = $1 WHERE user_id = $2;''',
                               userinfo['moves'] - 1, author.id)
        # sends DM
        rsend = self.bot.get_user(recipient_id)
        await rsend.send(
            f"{sender} has declared war on {recipient}. To view the terms, type `$cnc_view_interaction {aid}`.")
        await author.send(
            f"{sender} has declared war on {recipient}. To view the terms, type `$cnc_view_interaction {aid}`.")
        await ctx.send(f"War declared on {recipient}!")

    @commands.command(usage="[recipient],, [terms]", brief="Sends a peace offer to a nation")
    async def cnc_peace(self, ctx, *args):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # consolidates terms
        rawdata = ' '.join(args[:])
        data = rawdata.split(',,')
        if len(data) < 2:
            raise commands.UserInputError
        rrecipient = data[0]
        text = data[1]
        text = text.lstrip(' ')
        # fetches all user ids
        allusers = await conn.fetch('''SELECT user_id, username FROM cncusers;''')
        alluserids = list()
        allusernames = list()
        for id in allusers:
            alluserids.append(id['user_id'])
        for names in allusers:
            allusernames.append(names['username'].lower())
        # ensures author registration
        if author.id not in alluserids:
            await ctx.send(f"{author} not registered.")
            return
        # ensures recipient existance
        if rrecipient.lower() not in allusernames:
            await ctx.send(f"`{rrecipient}` not registered.")
            return
        # fetches user information
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        rinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE lower(username) = $1;''', rrecipient.lower())
        aid = ctx.message.id
        atype = "peace"
        sender = userinfo['username']
        sender_id = author.id
        recipient = rinfo['username']
        recipient_id = rinfo['user_id']
        terms = text
        if sender == recipient:
            await ctx.send("You cannot negotiatee peace with yourself.")
            return
        # ensures war status
        war = await conn.fetchrow('''SELECT relation FROM relations WHERE name = $1 AND nation = $2;''', sender,
                                  recipient)
        if war['relation'] != 'war':
            await ctx.send(f"You cannot negotiate peace with {sender} if you are not at war!")
            return
        # creates text file of terms
        with open(f"{self.interaction_directory}{aid}.txt", "w") as afile:
            afile.write(terms)
        # inserts information into pending interactions
        await conn.execute('''INSERT INTO pending_interactions (id, type, sender, sender_id, recipient,
                recipient_id, terms) VALUES($1, $2, $3, $4, $5, $6, $7);''', aid, atype, sender, sender_id,
                           recipient,
                           recipient_id, terms)
        # sends DM
        rsend = self.bot.get_user(recipient_id)
        await rsend.send(
            f"{sender} has sent an peace offer to {recipient}. To view the terms, type "
            f"`{self.bot.command_prefix}cnc_offer {aid}`. To accept or reject, use "
            f"`{self.bot.command_prefix}cnc_interaction {aid} [(accept,reject)]`")
        await ctx.send(f"Peace offer sent to {recipient}.")

    @commands.command(usage="[recipient],, [terms]", brief="One-time agreement with a nation.")
    async def cnc_treaty(self, ctx, *, args):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        data = args.split(',,')
        if len(data) != 2:
            raise WrongInput
        rrecipient = data[0]
        text = data[1]
        text = text.lstrip(' ')
        # fetches all user ids
        allusers = await conn.fetch('''SELECT user_id, username FROM cncusers;''')
        alluserids = list()
        allusernames = list()
        for id in allusers:
            alluserids.append(id['user_id'])
        for names in allusers:
            allusernames.append(names['username'].lower())
        # ensures author registration
        if author.id not in alluserids:
            await ctx.send(f"{author} not registered.")
            return
        # ensures recipient existance
        if rrecipient.lower() not in allusernames:
            await ctx.send(f"`{rrecipient}` not registered.")
            return
        # fetches user information
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        rinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE lower(username) = $1;''', rrecipient.lower())
        aid = ctx.message.id
        atype = "treaty"
        sender = userinfo['username']
        sender_id = author.id
        recipient = rinfo['username']
        recipient_id = rinfo['user_id']
        terms = text
        if sender == recipient:
            await ctx.send("You cannot send yourself a treaty.")
            return
        # creates interaction text file
        with open(f"{self.interaction_directory}{aid}.txt", "w") as afile:
            afile.write(terms)
        # inserts information into pending interactions
        await conn.execute('''INSERT INTO pending_interactions (id, type, sender, sender_id, recipient,
                recipient_id, terms) VALUES($1, $2, $3, $4, $5, $6, $7);''', aid, atype, sender, sender_id,
                           recipient,
                           recipient_id, terms)
        # sends DM
        rsend = self.bot.get_user(recipient_id)
        await rsend.send(
            f"{sender} has sent an treaty offer to {recipient}. To view the terms, type "
            f"`{self.bot.command_prefix}cnc_offer {aid}`. To accept or reject, use "
            f"`{self.bot.command_prefix}cnc_interaction {aid} [accept/reject]`.")
        await ctx.send(f"Treaty offer sent to {recipient}.")

    @commands.command(usage="[recipient]", brief="Proposes trade between nations.")
    async def cnc_trade_route(self, ctx, *, args):
        # establishes connection and author
        author = ctx.author
        conn = self.bot.pool
        # ensures existence
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        if userinfo is None:
            await ctx.send("You are not registered.")
            return
        recipient = args
        recip_info = await conn.fetchrow('''SELECT * FROM cncusers WHERE lower(username) = $1;''',
                                         recipient.lower())
        if recip_info is None:
            await ctx.send(f"`{recipient}` does not appear to be registered.")
            return
        if userinfo['moves'] <= 0:
            await ctx.send("You do not have enough action points for that!")
            return
        if userinfo['trade_routes'][2] <= userinfo['trade_routes'][0]:
            await ctx.send("You do not have enough available trade routes to establish a new one.")
            return
        pending_route = await conn.fetchrow('''SELECT * FROM pending_interactions 
        WHERE sender_id = $1 AND recipient = $2 AND type = 'trade';''', author.id, recip_info['username'])
        if pending_route is not None:
            await ctx.send(f"You have a trade route offer already pending for {recip_info['username']}.")
            return
        relations = await conn.fetchrow(
            '''SELECT * FROM relations WHERE lower(name) = $1 AND lower(nation) = $2;''',
            userinfo['username'].lower(), recipient.lower())
        if relations['relation'] == 'war':
            await ctx.send("You cannot establish a trade route with a nation you are at war with!")
            return
        sender = userinfo['username']
        sender_id = author.id
        recipient = recip_info['username']
        recipient_id = recip_info['user_id']
        if sender == recipient:
            await ctx.send("You cannot send yourself a trade route.")
            return
        await conn.execute('''INSERT INTO pending_interactions (id, type, sender, sender_id, recipient,
                                recipient_id, terms) VALUES($1, $2, $3, $4, $5, $6, $7);''', ctx.message.id,
                           "trade", sender, sender_id, recipient, recipient_id, "Establish a Trade Route.")
        await conn.execute('''UPDATE cncusers SET moves = $1 WHERE user_id = $2;''', userinfo['moves'] - 1,
                           author.id)
        recipient_user = self.bot.get_user(recipient_id)
        await recipient_user.send(f"{sender} has sent an offer to establish a trade route with you. To accept or "
                                  f"reject, use `$cnc_interaction {ctx.message.id} [accept/reject]`.")
        await ctx.send(f"Trade offer sent to {recipient}!")

    # ---------------------Resource and Recruit Commands------------------------------

    @commands.command(usage="<nation name>", aliases=['cncb'], brief="Displays information about a nation's income")
    async def cnc_bank(self, ctx, *args):
        author = ctx.author
        conn = self.bot.pool
        nationname = ' '.join(args[:])
        if nationname == '':
            # if the nationame is left blank, the author id is used to find the nation information
            authorid = ctx.author.id
            registeredusers = await conn.fetch('''SELECT user_id FROM cncusers;''')
            registeredlist = list()
            # makes a list of the registered users
            for users in registeredusers:
                registeredlist.append(users["user_id"])
            # checks the author id against the list of registered users
            if authorid not in registeredlist:
                await ctx.send(f"{ctx.author} is not registered.")
                return
            # grabs the nation information
            userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', authorid)
            # creates a list of provinces  owned
            cities = userinfo['citylimit'][0]
            ports = userinfo['portlimit'][0]
            # creates the projected resource gain data
            manpower = userinfo['manpower']
            taxation = userinfo['taxation']
            military_upkeep = userinfo['military_upkeep']
            public_services = userinfo['public_services']
            base_gain = manpower * (taxation / 100)
            base_gain -= base_gain * (military_upkeep / 100)
            base_gain -= base_gain * (public_services / 100)
            # adds trade gain and subtracts troop upkeep
            initial_trade_value = 0
            total_troops = 0
            for p in userinfo['provinces_owned']:
                if p == 0:
                    continue
                p_info = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', p)
                if p_info['occupier_id'] != author.id:
                    continue
                total_troops += p_info['troops']
                # for every province, calculate local trade value
                province_value = p_info['trade_value']
                if p_info['city'] and p_info['port']:
                    province_value *= 1.6
                elif p_info['city']:
                    province_value *= 1.1
                elif p_info['port']:
                    province_value *= 1.5
                initial_trade_value += province_value
            trade_gain = 0
            trade_gain += initial_trade_value * (userinfo['trade_routes'][0] / 10)
            trade_gain += initial_trade_value * ((userinfo['trade_routes'][1] * 5) / 100)
            base_gain += trade_gain
            base_gain -= total_troops * 0.01
            # sends the embed
            bankembed = discord.Embed(title=f"{userinfo['username']} - War Chest",
                                      description="An overview of the resource status of a nation.")
            bankembed.add_field(name="Current Resources", value=f"\u03FE{userinfo['resources']:,}")
            bankembed.add_field(name="Total Projected Gain", value=f"\u03FE{math.ceil(base_gain):,}")
            bankembed.add_field(name="Trade Gain", value=f"\u03FE{math.ceil(trade_gain):,}")
            bankembed.add_field(name="Cities", value=cities)
            bankembed.add_field(name="Ports", value=ports)
            await ctx.send(embed=bankembed)
        else:
            registeredusers = await conn.fetch('''SELECT username FROM cncusers;''')
            # makes a list of the registered users
            registeredlist = list()
            for users in registeredusers:
                registeredlist.append(users["username"].lower())
            # checks the author id against the list of registered users
            if nationname.lower() not in registeredlist:
                await ctx.send(f"{nationname} does not appear to be registered.")
            # fetches specified nation data
            userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE lower(username) = $1''',
                                           nationname.lower())
            # creates a list of provinces  owned
            ownedprovinces = [p for p in userinfo['provinces_owned']]
            if 0 in ownedprovinces:
                ownedprovinces.remove(0)
            cities = userinfo['citylimit'][0]
            ports = userinfo['portlimit'][0]
            # creates the projected resource gain data
            manpower = userinfo['manpower']
            taxation = userinfo['taxation']
            military_upkeep = userinfo['military_upkeep']
            public_services = userinfo['public_services']
            base_gain = manpower * (taxation / 100)
            base_gain -= base_gain * (military_upkeep / 100)
            base_gain -= base_gain * (public_services / 100)
            # adds trade gain and subtracts troop upkeep
            initial_trade_value = 0
            total_troops = 0
            for p in userinfo['provinces_owned']:
                if p == 0:
                    continue
                p_info = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', p)
                total_troops += p_info['troops']
                province_value = p_info['trade_value']
                if p_info['city'] and p_info['port']:
                    province_value *= 1.6
                elif p_info['city']:
                    province_value *= 1.1
                elif p_info['port']:
                    province_value *= 1.5
                initial_trade_value += province_value
            trade_gain = 0
            trade_gain += initial_trade_value * (userinfo['trade_routes'][0] / 10)
            trade_gain += initial_trade_value * ((userinfo['trade_routes'][1] * 5) / 100)
            base_gain += trade_gain
            base_gain -= total_troops * 0.01
            # sends the embed
            bankembed = discord.Embed(title=f"{userinfo['username']} - War Chest",
                                      description="An overview of the resource status of a nation.")
            bankembed.add_field(name="Current Resources", value=f"\u03FE{userinfo['resources']:,}")
            bankembed.add_field(name="Current Gain", value=f"\u03FE{math.ceil(base_gain):,}")
            bankembed.add_field(name="Trade Gain", value=f"\u03FE{math.ceil(trade_gain):,}")
            bankembed.add_field(name="Cities", value=str(cities))
            bankembed.add_field(name="Ports", value=str(ports))
            await ctx.send(embed=bankembed)

    @commands.command(usage="[battalion amount] <province id>", aliases=['cncr'],
                      brief="Recruits a number of battalions")
    @commands.guild_only()
    async def cnc_recruit(self, ctx, ramount: int, location: int = None):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # fetches user info
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        nationname = userinfo['username']
        monies = userinfo['resources']
        manpower = ramount * 1000
        cost = ramount * 1000
        # reduces or increases cost based on military spending
        if userinfo['military_upkeep'] >= 10:
            cost_reduction = (userinfo['military_upkeep'] - 10) / 100
            cost *= 1 - cost_reduction
        else:
            cost_increase = (userinfo['military_upkeep'] - 10) / 100
            cost *= 1 + cost_increase
        # checks if the focus is military
        if userinfo['focus'] == "m":
            cost = round(cost * uniform(.89, .99))
        # if the nation does not have enough resources
        if monies < cost:
            await ctx.send(
                f"{nationname} does not have enough resources to purchase {ramount * 1000} troops at \u03FE{cost}.")
            return
        # if the nation does not have enough manpower
        elif manpower > userinfo['manpower']:
            await ctx.send(f"{nationname} does not have enough manpower to recruit {ramount * 1000} troops, "
                           f"lacking {-(userinfo['manpower'] - manpower)} manpower. ")
            return
        # if the location is not set
        if location is None:
            # updates all user information
            await conn.execute('''UPDATE cncusers SET undeployed = $1, manpower = $2 WHERE user_id = $3;''',
                               ((ramount * 1000) + (userinfo['undeployed'])),
                               userinfo['manpower'] - (ramount * 1000), author.id)
            await conn.execute('''UPDATE cncusers SET resources = $1 WHERE user_id = $2;''', (monies - cost),
                               author.id)
            await ctx.send(
                f"{nationname} has recruited {ramount * 1000} troops to their recruitment pool. "
                f"\u03FE{cost} have been spent.")
            return
        else:
            # fetches all province ids and makes them into a list
            province = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', location)
            if province is None:
                await ctx.send(f"`{location}` is not a valid province ID.")
                return
            # if the location is not owned by the user
            if province['owner_id'] != author.id and province['occuper_id'] != author.id:
                await ctx.send(
                    f"{nationname} does not own province #{location}. "
                    f"Please select a location that {nationname} owns.")
                return
        # updates all province and user information
        await conn.execute('''UPDATE cncusers SET manpower= $1 WHERE user_id = $2;''',
                           userinfo['manpower'] - manpower,
                           author.id)
        troops = await conn.fetchrow('''SELECT troops FROM provinces  WHERE id = $1;''', location)
        await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                           (troops['troops'] + (ramount * 1000)), location)
        await conn.execute('''UPDATE cncusers SET resources = $1 WHERE user_id = $2;''', (monies - cost),
                           author.id)
        await ctx.send(f"{nationname} has successfully deployed {ramount * 1000} to Province #{location}. "
                       f"\u03FE{cost} have been spent.")

    @commands.command(usage="[battalion amount]", brief="Recruits a number of battalions in all controlled provinces")
    @commands.guild_only()
    async def cnc_mass_recruit(self, ctx, amount: int):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # fetches all users
        allusers = await conn.fetch('''SELECT user_id FROM cncusers''')
        alluserids = list()
        for id in allusers:
            alluserids.append(id['user_id'])
        # checks if author is registered
        if author.id not in alluserids:
            await ctx.send(f"{author} not registered.")
            return
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        provinces = await conn.fetchrow('''SELECT provinces_owned FROM cncusers WHERE user_id = $1;''',
                                        author.id)
        provincelist = provinces['provinces_owned']
        if 0 in provincelist:
            provincelist.remove(0)
        amount *= 1000
        manpower = (amount) * len(provincelist)
        cost = (amount) * len(provincelist)
        # checks if the focus is military
        if userinfo['focus'] == "m":
            cost = round(cost * uniform(.89, .99))
        # checks for enough resources
        if userinfo['resources'] < cost:
            await ctx.send(
                f"{userinfo['username']} does not have enough resources to purchase {amount} for every "
                f"province at \u03FE{cost}.")
            return
        # checks for enough manpower
        elif manpower > userinfo['manpower']:
            await ctx.send(f"{userinfo['username']} does not have enough manpower to recruit {amount} troops"
                           f" for every province, lacking {-(userinfo['manpower'] - manpower)} manpower. ")
            return
        await conn.execute('''UPDATE cncusers SET manpower= $1 WHERE user_id = $2;''',
                           userinfo['manpower'] - manpower, author.id)
        for p in provincelist:
            troops = await conn.fetchrow('''SELECT troops FROM provinces  WHERE id = $1;''', p)
            await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                               (troops['troops'] + amount),
                               p)
        await ctx.send(
            f"{userinfo['username']} has succssfully deployed {amount} troops to all {len(provincelist)} provinces.")

    @commands.command(usage="[amount] [recipient nation]", brief="Sends money to a specified nation")
    @commands.guild_only()
    async def cnc_tribute(self, ctx, amount: int, recipient: str):
        if amount <= 0:
            raise commands.UserInputError
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # fetches all user ids
        allusers = await conn.fetch('''SELECT user_id, username FROM cncusers''')
        alluserids = list()
        allusernames = list()
        for id in allusers:
            alluserids.append(id['user_id'])
        for names in allusers:
            allusernames.append(names['username'].lower())
        # ensures author registration
        if author.id not in alluserids:
            await ctx.send(f"{author} not registered.")
            return
        # ensures recipient existance
        if recipient.lower() not in allusernames:
            await ctx.send(f"`{recipient}` not registered.")
            return
        # fetches user info
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1''', author.id)
        # ensures resource sufficiency
        if amount > userinfo['resources']:
            await ctx.send(f"{userinfo['username']} does not have \u03FE{amount}!")
            return
        # fetches recipient info
        recipientinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE lower(username) = $1;''',
                                            recipient.lower())
        # subtract resource amount and transfer to recipient
        await conn.execute('''UPDATE cncusers SET resources = $1 WHERE user_id = $2;''',
                           (userinfo['resources'] - amount), author.id)
        await conn.execute('''UPDATE cncusers SET resources = $1 WHERE username = $2;''',
                           (recipientinfo['resources'] + amount), recipientinfo['username'])
        await ctx.send(f"{userinfo['username']} has sent \u03FE{amount:,} to {recipientinfo['username']}.")
        return

    @commands.command(usage="[battalion amount] [recipient nation]",
                      brief="Sends a numer of undeployed battalions to a specified nation.")
    async def cnc_expedition(self, ctx, amount: int, recipient: str):
        # create connection
        author = ctx.author
        conn = self.bot.pool
        # if the amount is less than zero
        if amount < 0:
            raise commands.UserInputError
        amount *= 1000
        # fetch userinfo and check existence
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        if userinfo is None:
            await ctx.send("You are not registered!")
            return
        # fetch recipient info and check existence
        recip_info = await conn.fetchrow('''SELECT * FROM cncusers WHERE lower(username) = $1;''',
                                         recipient.lower())
        if recip_info is None:
            await ctx.send(f"{recipient} does not appear to be registered.")
            return
        # check if the user has enough troops to send the expedition
        undeployed = userinfo['undeployed']
        if amount > undeployed:
            await ctx.send(f"{userinfo['username']} does not have {amount} undeployed troops!")
            return
        # execute changes
        await conn.execute('''UPDATE cncusers SET undeployed = $1 WHERE user_id = $2;''',
                           undeployed - amount, author.id)
        await conn.execute('''UPDATE cncusers SET undeployed = $1 WHERE user_id = $2;''',
                           recip_info['undeployed'] + amount, recip_info['user_id'])
        await ctx.send(f"{userinfo['username']} has sent an expeditionary force of {amount:,} troops to "
                       f"{recip_info['username']}.")

    @commands.command(usage="[province id]", brief="Purchases a specified province")
    @commands.guild_only()
    async def cnc_purchase(self, ctx, provinceid: int):
        loop = asyncio.get_running_loop()
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # fetches all user ids
        allusers = await conn.fetch('''SELECT user_id FROM cncusers''')
        alluserids = list()
        for id in allusers:
            alluserids.append(id['user_id'])
        # ensures author registration
        if author.id not in alluserids:
            await ctx.send(f"{author} not registered.")
            return
        # fetches all province ids
        allprovinces = await conn.fetch('''SELECT id FROM provinces''')
        allids = list()
        for pid in allprovinces:
            allids.append(pid['id'])
        # ensures province validity
        if provinceid not in allids:
            await ctx.send(f"Location id `{provinceid}` is not a valid ID.")
            return
        # fetches province and user information
        provinceowner = await conn.fetchrow('''SELECT * FROM provinces  WHERE id = $1;''', provinceid)
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1''', author.id)
        cost = 3000 + provinceowner['trade_value']
        # checks for economic focus
        if userinfo['focus'] == "e":
            cost = 3000 * uniform(.89, .99)
        # ensures user disownership
        if provinceid in userinfo['provinces_owned']:
            await ctx.send(f"{userinfo['username']} already owns Province #{provinceid}")
            return
        # ensures province availability
        elif provinceowner['owner_id'] != 0:
            await ctx.send(f"Province #{provinceid} is already owned!")
            return
        # ensures province's coastal proximity
        elif provinceowner['coast'] is False:
            await ctx.send(f"Province #{provinceid} is not a coastal province and cannot be purchased!")
            return
        # ensures resource sufficiency
        elif userinfo['resources'] < cost:
            difference = cost - userinfo['resources']
            await ctx.send(
                f"{userinfo['username']} possesses {math.ceil(difference)} fewer credit resources than needed to buy a province.")
            return
        # ensures that the user has less than 3 provinces
        elif len(userinfo['provinces_owned']) >= 2:
            await ctx.send(f"{userinfo['username']} already controls enough provinces and is not eligible to "
                           f"purchase another.")
            return
        else:
            # fetches necessary ownership information
            provincesowned = await conn.fetchrow('''SELECT provinces_owned FROM cncusers WHERE user_id = $1;''',
                                                 author.id)
            ownedlist = provincesowned['provinces_owned']
            if ownedlist is None:
                ownedlist = list()
            ownedlist.append(provinceid)
            # updates all relevant information
            await conn.execute('''UPDATE cncusers SET provinces_owned = $1 WHERE user_id = $2;''', ownedlist,
                               author.id)
            await conn.execute('''UPDATE provinces  SET owner = $1, owner_id = $2 WHERE id = $3;''',
                               userinfo['username'], author.id, provinceid)
            await conn.execute('''UPDATE cncusers SET resources = $1 WHERE user_id = $2;''',
                               (userinfo['resources'] - cost), author.id)
            await ctx.send(f"{userinfo['username']} has purchased Province #{provinceid} successfully!")
            await loop.run_in_executor(None, self.map_color, provinceid, provinceowner['cord'][0:2],
                                       userinfo['usercolor'])
            return

    @commands.command(usage="[province id] [structure (fort, port, city, capital, move_capital)]",
                      brief="Constructs a building in a specified province")
    @commands.guild_only()
    async def cnc_construct(self, ctx, provinceid: int, structure: str):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # fetches all user ids
        allusers = await conn.fetch('''SELECT user_id FROM cncusers''')
        alluserids = list()
        for id in allusers:
            alluserids.append(id['user_id'])
        # ensures author registration
        if author.id not in alluserids:
            await ctx.send(f"{author} not registered.")
            return
        # fetches all province ids
        allprovinces = await conn.fetch('''SELECT id FROM provinces''')
        allids = list()
        for pid in allprovinces:
            allids.append(pid['id'])
        # ensures province validity
        if provinceid not in allids:
            await ctx.send(f"Location id `{provinceid}` is not a valid ID.")
            return
        # fetches province and user information
        provinceinfo = await conn.fetchrow('''SELECT * FROM provinces  WHERE id = $1;''', provinceid)
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1''', author.id)
        # ensures user disownership
        if provinceid not in userinfo['provinces_owned']:
            await ctx.send(f"{userinfo['username']} does not own Province #{provinceid}!")
            return
        if structure.lower() not in ['fort', 'port', 'city', 'capital', 'move_capital']:
            raise commands.UserInputError
        if structure.lower() == 'port':
            pcost = 10000
            if provinceinfo['coast'] is False:
                await ctx.send(f"Province #{provinceid} is not a coastal province.")
                return
            elif userinfo['portlimit'][0] == userinfo['portlimit'][1]:
                await ctx.send(f"{userinfo['username']} has reached its port building limit.")
                return
            if userinfo['focus'] == "e":
                pcost = math.ceil(10000 * uniform(.89, .99))
            if userinfo['resources'] < pcost:
                difference = pcost - userinfo['resources']
                await ctx.send(f"{userinfo['username']} does not have enough credit resources to build a port."
                               f"\n**Resource Deficit:** \u03FE{math.ceil(difference)}")
                return
            elif provinceinfo['port'] is True:
                await ctx.send(f"Province #{provinceid} already has a port constructed!")
                return
            elif provinceinfo['terrain'] == 5:
                await ctx.send("It is impossible to build a port on a mountain!")
                return
            else:
                port_limit = userinfo['portlimit']
                port_limit[0] += 1
                await conn.execute('''UPDATE provinces  SET port = TRUE WHERE id = $1;''', provinceid)
                await conn.execute('''UPDATE cncusers SET resources = $1, portlimit = $2 WHERE user_id = $3;''',
                                   (userinfo['resources'] - pcost), port_limit, author.id)
                await ctx.send(
                    f"{userinfo['username']} successfully constructed a port in province #{provinceid}.")
                return
        if structure.lower() == 'city':
            ccost = 25000
            if userinfo['resources'] < ccost:
                difference = ccost - userinfo['resources']
                await ctx.send(f"{userinfo['username']} does not have enough credit resources to build a city."
                               f"\n**Resource Deficit:** \u03FE{math.ceil(difference)}")
                return
            elif userinfo['citylimit'][0] == userinfo['citylimit'][1]:
                await ctx.send(f"{userinfo['username']} has reached its city building limit.")
                return
            elif provinceinfo['city'] is True:
                await ctx.send(f"Province #{provinceid} already has a city constructed!")
                return
            elif provinceinfo['terrain'] == 5:
                await ctx.send("It is impossible to build a port on a mountain!")
                return
            else:
                city_limit = userinfo['citylimit']
                city_limit[0] += 1
                await conn.execute('''UPDATE provinces  SET city = TRUE WHERE id = $1;''',
                                   provinceid)
                await conn.execute('''UPDATE cncusers SET resources = $1, citylimit = $2 WHERE user_id = $3;''',
                                   (userinfo['resources'] - ccost), city_limit, author.id)
                await ctx.send(
                    f"{userinfo['username']} successfully constructed a city in province #{provinceid}.")
                return
        if structure.lower() == 'fort':
            fcost = 15000
            if userinfo['focus'] == "s":
                fcost = math.ceil(15000 * uniform(.89, .99))
            if userinfo['resources'] < fcost:
                difference = fcost - userinfo['resources']
                await ctx.send(f"{userinfo['username']} does not have enough credit resources to build a fort."
                               f"\n**Resource Deficit:** \u03FE{math.ceil(difference)}")
                return
            elif userinfo['fortlimit'][0] == userinfo['fortlimit'][1]:
                await ctx.send(f"{userinfo['username']} has reached its fort building limit.")
                return
            elif provinceinfo['fort'] is True:
                await ctx.send(f"Province #{provinceid} already has a fort constructed!")
                return
            elif provinceinfo['terrain'] == 5:
                await ctx.send("Mountainous terrains are impossible to build forts on!")
                return
            else:
                fortlimit = userinfo['fortlimit']
                fortlimit[0] += 1
                await conn.execute('''UPDATE provinces  SET fort = TRUE WHERE id = $1;''', provinceid)
                await conn.execute('''UPDATE cncusers SET resources = $1, fortlimit = $2 WHERE user_id = $3;''',
                                   (userinfo['resources'] - fcost), fortlimit, author.id)
                await ctx.send(
                    f"{userinfo['username']} successfully constructed a fort in province #{provinceid}.")
                return
        if structure.lower() == 'capital':
            if userinfo['capital'] != 0:
                await ctx.send(f"{userinfo['username']} already has a capital in Province #{userinfo['capital']}.")
                return
            if userinfo['resources'] < 50000:
                difference = 50000 - userinfo['resources']
                await ctx.send(f"{userinfo['username']} does not have enough credit resources to build a capital."
                               f"\n**Resource Deficit:** \u03FE{math.ceil(difference)}")
                return
            if provinceinfo['city'] is False:
                await ctx.send("A capital can only be built in a province with an existing city.")
                return
            await conn.execute('''UPDATE cncusers SET capital = $1, resources = $2 WHERE user_id = $3;''',
                               provinceid, userinfo['resources'] - 50000, author.id)
            await ctx.send(f"{userinfo['username']} successfully constructed a capital in province # {provinceid}.")
            return
        if structure.lower() == 'move_capital':
            if userinfo['capital'] == provinceid:
                await ctx.send(
                    f"{userinfo['username']} already has the capital in Province #{userinfo['capital']}.")
                return
            elif userinfo['capital'] == 0:
                await ctx.send(f"{userinfo['username']} has not constructed a capital.")
                return
            elif userinfo['resources'] < 25000:
                difference = 25000 - userinfo['resources']
                await ctx.send(f"{userinfo['username']} does not have enough credit resources to move the capital."
                               f"\n**Resource Deficit:** \u03FE{math.ceil(difference)}")
                return
            elif provinceinfo['city'] is False:
                await ctx.send("A capital can only be moved to a province with an existing city.")
                return
            turn = await conn.fetchrow('''SELECT data_value FROM cnc_data WHERE data_name = 'turn';''')
            if userinfo['capital_move'] == turn['data_value']:
                await ctx.send("You have already moved your capital this turn and cannot move it again.")
                return
            await conn.execute('''UPDATE cncusers SET capital = $1, resources = $2, capital_move = $3 
            WHERE user_id = $4;''',
                               provinceid, userinfo['resources'] - 25000, turn['data_valye'], author.id)
            await ctx.send(f"Capital successfully moved to province #{provinceid}.")
            return

    @commands.command(usage="[rate changing (tax, military, services; t,m,s)] [whole number rate]",
                      brief="Changes the rate of the given spending rate.")
    async def cnc_change_rate(self, ctx, changed: str, rate: int):
        # defines author and connection pool
        author = ctx.author
        conn = self.bot.pool
        # fetches user information
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        if userinfo is None:
            await ctx.send(f"{author} does not appear to be registered.")
            return
        if changed not in ['tax', 'military', 'services', 't', 'm', 's']:
            raise commands.UserInputError
        if rate < 0:
            raise commands.UserInputError
        if changed == 'tax' or changed == 't':
            changed = 'taxation'
            if rate > 25:
                await ctx.send("The maximum tax rate is 25%.")
                return
            current_rate = userinfo[changed]
            if current_rate == rate:
                await ctx.send(f"Your rate is already {rate}%!")
                return
            await conn.execute('''UPDATE cncusers SET taxation = $1 WHERE user_id = $2;''', rate, author.id)
        if changed == 'military' or changed == 'm':
            changed = 'military_upkeep'
            if rate > 30:
                await ctx.send("The maximum military upkeep rate is 30%.")
                return
            current_rate = userinfo[changed]
            if current_rate == rate:
                await ctx.send(f"Your rate is already {rate}%!")
                return
            await conn.execute('''UPDATE cncusers SET military_upkeep = $1 WHERE user_id = $2;''', rate, author.id)
        if changed == 'services' or changed == 's':
            changed = 'public_services'
            if rate > 50:
                await ctx.send("The maximum public services rate is 50%.")
                return
            current_rate = userinfo[changed]
            if current_rate == rate:
                await ctx.send(f"Your rate is already {rate}%!")
                return
            await conn.execute('''UPDATE cncusers SET public_services = $1 WHERE user_id = $2;''', rate, author.id)
        changed = changed.replace("_", " ")
        await ctx.send(f"{changed.title()} rate changed from {current_rate}% to {rate}% successfully!")

    # -------------------Movement Commands----------------------------

    @commands.command(usage="[province id] <amount>", aliases=['cncw'],
                      brief="Removes a number of troops from a specified province")
    @commands.guild_only()
    async def cnc_withdraw(self, ctx, province: int, amount: int = None):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # fetches all user ids
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        # ensures author registration
        if userinfo is None:
            await ctx.send(f"{author} not registered.")
            return
        # fetches all province ids
        provinceinfo = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', province)
        if provinceinfo is None:
            await ctx.send(f"`{province}` is not a valid ID.")
        if amount is not None:
            if amount > provinceinfo['troops']:
                await ctx.send(f"There are not {amount:,} troops in province #{province}.")
                return
        if provinceinfo['owner_id'] != author.id and provinceinfo['occupier_id'] != author.id:
            await ctx.send("You do not own or occupy that province.")
            return
        # ensures the amount is in the province
        if amount is None:
            amount = provinceinfo['troops']
        await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                           (provinceinfo['troops'] - amount),
                           province)
        await conn.execute('''UPDATE cncusers SET undeployed = $1 WHERE user_id = $2;''',
                           (userinfo['undeployed'] + amount), author.id)
        await ctx.send(
            f"{amount:,} troops removed from province #{province} and returned to the undeployed stockpile.")
        return

    @commands.command(brief="Removes all troops from all provinces")
    @commands.guild_only()
    async def cnc_withdraw_all(self, ctx):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # fetches all user ids
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        # ensures author registration
        if userinfo is None:
            await ctx.send(f"{author} not registered.")
            return
        withdrawn_raw = await conn.fetchrow('''SELECT sum(troops::int) FROM provinces 
        WHERE occupier_id = $1 AND owner_id = $1;''',
                                            author.id)
        withdrawn = withdrawn_raw['sum']
        await conn.execute('''UPDATE provinces SET troops = 0 WHERE occupier_id = $1;''',
                           author.id)
        await conn.execute('''UPDATE cncusers SET undeployed = $1 WHERE user_id = $2;''',
                           (userinfo['undeployed'] + withdrawn), author.id)
        await ctx.send(f"{withdrawn:,} troops removed from all owned or occupied provinces "
                       f"and returned to the undeployed stockpile.")
        return

    @commands.command(usage="[amount]", brief="Deploys a given number of troops to all provinces")
    @commands.guild_only()
    async def cnc_mass_deploy(self, ctx, amount: int):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # fetches all user ids
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        # ensures author registration
        if userinfo is None:
            await ctx.send(f"{author} not registered.")
            return
        occupied_provinces = await conn.fetch('''SELECT * FROM provinces WHERE occupier_id = $1;''', author.id)
        total_deployed = amount * len(occupied_provinces)
        if amount <= 0:
            raise commands.UserInputError
        if total_deployed > userinfo['undeployed']:
            await ctx.send(f"{userinfo['username']} does not have enough undeployed troops to deploy {amount} troops "
                           f"to all {len(occupied_provinces)} "
                           f"owned and occupied provinces.")
            return
        await conn.execute('''UPDATE cncusers SET undeployed = $1 WHERE user_id = $2;''',
                           userinfo['undeployed'] - total_deployed, author.id)
        for p in occupied_provinces:
            p_info = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', p['id'])
            troops = p_info['troops']
            await conn.execute('''UPDATE provinces SET troops = $1 WHERE id = $2;''', troops + amount, p['id'])
        await ctx.send(f"{amount:,} troops deployed to all {len(userinfo['provinces_owned'])} provinces.")
        return

    @commands.command(usage="[stationed target id] [target province id] [amount]", aliases=['cncm'],
                      brief="Moves troops from one province to another")
    @commands.guild_only()
    async def cnc_move(self, ctx, stationed: int, target: int, amount: int):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # fetches all user ids
        allusers = await conn.fetch('''SELECT user_id FROM cncusers''')
        alluserids = list()
        for id in allusers:
            alluserids.append(id['user_id'])
        # ensures author registration
        if author.id not in alluserids:
            await ctx.send(f"{author} not registered.")
            return
        # fetches all province ids
        allprovinces = await conn.fetch('''SELECT id FROM provinces''')
        allids = list()
        for pid in allprovinces:
            allids.append(pid['id'])
        # ensures province existence
        if target not in allids:
            await ctx.send(f"Location id `{target}` is not a valid ID.")
            return
        elif stationed not in allids:
            await ctx.send(f"Location id `{stationed}` is not a valid ID.")
            return
        # fetches target and stationed information
        targetowner = await conn.fetchrow('''SELECT * FROM provinces  WHERE id = $1;''', target)
        stationedowner = await conn.fetchrow('''SELECT * FROM provinces  WHERE id = $1;''', stationed)
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1''', author.id)
        # ensures province ownership
        if targetowner['occupier_id'] != author.id:
            await ctx.send(f"{userinfo['username']} does not occupy Province #{target}!")
            return
        elif stationedowner['occupier_id'] != author.id:
            await ctx.send(f"{userinfo['username']} does not occupy Province #{stationed}!")
            return
        # gathers specific province information
        targetinfo = await conn.fetchrow('''SELECT * FROM provinces  WHERE id = $1;''', target)
        stationedinfo = await conn.fetchrow('''SELECT owner_id, coast, troops FROM provinces  WHERE id = $1;''',
                                            stationed)
        # ensures bordering
        if (targetinfo['coast'] is False) or (stationedinfo['coast'] is False):
            if stationed not in targetinfo['bordering']:
                await ctx.send(f"Province #{stationed} does not border province #{target}!")
                return
        # ensures sufficient troops reside in province
        if stationedinfo['troops'] < amount:
            await ctx.send(f"Province #{stationed} does not contain {amount} troops!")
            return
        await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                           (targetinfo['troops'] + amount),
                           target)
        await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                           (stationedinfo['troops'] - amount),
                           stationed)
        await ctx.send(f"{amount:,} troops moved to Province #{target} successfully!")

    @commands.command(usage="[stationed province] [target province] [attack force]", aliases=['cnca'],
                      brief="Attacks from one province to another")
    @commands.guild_only()
    async def cnc_attack(self, ctx, stationed: int, target: int, force: int = None):
        # connects to the database
        conn = self.bot.pool
        loop = asyncio.get_running_loop()
        author = ctx.author
        # fetches all user ids
        allusers = await conn.fetch('''SELECT user_id FROM cncusers;''')
        alluserids = list()
        for id in allusers:
            alluserids.append(id['user_id'])
        # ensures author registration
        if author.id not in alluserids:
            await ctx.send(f"{author} not registered.")
            return
        # fetches all province ids
        allprovinces = await conn.fetch('''SELECT id FROM provinces;''')
        allids = list()
        for pid in allprovinces:
            allids.append(pid['id'])
        # ensures province existence
        if target not in allids:
            await ctx.send(f"Location id `{target}` is not a valid ID.")
            return
        elif stationed not in allids:
            await ctx.send(f"Location id `{stationed}` is not a valid ID.")
            return
        # fetches target and stationed information
        targetownerid = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', target)
        stationedownerid = await conn.fetchrow('''SELECT * FROM provinces  WHERE id = $1;''', stationed)
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        # checks to make sure the user has enough moves
        if userinfo['moves'] <= 0:
            await ctx.send(f"{userinfo['username']} does not have any movement points left!")
            return
        # checks ownership conflicts
        if stationedownerid['occupier_id'] != author.id:
            await ctx.send(f"{userinfo['username']} does not occupy Province #{stationed}!")
            return
        if targetownerid['occupier_id'] == author.id:
            await ctx.send(f"You cannot attack a province you already own or occupy!")
            return
        targetinfo = await conn.fetchrow('''SELECT * FROM provinces  WHERE id = $1;''', target)
        stationedinfo = await conn.fetchrow('''SELECT * FROM provinces  WHERE id = $1;''',
                                            stationed)
        if force is None:
            force = stationedinfo['troops']
        if force == 0:
            await ctx.send("You cannot attack with 0 troops.")
            return
        if targetinfo['owner_id'] != 0:
            defenderinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''',
                                               targetinfo['occupier_id'])
            if defenderinfo is None:
                raise Exception("Defenderinfo fetching broken")
        # ensures valid conflict
        if targetinfo['owner_id'] != 0:
            # if the province is occupied and the attacker is the owner, check for a valid conflict
            if targetinfo['owner_id'] != targetinfo['occupier_id'] and targetinfo['owner_id'] == author.id:
                war = await conn.fetchrow('''SELECT relation FROM relations WHERE name = $1 and nation = $2;''',
                                          userinfo['username'], targetinfo['occupier'])
                if war['relation'] != 'war':
                    await ctx.send("You cannot attack a province occupied by a nation you are not at war with or"
                                   "owned by a nation you are not at war with.")
                    return
            else:
                war = await conn.fetchrow('''SELECT relation FROM relations WHERE name = $1 and nation = $2;''',
                                          userinfo['username'], defenderinfo['username'])
                if war['relation'] != 'war':
                    await ctx.send("You cannot attack a province owned by a nation you are not at war with.")
                    return
        # ensures bordering
        if (targetinfo['coast'] is False) and (stationedinfo['coast'] is False):
            if stationed not in targetinfo['bordering']:
                await ctx.send(f"Province #{stationed} does not border province #{target}!")
                return
        # ensures sufficient troops reside in province
        if stationedinfo['troops'] < force:
            await ctx.send(f"Province #{stationed} does not contain {force} troops!")
            return
        # calculates crossing fee if the provinces do not border
        if (targetinfo['coast'] is True) and (stationedinfo['coast'] is True) and (
                stationed not in targetinfo['bordering']):
            # checks for sufficient resources
            crossingfee = math.ceil(force * .50)
            if userinfo['focus'] == 'm':
                crossingfee = math.ceil(force * .40)
            if crossingfee > userinfo['resources']:
                await ctx.send(
                    f"{userinfo['username']} does not have enough resources to cross with {force} troops!\n"
                    f"**Resources Required:** \u03FE{math.ceil(force * .05)}")
                return
            if stationedinfo['port'] is True:
                crossingfee *= .5
                math.ceil(crossingfee)
        else:
            crossingfee = 0
        # checks for terrain/defensive modifiers
        river = targetinfo['river']
        fort = targetinfo['fort']
        city = targetinfo['city']
        # if there are no troops in the target province
        if targetinfo['troops'] == 0:
            # fetches necessary ownership information
            provincesowned = await conn.fetchrow('''SELECT provinces_owned FROM cncusers WHERE user_id = $1;''',
                                                 author.id)
            ownedlist = provincesowned['provinces_owned']
            if ownedlist is None:
                ownedlist = list()
            ownedlist.append(target)
            # execute all data changes
            await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                               (targetinfo['troops'] + force), target)
            await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                               (stationedinfo['troops'] - force), stationed)
            if targetinfo['owner_id'] == 0:
                await conn.execute('''UPDATE provinces  SET owner_id = $1, owner = $2, occupier = $2, occupier_id = $1
                 WHERE id = $3;''', author.id, userinfo['username'], target)
                await conn.execute(
                    '''UPDATE cncusers SET provinces_owned = $1, moves = $2, resources = $3 WHERE user_id = $4;''',
                    ownedlist, (userinfo['moves'] - 1), (userinfo['resources'] - crossingfee), author.id)
                owner = "the natives"
                await ctx.send(
                    f"Province #{target} is undefended! It has been overrun by {userinfo['username']} with {force}"
                    f" troops, seizing the province from {owner}!")
                await loop.run_in_executor(None, self.map_color, target, targetinfo['cord'][0:2],
                                           userinfo['usercolor'])
            # if there is an owner, all relevant information updated
            if targetinfo['owner_id'] != 0:
                await conn.execute('''UPDATE provinces SET occupier_id = $1, occupier = $2 WHERE id = $3;''', author.id,
                                   userinfo['username'], target)
                await conn.execute(
                    '''UPDATE cncusers SET moves = $1, resources = $2 WHERE user_id = $3;''',
                    (userinfo['moves'] - 1), (userinfo['resources'] - crossingfee), author.id)
                owner = targetinfo['occupier']
                await loop.run_in_executor(None, self.occupy_color, target, targetinfo['cord'][0:2],
                                           userinfo['usercolor'], defenderinfo['usercolor'])
                await ctx.send(
                    f"Province #{target} is undefended! It has been overrun by {userinfo['username']} with {force}"
                    f" troops, seizing the province from {owner}!")
            return
        # if there are any stationed troops
        else:
            # fetch proper information
            defending_troops = int(targetinfo['troops'])
            attacking_troops = force
            terrain_id = targetinfo['terrain']
            terrain = await conn.fetchrow('''SELECT name FROM terrains WHERE id = $1;''', terrain_id)
            terrain = terrain['name']
            battle = calculations(attacking_troops, defending_troops, terrain_id, ctx)
            # simulate battle
            await battle.Casualties()
            # if the defenders win the battle roll, no retreat
            if battle.defenseroll >= battle.attackroll:
                victor = "The defenders are victorious!"
                advance = False
            # if the attackers win the battle roll, retreat
            else:
                victor = "The attackers are victorious!"
                advance = True
            # create battleembed object
            battleembed = discord.Embed(title=f"Battle of {targetinfo['name']} (Province #{target})",
                                        description=f"Attack from Province #{stationed} by {userinfo['username']} on Province #{target} with {force} troops.",
                                        color=discord.Color.red())
            battleembed.add_field(name="Attacking Force", value=str(attacking_troops))
            battleembed.add_field(name="Defending Force", value=str(defending_troops))
            battleembed.add_field(name="Terrain", value=terrain)
            battleembed.add_field(name="Outcome", value=str(victor), inline=False)
            battleembed.add_field(name="Attacking Casualties", value=str(battle.AttackingCasualties))
            battleembed.add_field(name="Defending Casualties", value=str(battle.DefendingCasualties))
            battleembed.add_field(name="Crossing Fee", value=str(crossingfee), inline=False)
            battleembed.add_field(name="Remaining Attacking Force", value=str(battle.RemainingAttackingArmy))
            battleembed.add_field(name="Remaining Defending Force", value=str(battle.RemainingDefendingArmy))
            battleembed.set_thumbnail(url="https://i.ibb.co/gTpHmgq/Command-Conquest-symbol.png")
            deaths = await conn.fetchrow('''SELECT data_value FROM cnc_data WHERE data_name = 'deaths';''')
            await conn.execute('''UPDATE cnc_data SET data_value = $1 WHERE data_name = 'deaths';''',
                               deaths['data_value'] + battle.AttackingCasualties + battle.DefendingCasualties)
            # if there is a river battle to be fought
            if advance is True:
                # if there is a river, the attackers must ford the river
                if river is True:
                    # if there is no owner
                    if targetinfo['owner_id'] == 0:
                        owner = "the Natives"
                    else:
                        owner = targetinfo['owner']
                    # sets the relevant battle information
                    battleembed.set_footer(text=f"{userinfo['username']} has successfully defeated the initial "
                                                f"defense. Province #{target} has a river, which must be forded. React with"
                                                f" \U00002694 to attack again or \U0001f3f3 to retreat.")
                    # updates the relevant information
                    await conn.execute(
                        '''UPDATE cncusers SET resources = $1 WHERE user_id = $2;''',
                        (userinfo['resources'] - crossingfee), author.id)
                    await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                       (stationedinfo['troops'] - battle.AttackingCasualties), stationed)
                    await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                       (targetinfo['troops'] - battle.DefendingCasualties), target)
                    deaths = await conn.fetchrow('''SELECT data_value FROM cnc_data WHERE data_name = 'deaths';''')
                    await conn.execute('''UPDATE cnc_data SET data_value = $1 WHERE data_name = 'deaths';''',
                                       deaths[
                                           'data_value'] + battle.AttackingCasualties + battle.DefendingCasualties)
                    # sends the embed object and adds the reactions
                    battlenotif = await ctx.send(embed=battleembed)
                    await battlenotif.add_reaction("\U00002694")
                    await battlenotif.add_reaction("\U0001f3f3")
                    try:
                        # the check for the emojis
                        def fordcheck(reaction, user):
                            return user == ctx.message.author and str(reaction.emoji)

                        # waits for the correct emoji response
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=180, check=fordcheck)
                        # if the reaction is the attack, the attack commences and the footer is updated
                        if str(reaction.emoji) == "\U00002694":
                            await battlenotif.clear_reactions()
                            battleembed.set_footer(text=f"The attack continues!")
                            await battlenotif.edit(embed=battleembed)
                            defending_troops = battle.RemainingDefendingArmy
                            attacking_troops = battle.RemainingAttackingArmy
                            terrain_id = 3
                            try:
                                battle = calculations(attacking_troops, defending_troops, terrain_id, ctx)
                            except Exception:
                                self.bot.logger.warning(traceback.format_exc())
                            # simulate battle
                            await battle.Casualties()
                            # if the defenders win the battle roll, no retreat
                            if battle.defenseroll >= battle.attackroll:
                                victor = "The defenders are victorious!"
                                advance = False
                            # if the attackers win the battle roll, retreat
                            elif battle.attackroll > battle.defenseroll:
                                victor = "The attackers are victorious!"
                                advance = True
                            # create battleembed object
                            battleembed = discord.Embed(
                                title=f"Battle of {targetinfo['name']} (Province #{target})",
                                description=f"Attack from Province #{stationed} by {userinfo['username']} on Province #{target} with {force} troops.",
                                color=discord.Color.red())
                            battleembed.add_field(name="Attacking Force", value=str(attacking_troops))
                            battleembed.add_field(name="Defending Force", value=defending_troops)
                            battleembed.add_field(name="Terrain", value="River")
                            battleembed.add_field(name="Outcome", value=victor, inline=False)
                            battleembed.add_field(name="Attacking Casualties",
                                                  value=str(battle.AttackingCasualties))
                            battleembed.add_field(name="Defending Casualties",
                                                  value=str(battle.DefendingCasualties))
                            battleembed.add_field(name="Crossing Fee", value=str(crossingfee), inline=False)
                            battleembed.add_field(name="Remaining Attacking Force",
                                                  value=str(battle.RemainingAttackingArmy))
                            battleembed.add_field(name="Remaining Defending Force",
                                                  value=str(battle.RemainingDefendingArmy))
                            battleembed.set_thumbnail(url="https://i.ibb.co/gTpHmgq/Command-Conquest-symbol.png")
                            deaths = await conn.fetchrow(
                                '''SELECT data_value FROM cnc_data WHERE data_name = 'deaths';''')
                            await conn.execute(
                                '''UPDATE cnc_data SET data_value = $1 WHERE data_name = 'deaths';''',
                                deaths['data_value'] + battle.AttackingCasualties + battle.DefendingCasualties)
                        # if the reaction is retreat, the attack does not continue
                        if str(reaction.emoji) == "\U0001f3f3":
                            await battlenotif.clear_reactions()
                            battleembed.set_footer(
                                text=f"The attacker retreated from the ford and the province has been "
                                     f"returned to the control of {owner}.")
                            await battlenotif.edit(embed=battleembed)
                            return
                        # default result is retreat on the timeout error
                    except asyncio.TimeoutError:
                        await battlenotif.clear_reactions()
                        battleembed.set_footer(
                            text=f"The attacker retreated from the ford and the province has been "
                                 f"returned to the control of {owner}.")
                        await battlenotif.edit(embed=battleembed)
                        return
            if advance is True:
                # if there is a fort, the attackers must attack the fort
                if fort is True:
                    # if there is no owner
                    if targetinfo['owner_id'] == 0:
                        owner = "the Natives"
                    else:
                        owner = targetinfo['owner']
                    # sets the relevant battle information
                    battleembed.set_footer(text=f"{userinfo['username']} has successfully defeated the initial "
                                                f"defense. Province #{target} has a fort, which must be captured. "
                                                f"React with \U00002694 to attack again or \U0001f3f3 to retreat.")
                    # updates the relevant information
                    await conn.execute(
                        '''UPDATE cncusers SET resources = $1 WHERE user_id = $2;''',
                        (userinfo['resources'] - crossingfee), author.id)
                    await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                       (stationedinfo['troops'] - battle.AttackingCasualties), stationed)
                    await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                       (targetinfo['troops'] - battle.DefendingCasualties), target)
                    deaths = await conn.fetchrow('''SELECT data_value FROM cnc_data WHERE data_name = 'deaths';''')
                    await conn.execute('''UPDATE cnc_data SET data_value = $1 WHERE data_name = 'deaths';''',
                                       deaths[
                                           'data_value'] + battle.AttackingCasualties + battle.DefendingCasualties)
                    # sends the embed object and adds the reactions
                    battlenotif = await ctx.send(embed=battleembed)
                    await battlenotif.add_reaction("\U00002694")
                    await battlenotif.add_reaction("\U0001f3f3")

                    # the check for the emojis
                    def siegecheck(reaction, user):
                        return user == ctx.message.author and str(reaction.emoji)

                    # waits for the correct emoji response
                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=180, check=siegecheck)
                        # if the reaction is the attack, the attack commences and the footer is updated
                        if str(reaction.emoji) == "\U00002694":
                            await battlenotif.clear_reactions()
                            battleembed.set_footer(text=f"The attack continues!")
                            await battlenotif.edit(embed=battleembed)
                            defending_troops = battle.RemainingDefendingArmy
                            attacking_troops = battle.RemainingAttackingArmy
                            terrain_id = 8
                            battle = calculations(attacking_troops, defending_troops, terrain_id, ctx)
                            # simulate battle
                            await battle.Casualties()
                            # if the defenders win the battle roll, no retreat
                            if battle.defenseroll >= battle.attackroll:
                                victor = "The defenders are victorious!"
                                advance = False
                            # if the attackers win the battle roll, retreat
                            elif battle.attackroll > battle.defenseroll:
                                victor = "The attackers are victorious!"
                                advance = True
                            # create battleembed object
                            battleembed = discord.Embed(title=f"Siege of Province #{target}",
                                                        description=f"Attack from Province #{stationed} by {userinfo['username']} on the fort in Province #{target} with {force} troops.",
                                                        color=discord.Color.red())
                            battleembed.add_field(name="Attacking Force", value=str(attacking_troops))
                            battleembed.add_field(name="Defending Force", value=defending_troops)
                            battleembed.add_field(name="Terrain", value="Fort")
                            battleembed.add_field(name="Outcome", value=victor, inline=False)
                            battleembed.add_field(name="Attacking Casualties",
                                                  value=str(battle.AttackingCasualties))
                            battleembed.add_field(name="Defending Casualties",
                                                  value=str(battle.DefendingCasualties))
                            battleembed.add_field(name="Crossing Fee", value=str(crossingfee), inline=False)
                            battleembed.add_field(name="Remaining Attacking Force",
                                                  value=str(battle.RemainingAttackingArmy))
                            battleembed.add_field(name="Remaining Defending Force",
                                                  value=str(battle.RemainingDefendingArmy))
                            battleembed.set_thumbnail(url="https://i.ibb.co/gTpHmgq/Command-Conquest-symbol.png")
                            deaths = await conn.fetchrow(
                                '''SELECT data_value FROM cnc_data WHERE data_name = 'deaths';''')
                            await conn.execute(
                                '''UPDATE cnc_data SET data_value = $1 WHERE data_name = 'deaths';''',
                                deaths['data_value'] + battle.AttackingCasualties + battle.DefendingCasualties)
                        # if the reaction is retreat, the attack does not continue
                        if str(reaction.emoji) == "\U0001f3f3":
                            await battlenotif.clear_reactions()
                            battleembed.set_footer(
                                text=f"The attacker retreated from the fort and the province has "
                                     f"been returned to the control of {owner}.")
                            await battlenotif.edit(embed=battleembed)
                            return
                    # default result is retreat on the timeout error
                    except asyncio.TimeoutError:
                        await battlenotif.clear_reactions()
                        battleembed.set_footer(
                            text=f"The attacker retreated from the fort and the province has been "
                                 f"returned to the control of {owner}.")
                        await battlenotif.edit(embed=battleembed)
                        return
            if advance is True:
                # if there is a city, the attackers must sack the city
                if city is True:
                    # if there is no owner
                    if targetinfo['owner_id'] == 0:
                        owner = "the Natives"
                    else:
                        owner = targetinfo['owner']
                    # sets the relevant battle information
                    battleembed.set_footer(text=f"{userinfo['username']} has successfully defeated the initial "
                                                f"defense. Province #{target} has a city, which must be captured. "
                                                f"React with \U00002694 to attack again or \U0001f3f3 to retreat.")
                    # updates the relevant information
                    await conn.execute(
                        '''UPDATE cncusers SET resources = $1 WHERE user_id = $2;''',
                        (userinfo['resources'] - crossingfee), author.id)
                    await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                       (stationedinfo['troops'] - battle.AttackingCasualties), stationed)
                    await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                       (targetinfo['troops'] - battle.DefendingCasualties), target)
                    # sends the embed object and adds the reactions
                    battlenotif = await ctx.send(embed=battleembed)
                    await battlenotif.add_reaction("\U00002694")
                    await battlenotif.add_reaction("\U0001f3f3")

                    # the check for the emojis
                    def sackcheck(reaction, user):
                        return user == ctx.message.author and str(reaction.emoji)

                    # waits for the correct emoji response
                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=180, check=sackcheck)
                        # if the reaction is the attack, the attack commences and the footer is updated
                        if str(reaction.emoji) == "\U00002694":
                            await battlenotif.clear_reactions()
                            battleembed.set_footer(text=f"The attack continues!")
                            await battlenotif.edit(embed=battleembed)
                            defending_troops = battle.RemainingDefendingArmy
                            attacking_troops = battle.RemainingAttackingArmy
                            terrain_id = 4
                            battle = calculations(attacking_troops, defending_troops, terrain_id, ctx)
                            # simulate battle
                            await battle.Casualties()
                            # if the defenders win the battle roll, no retreat
                            if battle.defenseroll >= battle.attackroll:
                                victor = "The defenders are victorious!"
                                advance = False
                            # if the attackers win the battle roll, retreat
                            elif battle.attackroll > battle.defenseroll:
                                victor = "The attackers are victorious!"
                                advance = True
                            # create battleembed object
                            battleembed = discord.Embed(
                                title=f"Battle of the City of {targetinfo['name']} (Province #{target})",
                                description=f"Attack from Province #{stationed} by {userinfo['username']} on Province #{target} with {force} troops.",
                                color=discord.Color.red())
                            battleembed.add_field(name="Attacking Force", value=str(attacking_troops))
                            battleembed.add_field(name="Defending Force", value=defending_troops)
                            battleembed.add_field(name="Terrain", value="City")
                            battleembed.add_field(name="Outcome", value=victor, inline=False)
                            battleembed.add_field(name="Attacking Casualties",
                                                  value=str(battle.AttackingCasualties))
                            battleembed.add_field(name="Defending Casualties",
                                                  value=str(battle.DefendingCasualties))
                            battleembed.add_field(name="Crossing Fee", value=str(crossingfee), inline=False)
                            battleembed.add_field(name="Remaining Attacking Force",
                                                  value=str(battle.RemainingAttackingArmy))
                            battleembed.add_field(name="Remaining Defending Force",
                                                  value=str(battle.RemainingDefendingArmy))
                            deaths = await conn.fetchrow(
                                '''SELECT data_value FROM cnc_data WHERE data_name = 'deaths';''')
                            await conn.execute(
                                '''UPDATE cnc_data SET data_value = $1 WHERE data_name = 'deaths';''',
                                deaths['data_value'] + battle.AttackingCasualties + battle.DefendingCasualties)
                            battleembed.set_thumbnail(url="https://i.ibb.co/gTpHmgq/Command-Conquest-symbol.png")
                        # if the reaction is retreat, the attack does not continue
                        if str(reaction.emoji) == "\U0001f3f3":
                            await battlenotif.clear_reactions()
                            battleembed.set_footer(
                                text=f"The attacker retreated from the city and the province has been "
                                     f"returned to the control of {owner}.")
                            await battlenotif.edit(embed=battleembed)
                            return
                    # default result is retreat on the timeout error
                    except asyncio.TimeoutError:
                        await battlenotif.clear_reactions()
                        battleembed.set_footer(
                            text=f"The attacker retreated from the city and the province has been "
                                 f"returned to the control of {owner}.")
                        await battlenotif.edit(embed=battleembed)
                        return
            # if the attackers are victorious in all battles, force the defenders to retreat
            if advance is True:
                # if the natives own the province
                if targetinfo['owner_id'] == 0:
                    # adds the target to the owned list
                    victorownedlist = userinfo['provinces_owned']
                    if victorownedlist is None:
                        victorownedlist = list()
                    victorownedlist.append(target)
                    # updates the relevant information
                    await conn.execute(
                        '''UPDATE provinces SET troops = $1, owner_id = $2, owner = $3, occupier_id = $2, occupier = $3
                         WHERE id = $4;''',
                        battle.RemainingAttackingArmy, author.id, userinfo['username'], target)
                    await conn.execute(
                        '''UPDATE cncusers SET provinces_owned = $1, moves = $2, resources = $3 WHERE user_id = $4;''',
                        victorownedlist, (userinfo['moves'] - 1), (userinfo['resources'] - crossingfee),
                        author.id)
                    await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                       (stationedinfo['troops'] - force), stationed)
                    # sets the footer and sends the embed object
                    battleembed.set_footer(
                        text=f"The natives have lost control of province #{target}!"
                             f" All {targetinfo['troops']} troops have "
                             f"been killed or captured!")
                    await ctx.send(embed=battleembed)
                    await loop.run_in_executor(None, self.map_color, target, targetinfo['cord'][0:2],
                                               userinfo['usercolor'])
                    return
                # fetches potential retreat options for the defender
                defenderprovs = set(prov for prov in defenderinfo['provinces_owned'])
                targetborder = set(p for p in targetinfo['bordering'])
                retreatoptions = list(defenderprovs.intersection(targetborder))
                if (len(retreatoptions) == 0) and (targetinfo['coast'] is False):
                    # if the retreat options are none and the defending land is not a coastline
                    # all troops will be destroyed and the attacker takes control of the province
                    # updates all troop and province information and sends the embed
                    await conn.execute(
                        '''UPDATE cncusers SET resources = $1 WHERE user_id = $2;''',
                        (userinfo['resources'] - crossingfee), author.id)
                    await conn.execute(
                        '''UPDATE provinces  SET troops = $1, occupier_id = $2, occupier = $3 WHERE id = $4;''',
                        battle.RemainingAttackingArmy, author.id, userinfo['username'], target)
                    await conn.execute(
                        '''UPDATE cncusers SET moves = $1, resources = $2 WHERE user_id = $3;''',
                        (userinfo['moves'] - 1), (userinfo['resources'] - crossingfee),
                        author.id)
                    await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                       (stationedinfo['troops'] - force), stationed)
                    battleembed.set_footer(
                        text=f"{defenderinfo['username']} has lost control of province #{target}!"
                             f" With nowhere to retreat, all {targetinfo['troops']} troops have "
                             f"been killed!")
                    # if the province is the capital province, add 50 national unrest
                    if userinfo['capital'] == target:
                        await conn.execute('''UPDATE cncusers SET national_unrest = $1 WHERE username = $2;''',
                                           userinfo['national_unrest'] + 50, userinfo['username'])
                    await ctx.send(embed=battleembed)
                    await loop.run_in_executor(None, self.occupy_color, target, targetinfo['cord'][0:2],
                                               userinfo['usercolor'], defenderinfo['usercolor'])
                    return
                if (len(retreatoptions) == 0) and (targetinfo['coast'] is True):
                    # if the target is a coastline and there are no retreat options by land, the army will be
                    # returned to the defender's stockpile
                    # gets the list of all owned provinces  for both parties
                    # updates all relevant information and sends the embed
                    await conn.execute(
                        '''UPDATE cncusers SET undeployed = $1 WHERE user_id = $2;''',
                        (defenderinfo['undeployed'] + battle.RemainingDefendingArmy),
                        defenderinfo['user_id'])
                    await conn.execute(
                        '''UPDATE provinces  SET troops = $1, occupier_id = $2, occupier = $3 WHERE id = $4;''',
                        battle.RemainingAttackingArmy, author.id, userinfo['username'], target)
                    await conn.execute(
                        '''UPDATE cncusers SET moves = $1, resources = $2 WHERE user_id = $3;''',
                        (userinfo['moves'] - 1), (userinfo['resources'] - crossingfee),
                        author.id)
                    await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                       (stationedinfo['troops'] - force), stationed)
                    deaths = await conn.fetchrow(
                        '''SELECT data_value FROM cnc_data WHERE data_name = 'deaths';''')
                    await conn.execute(
                        '''UPDATE cnc_data SET data_value = $1 WHERE data_name = 'deaths';''',
                        deaths['data_value'] + battle.AttackingCasualties + battle.DefendingCasualties)
                    battleembed.set_footer(
                        text=f"{defenderinfo['username']} has lost control of province #{target}!"
                             f" With nowhere to retreat, all {battle.RemainingDefendingArmy} troops have "
                             f"returned to the stockpile!")
                    # if the province is the capital province, add 50 national unrest
                    if userinfo['capital'] == target:
                        await conn.execute('''UPDATE cncusers SET national_unrest = $1 WHERE username = $2;''',
                                           userinfo['national_unrest'] + 50, userinfo['username'])
                    await ctx.send(embed=battleembed)
                    await loop.run_in_executor(None, self.occupy_color, target, targetinfo['cord'][0:2],
                                               userinfo['usercolor'], defenderinfo['usercolor'])
                    return
                else:
                    # if there are retreat options, one will be randomly selected and all remaining troops will
                    # retreat there
                    retreatprovince = choice(retreatoptions)
                    retreatinfo = await conn.fetchrow('''SELECT * FROM provinces  WHERE id = $1;''',
                                                      retreatprovince)
                    # updates all relevant information and sends the embed
                    await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                       (battle.RemainingDefendingArmy + retreatinfo['troops']), retreatprovince)
                    await conn.execute(
                        '''UPDATE cncusers SET resources = $1 WHERE user_id = $2;''',
                        (userinfo['resources'] - crossingfee), author.id)
                    await conn.execute(
                        '''UPDATE provinces  SET troops = $1, occupier_id = $2, occupier     = $3 WHERE id = $4;''',
                        battle.RemainingAttackingArmy, author.id, userinfo['username'], target)
                    await conn.execute(
                        '''UPDATE cncusers SET moves = $1, resources = $2 WHERE user_id = $3;''',
                        (userinfo['moves'] - 1), (userinfo['resources'] - crossingfee), author.id)
                    await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                       (stationedinfo['troops'] - force), stationed)
                    deaths = await conn.fetchrow(
                        '''SELECT data_value FROM cnc_data WHERE data_name = 'deaths';''')
                    await conn.execute(
                        '''UPDATE cnc_data SET data_value = $1 WHERE data_name = 'deaths';''',
                        deaths['data_value'] + battle.AttackingCasualties + battle.DefendingCasualties)
                    battleembed.set_footer(
                        text=f"{defenderinfo['username']} has lost control of province #{target}!"
                             f" Their {battle.RemainingDefendingArmy} troops have retreated to "
                             f"province #{retreatprovince}!")
                    # if the province is the capital province, add 50 national unrest
                    if userinfo['capital'] == target:
                        await conn.execute('''UPDATE cncusers SET national_unrest = $1 WHERE username = $2;''',
                                           userinfo['national_unrest'] + 50, userinfo['username'])
                    await ctx.send(embed=battleembed)
                    await loop.run_in_executor(None, self.occupy_color, target, targetinfo['cord'][0:2],
                                               userinfo['usercolor'], defenderinfo['usercolor'])
                    return
            # if the attacker is not victorious, no provinces change hands
            else:
                if targetinfo['owner_id'] == 0:
                    # updates the relevant information and sends the embed
                    await conn.execute(
                        '''UPDATE cncusers SET resources = $1 WHERE user_id = $2;''',
                        (userinfo['resources'] - crossingfee), author.id)
                    await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                       (stationedinfo['troops'] - battle.AttackingCasualties), stationed)
                    await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                       (targetinfo['troops'] - battle.DefendingCasualties), target)
                    deaths = await conn.fetchrow(
                        '''SELECT data_value FROM cnc_data WHERE data_name = 'deaths';''')
                    await conn.execute(
                        '''UPDATE cnc_data SET data_value = $1 WHERE data_name = 'deaths';''',
                        deaths['data_value'] + battle.AttackingCasualties + battle.DefendingCasualties)
                    battleembed.set_footer(
                        text=f"The natives have successfully defended province #{target}!")
                    await ctx.send(embed=battleembed)
                    return
                # updates the relevant information and sends the embed
                await conn.execute(
                    '''UPDATE cncusers SET resources = $1 WHERE user_id = $2;''',
                    (userinfo['resources'] - crossingfee), author.id)
                await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                   (stationedinfo['troops'] - battle.AttackingCasualties), stationed)
                await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                   (targetinfo['troops'] - battle.DefendingCasualties), target)
                deaths = await conn.fetchrow(
                    '''SELECT data_value FROM cnc_data WHERE data_name = 'deaths';''')
                await conn.execute(
                    '''UPDATE cnc_data SET data_value = $1 WHERE data_name = 'deaths';''',
                    deaths['data_value'] + battle.AttackingCasualties + battle.DefendingCasualties)
                battleembed.set_footer(
                    text=f"{defenderinfo['username']} has successfully defended province #{target}!")
                await ctx.send(embed=battleembed)
                return

    # ------------------Map Commands----------------------------

    @commands.command(brief="Displays the map")
    @commands.guild_only()
    @commands.max_concurrency(1, commands.BucketType.user)
    async def cnc_map(self, ctx, debug: bool = False):
        loop = asyncio.get_running_loop()
        reactions = ["\U0001f5fa", "\U000026f0", "\U0001f3f3", "\U0001f4cc", "\U0000274c"]
        map = await ctx.send("https://i.ibb.co/kMCVN4K/wargame-terrain-with-numbers.png")
        for react in reactions:
            await map.add_reaction(react)

        # the check for the emojis
        def mapcheck(reaction, user):
            return user == ctx.message.author and str(reaction.emoji)

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60, check=mapcheck)
                # terrain map
                if str(reaction.emoji) == "\U000026f0":
                    await map.clear_reactions()
                    await map.edit(content="https://i.ibb.co/pXg4Fj1/wargame.png")
                    for react in reactions:
                        await map.add_reaction(react)
                    continue
                # numbers + terrain
                if str(reaction.emoji) == "\U0001f5fa":
                    await map.clear_reactions()
                    await map.edit(content="https://i.ibb.co/kMCVN4K/wargame-terrain-with-numbers.png")
                    for react in reactions:
                        await map.add_reaction(react)
                    continue
                # numbers + nations
                if str(reaction.emoji) == "\U0001f3f3":
                    await map.clear_reactions()
                    await map.edit(content="Loading...")
                    async with ctx.typing():
                        initiate = perf_counter()
                        await loop.run_in_executor(None, self.add_ids)
                        with open(fr"{self.map_directory}/Maps/wargame_nations_map.png", "rb") as preimg:
                            img = b64encode(preimg.read())
                        image = perf_counter()
                        params = {"key": "a64d9505a13854ff660980db67ee3596",
                                  "image": img}
                        sleep(1)
                        upload_initate = perf_counter()
                        upload = await loop.run_in_executor(None, requests.post, "https://api.imgbb.com/1/upload",
                                                            params)
                        upload_complete = perf_counter()
                        response = upload.json()
                        await map.edit(content=response["data"]["url"])
                        if debug is True:
                            await ctx.send(
                                f"Image compiled = {image - initiate}\nStarted upload = {upload_initate - initiate}\nUpload Complete = {upload_complete - initiate}")
                    for react in reactions:
                        await map.add_reaction(react)
                        continue
                # name map
                if str(reaction.emoji) == "\U0001f4cc":
                    await map.clear_reactions()
                    await map.edit(content="https://i.ibb.co/TBTMRxK/CNC-name-map.png")
                    for react in reactions:
                        await map.add_reaction(react)
                    continue
                # close
                if str(reaction.emoji) == "\U0000274c":
                    await map.clear_reactions()
                    return
            except asyncio.TimeoutError:
                await map.clear_reactions()
                return

    @commands.command()
    @commands.is_owner()
    async def cnc_wipe_all_data_reset(self, ctx):
        # connects to the database
        conn = self.bot.pool
        await conn.execute('''DELETE FROM cncusers;''')
        await conn.execute('''DELETE FROM relations;''')
        await conn.execute('''DELETE FROM interactions;''')
        await conn.execute('''DELETE FROM pending_interactions;''')
        await conn.execute('''UPDATE provinces  SET owner = '', owner_id = 0, troops = 0;''')
        provinceinfo = await conn.fetch('''SELECT * FROM provinces;''')
        province_ids = [p['id'] for p in provinceinfo]
        for p in province_ids:
            terrain = await conn.fetchrow('''SELECT terrain FROM provinces WHERE id = $1;''', p)
            if terrain['terrain'] == 0:
                await conn.execute(
                    '''UPDATE provinces SET troops = $1, port = FALSE, city = FALSE, fort = FALSE WHERE id = $2;''',
                    randrange(250, 400), p)
            if terrain['terrain'] == 1:
                await conn.execute(
                    '''UPDATE provinces SET troops = $1, port = FALSE, city = FALSE, fort = FALSE WHERE id = $2;''',
                    randrange(100, 180), p)
            if terrain['terrain'] == 2:
                await conn.execute(
                    '''UPDATE provinces SET troops = $1, port = FALSE, city = FALSE, fort = FALSE WHERE id = $2;''',
                    randrange(300, 400), p)
            if terrain['terrain'] == 5:
                await conn.execute(
                    '''UPDATE provinces SET troops = $1, port = FALSE, city = FALSE, fort = FALSE WHERE id = $2;''',
                    randrange(1000, 1300), p)
            if terrain['terrain'] == 7:
                await conn.execute(
                    '''UPDATE provinces SET troops = $1, port = FALSE, city = FALSE, fort = FALSE WHERE id = $2;''',
                    randrange(100, 180), p)
        await conn.execute('''UPDATE cnc_data SET data_value = $1 WHERE data_name = $2;''', 0, "turns")
        await conn.execute('''UPDATE cnc_data SET data_value = $1 WHERE data_name = $2;''', 0, "resources")
        await conn.execute('''UPDATE cnc_data SET data_value = $1 WHERE data_name = $2;''', 0, "deaths")
        await ctx.send("https://tenor.com/view/finished-elijah-wood-lord-of-the-rings-lava-fire-gif-5894611")
        return

    @commands.command()
    @commands.is_owner()
    async def cnc_reset_map(self, ctx):
        map = Image.open(fr"{self.map_directory}/Maps/wargame_blank_save.png").convert("RGBA")
        map.save(fr"{self.map_directory}/Maps/wargame_provinces.png")
        await ctx.send("Map reset.")

    # ---------------------Moderation------------------------------

    @commands.command(usage="[nation name] [amount] [reason]", brief="Gives a specified nation credits")
    @modcheck()
    async def cnc_award(self, ctx, username: str, amount: int, *args):
        # connects to the database
        conn = self.bot.pool
        # checks for user existence
        author = ctx.author
        allusers = await conn.fetch('''SELECT username FROM cncusers;''')
        allusers = [u['username'].lower() for u in allusers]
        if username.lower() not in allusers:
            await ctx.send(f"{username} does not appear to be registered")

            return
        if amount == 0:
            await ctx.send("Don't waste my time.")

            return
        reason = ' '.join(args[:])
        # commits changes
        userinfo = await conn.fetchrow('''SELECT resources FROM cncusers WHERE lower(username) = $1;''',
                                       username.lower())
        await conn.execute('''UPDATE cncusers SET resources = $1 WHERE lower(username) = $2;''',
                           (userinfo['resources'] + amount), username)
        await conn.execute('''INSERT INTO mod_logs(mod, mod_id, action, reason) VALUES($1, $2, $3, $4);''',
                           author.name, author.id, f"awarded {amount} credit resources to {username}", reason)
        return

    @commands.command(usage="[nation name] [province] [reason]", brief="Gives a specified nation a specified province")
    @modcheck()
    async def cnc_cede(self, ctx, username: str, province: int, *args):
        # connects to the database
        conn = self.bot.pool
        author = ctx.author
        reason = ' '.join(args[:])
        # if it is not a release
        if username != "0":
            # checks user existence
            allusers = await conn.fetch('''SELECT username FROM cncusers;''')
            allusers = [u['username'].lower() for u in allusers]
            if username.lower() not in allusers:
                await ctx.send(f"{username} does not appear to be registered")

                return
            # fetches user info
            user = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1;''', username)
            provinceinfo = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', province)
            if provinceinfo is None:
                await ctx.send("That province does not seem to exist.")

                return
            # if the province is owned by the natives
            if provinceinfo['owner_id'] == 0:
                # updateds all relevant information
                await conn.execute('''UPDATE provinces SET owner = $1, owner_id = $2, troops = 0 WHERE id = $3;''',
                                   user['username'], user['user_id'], province)
                owned_list = user['provinces_owned'].append(province)
                await conn.execute('''UPDATE cncusers SET provinces_owned = $1 WHERE user_id = $2;''',
                                   owned_list, user['user_id'])
                self.map_color(province, provinceinfo['cord'], user['usercolor'])
                await conn.execute('''INSERT INTO mod_logs(id, mod_id, action, reason) VALUES($1,$2,$3,$4);''',
                                   ctx.message.id, author.id, f"ceded province {province} to {user['username']}",
                                   reason)
                await ctx.send(f"Province #{province} awarded to {user['username']}.")
                return
            # if the province is owned
            elif provinceinfo['owner_id'] != 0:
                # fetches province owner information and removes province id
                owner = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', provinceinfo['owner_id'])
                stationedtroops = provinceinfo['troops']
                owner_ownedlist = owner['provinces_owned']
                owner_ownedlist.remove(province)
                # updates relevant information
                await conn.execute('''UPDATE provinces SET owner = $1, owner_id = $2, troops = 0 WHERE id = $3;''',
                                   user['username'], user['user_id'], province)
                owned_list = user['provinces_owned'].append(province)
                await conn.execute('''UPDATE cncusers SET provinces_owned = $1 WHERE user_id = $2;''',
                                   owned_list, user['user_id'])
                await conn.execute(
                    '''UPDATE cncusers SET provinces_owned = $1, undeployed = $2 WHERE user_id = $3;''',
                    owner_ownedlist, owner['undeployed'] + stationedtroops, owner['user_id'])
                self.map_color(province, provinceinfo['cord'], user['usercolor'])
                await conn.execute('''INSERT INTO mod_logs(id, mod_id, action, reason) VALUES($1,$2,$3,$4);''',
                                   ctx.message.id, author.id,
                                   f"ceded province #{province} from {owner['username']} to {user['username']}",
                                   reason)
                await ctx.send(
                    f"Province #{province} has been ceded from {owner['username']} to {user['username']}."
                    f"All {stationedtroops} in the province have been returned to the undeployed stockpile.")
                await owner['user_id'].send(f"Province #{province} has been removed from your control for the "
                                            f"following reason: ```{reason}```")
                return
        # if the province needs to be released
        elif username == "0":
            # fetch province and owner info
            provinceinfo = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', province)
            if provinceinfo is None:
                await ctx.send("That province does not seem to exist.")
                return
            if provinceinfo['owner_id'] == 0:
                await ctx.send("You cannot force-release a province that is not owned by a user.")
                return
            owner = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', provinceinfo['owner_id'])
            stationedtroops = provinceinfo['troops']
            owner_ownedlist = owner['provinces_owned']
            owner_ownedlist.remove(province)
            # execute updating information
            await conn.execute('''UPDATE cncusers SET provinces_owned = $1, undeployed = $2 WHERE user_id = $3;''',
                               owner_ownedlist, owner['undeployed'] + stationedtroops, owner['user_id'])
            self.map_color(province, provinceinfo['cord'], "#000000", True)
            await conn.execute('''INSERT INTO mod_logs(id, mod_id, action, reason) VALUES($1,$2,$3,$4);''',
                               ctx.message.id, author.id, f"released province #{province} from {owner['username']}",
                               reason)
            await ctx.send(f"Province #{province} has been released from {owner['username']}'s control."
                           f"All {stationedtroops} in the province have been returned to the undeployed stockpile.")
            await owner['user_id'].send(f"Province #{province} has been removed from your control for the "
                                        f"following reason: ```{reason}```")
            return

    @commands.command(usage="[time(s,m,h,d)] [user]", brief="Mutes a user for a specified time or indefinitely")
    @modcheck()
    async def cnc_mute(self, ctx, mutetime, *args):
        # connects to the database
        conn = self.bot.pool
        # parses the user ID and fetches user information
        author = ctx.author
        try:
            user = ' '.join(args[:])
            user = await commands.converter.MemberConverter().convert(ctx, user)
        except commands.BadArgument:
            await ctx.send("That user does not appear to exist. User information is case and spelling sensitive.")
            return
        allusers = await conn.fetch('''SELECT user_id FROM cncusers;''')
        allusers = [u['user_id'] for u in allusers]
        if user.id not in allusers:
            await ctx.send("You cannot mute a user who is not part of the CnC system.")
            return
        # checks that user is not actively muted
        muted = await conn.fetchrow('''SELECT * FROM blacklist WHERE user_id = $1 AND status = $2 AND active = True;''',
                                    user.id, "mute")
        if muted is not None:
            await ctx.send("You cannot mute a user who is already muted!")
            return
        # sets mute time
        basetime = 0
        mutetime = mutetime.split(',')
        unmute_time = 0
        datetimeunmute = 0
        for t in mutetime:
            if t.endswith('s'):
                basetime += int(t[:-1])
            elif t.endswith('m'):
                basetime += int(t[:-1]) * 60
            elif t.endswith('h'):
                basetime += int(t[:-1]) * 3600
            elif t.endswith('d'):
                basetime += int(t[:-1]) * 86400
            elif t == "0":
                pass
            else:
                raise commands.UserInputError
        if basetime < 0:
            raise commands.UserInputError
        # if the mute is temporary
        elif basetime != 0:
            unmute_time = time() + basetime
            # gets the time from now, gets struct time
            datetimeunmute = datetime.datetime.now() + datetime.timedelta(days=0, seconds=basetime)
            unmute_time_struct = strftime('%a, %d %b %Y %H:%M:%S', localtime(unmute_time))
        # if mute time is indefinite
        elif basetime == 0:
            unmute_time = None
        await ctx.send("For what reason are you muting this user? The prompt will time out in 5 minutes")

        def authorcheck(message):
            return ctx.author == message.author and ctx.channel == message.channel

        # waits for a reply
        try:
            banreply = await self.bot.wait_for('message', check=authorcheck, timeout=300)
            reason = banreply.content
        # if 60 seconds pass, timeout
        except asyncio.TimeoutError:
            return await ctx.send("Timed out. Please answer me next time!")
        # execute temporary mute
        if unmute_time is not None:
            await conn.execute(
                '''INSERT INTO blacklist(user_id, action_id, status, end_time, mod_id, reason, action_date) 
                VALUES($1,$2,$3,$4,$5,$6,$7)''',
                user.id, ctx.message.id, "mute", datetimeunmute, author.id, reason, datetime.datetime.now())
            await conn.execute('''INSERT INTO mod_logs(id, mod_id, action, reason) VALUES($1,$2,$3,$4);''',
                               ctx.message.id, author.id, f"muted {user.id} for {mutetime}", reason)
            muteduser = self.bot.get_user(user.id)
            await muteduser.send(
                f"You have been muted and will be unable to use the CnC system until {unmute_time_struct} for the following reason:"
                f"```{reason}```")
            await ctx.send(f"User muted until {unmute_time_struct} EST.")
            return
        # execute indefinite mute
        if unmute_time is None:
            await conn.execute(
                '''INSERT INTO blacklist(user_id, status, mod_id, reason, action_date) VALUES($1,$2,$3,$4,$5)''',
                user.id, "mute", author.id, reason, datetime.datetime.now())
            await conn.execute('''INSERT INTO mod_logs(id, mod_id, action, reason) VALUES($1,$2,$3,$4);''',
                               ctx.message.id, author.id, f"muted {user.id} for {mutetime}", reason)
            await ctx.send(f"User muted indefinitely.")
            return

    @commands.command(usage="[user]", brief="Unmutes a user")
    @modcheck()
    async def cnc_unmute(self, ctx, *args):
        # connects to the database
        conn = self.bot.pool
        # parses out user ID and checks for existence
        author = ctx.author
        try:
            user = ' '.join(args[:])
            user = await commands.converter.MemberConverter().convert(ctx, user)
        except commands.BadArgument:
            await ctx.send("That user does not appear to exist. User information is case and spelling sensitive.")
            return
        allusers = await conn.fetch('''SELECT user_id FROM cncusers;''')
        allusers = [u['user_id'] for u in allusers]
        if user.id not in allusers:
            await ctx.send("You cannot unmute a user who is not part of the CnC system.")
            return
        # checks to make sure that the user is muted
        muted = await conn.fetchrow('''SELECT * FROM blacklist WHERE user_id = $1 AND status = $2 AND active = True;''',
                                    user.id, "mute")
        if muted is None:
            await ctx.send("You cannot unmute a user who is not already muted!")
            return
        # executes unmute
        await conn.execute(
            '''INSERT INTO blacklist SET active = True WHERE user_id = $1 AND status = $2 AND active = True;''',
            user.id, "mute")
        await conn.execute('''INSERT INTO mod_logs(id, mod_id, action, reason) VALUES($1,$2,$3,$4);''',
                           ctx.message.id, author.id, f"unmuted {user.id}", "n/a")
        await ctx.send("User unmuted.")
        return

    @commands.command(usage="[user]", brief="Bans a user")
    @modcheck()
    async def cnc_ban(self, ctx, *args):
        # connects to the database
        conn = self.bot.pool
        # gets user and checks for existence
        try:
            user = ' '.join(args[:])
            user = await commands.converter.MemberConverter().convert(ctx, user)
        except commands.BadArgument:
            await ctx.send("That user does not appear to exist. User information is case and spelling sensitive.")
            return
        author = ctx.author
        allusers = await conn.fetch('''SELECT user_id FROM cncusers;''')
        allusers = [u['user_id'] for u in allusers]
        if user.id not in allusers:
            await ctx.send("You cannot ban a user who is not part of the CnC system.")
            return
        # checks that the user is not banned
        banned = await conn.fetchrow(
            '''SELECT * FROM blacklist WHERE user_id = $1 AND status = $2 AND active = True;''',
            user.id, "ban")
        if banned is not None:
            await ctx.send("You cannot ban a user who is already banned!")
            return
        await ctx.send("For what reason are you banning this user? The prompt will time out in 5 minutes")

        def authorcheck(message):
            return ctx.author == message.author and ctx.channel == message.channel

        # waits for a reply
        try:
            banreply = await self.bot.wait_for('message', check=authorcheck, timeout=300)
            reason = banreply.content
        # if 60 seconds pass, timeout
        except asyncio.TimeoutError:
            return await ctx.send("Timed out. Please answer me next time!")
        # executes ban
        await conn.execute(
            '''INSERT INTO blacklist(user_id, action_id, status, mod_id, reason, action_date)
             VALUES($1,$2,$3,$4,$5,$6);''',
            user.id, ctx.message.id, "ban", author.id, reason, datetime.datetime.now())
        await conn.execute('''INSERT INTO mod_logs(id, mod_id, action, reason) VALUES($1,$2,$3,$4);''',
                           ctx.message.id, author.id, f"banned {user.id}", reason)
        banneduser = self.bot.get_user(user.id)
        await banneduser.send(f"You have been banned from the CnC system for the following reason:```{reason}```")
        await ctx.send("User banned.")
        return

    @commands.command(usage="[user]", brief="Unbans a user")
    @modcheck()
    async def cnc_unban(self, ctx, *args):
        # connects to the database
        conn = self.bot.pool
        author = ctx.author
        # parses out user ID and checks for existence
        try:
            user = ' '.join(args[:])
            user = await commands.converter.MemberConverter().convert(ctx, user)
        except commands.BadArgument:
            await ctx.send("That user does not appear to exist. User information is case and spelling sensitive.")
            return
        allusers = await conn.fetch('''SELECT user_id FROM cncusers;''')
        allusers = [u['user_id'] for u in allusers]
        if user.id not in allusers:
            await ctx.send("You cannot unban a user who is not part of the CnC system.")
            return
        # checks that user is banned
        banned = await conn.fetchrow(
            '''SELECT * FROM blacklist WHERE user_id = $1 AND status = $2 AND active = True;''',
            user.id, "ban")
        if banned is None:
            await ctx.send("You cannot unban a user who is not already banned!")
            return
        # executes unban
        await conn.execute(
            '''UPDATE blacklist SET active = False WHERE user_id = $1 AND status = $2 AND active = True;''',
            user.id, "ban")
        await conn.execute('''INSERT INTO mod_logs(id, mod_id, action, reason) VALUES($1,$2,$3,$4);''',
                           ctx.message.id, author.id, f"unbanned {user.id}", "n/a")
        await ctx.send("User unbanned.")
        return

    @commands.command(usage="[user]", brief="Displays a user's record")
    @modcheck()
    async def cnc_user_log(self, ctx, *args):
        # connects to the database
        conn = self.bot.pool
        # parses out user ID and checks for existence
        try:
            user = ' '.join(args[:])
            user = await commands.converter.MemberConverter().convert(ctx, user)
        except commands.BadArgument:
            await ctx.send("That user does not appear to exist. User information is case and spelling sensitive.")
            return
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', user.id)
        if userinfo is None:
            await ctx.send("That user does not appear to exist.")
            return
        logs = await conn.fetch('''SELECT * FROM blacklist WHERE user_id = $1 ORDER BY action_date DESC;''',
                                user.id)
        userobj = self.bot.get_user(user.id)
        if len(logs) == 0:
            await ctx.send("That user has no record.")
            return
        if len(logs) == 1:
            entry = logs[0]
            userlogembed = discord.Embed(title=f"Logs for {userobj.name}#{userobj.discriminator}",
                                         color=discord.Color.red())
            userlogembed.add_field(name="Reason", value=entry['reason'], inline=False)
            userlogembed.add_field(name="Action ID", value=entry['action_id'])
            userlogembed.add_field(name="Date",
                                   value=f"{entry['action_date'].day}-{entry['action_date'].month}-{entry['action_date'].year}")
            userlogembed.add_field(name="Type", value=entry['status'])
            if entry['end_time'] is not None:
                userlogembed.add_field(name="Timeout", value=f"{strftime('%a, %d %b %Y %H:%M:%S %Z')}")
            userlogembed.add_field(name="Moderator",
                                   value=f"{(self.bot.get_user(entry['mod_id'])).name}#{(self.bot.get_user(entry['mod_id'])).discriminator}")
            userlogembed.add_field(name="Active", value=str(entry['active']))
            await ctx.send(embed=userlogembed)
            return
        if len(logs) > 1:
            reactions = ['\U000025c0', '\U0000274c', '\U000025b6']
            entrynumber = 0
            pages = len(logs)
            entry = logs[entrynumber]
            userlogembed = discord.Embed(title=f"Logs for {userobj.name}#{userobj.discriminator}",
                                         color=discord.Color.red())
            userlogembed.add_field(name="Reason", value=entry['reason'], inline=False)
            userlogembed.add_field(name="Action ID", value=entry['action_id'])
            userlogembed.add_field(name="Date",
                                   value=f"{entry['action_date'].day}-{entry['action_date'].month}-{entry['action_date'].year}")
            userlogembed.add_field(name="Type", value=entry['status'])
            if entry['end_time'] is not None:
                userlogembed.add_field(name="Timeout",
                                       value=f"{entry['end_time'].strftime('%a, %d %b %Y %H:%M:%S')}")
            userlogembed.add_field(name="Moderator",
                                   value=f"{(self.bot.get_user(entry['mod_id'])).name}#{(self.bot.get_user(entry['mod_id'])).discriminator}")
            userlogembed.add_field(name="Active", value=str(entry['active']))
            userlogembed.set_footer(text=f"Page {abs(entrynumber + 1)} of {pages}")
            logmessage = await ctx.send(embed=userlogembed)
            for r in reactions:
                await logmessage.add_reaction(r)
            while True:

                # the check for the emojis
                def mapcheck(reaction, user):
                    return user == ctx.message.author and str(reaction.emoji)

                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=180, check=mapcheck)
                except asyncio.TimeoutError:
                    await logmessage.clear_reactions()
                    await logmessage.edit(content="Logs timed out.", embed=None)
                    break
                # if the reaction is back
                if str(reaction) == '\U000025c0':
                    # if the reaction is back and we are at entry 0
                    if entrynumber == 0:
                        await logmessage.clear_reactions()
                        for r in reactions:
                            await logmessage.add_reaction(r)
                    else:
                        entrynumber -= 1
                        entry = logs[entrynumber]
                        userlogembed = discord.Embed(title=f"Logs for {userobj.name}#{userobj.discriminator}",
                                                     color=discord.Color.red())
                        userlogembed.add_field(name="Reason", value=entry['reason'], inline=False)
                        userlogembed.add_field(name="Action ID", value=entry['action_id'])
                        userlogembed.add_field(name="Date",
                                               value=f"{entry['action_date'].day}-{entry['action_date'].month}-{entry['action_date'].year}")
                        userlogembed.add_field(name="Type", value=entry['status'])
                        if entry['end_time'] is not None:
                            userlogembed.add_field(name="Timeout",
                                                   value=f"{entry['end_time'].strftime('%a, %d %b %Y %H:%M:%S')}")
                        userlogembed.add_field(name="Moderator",
                                               value=f"{(self.bot.get_user(entry['mod_id'])).name}#{(self.bot.get_user(entry['mod_id'])).discriminator}")
                        userlogembed.add_field(name="Active", value=str(entry['active']))
                        userlogembed.set_footer(text=f"Page {abs(entrynumber - 1)} of {pages}")
                        await logmessage.clear_reactions()
                        await logmessage.edit(embed=userlogembed)
                        for r in reactions:
                            await logmessage.add_reaction(r)
                # if the reaction is close
                if str(reaction) == "\U0000274c":
                    await logmessage.clear_reactions()
                    await logmessage.edit(content="Closed.", embed=None)

                    break
                # if the reaction is forward
                if str(reaction) == "\U000025b6":
                    # if the current page is the final page
                    if entrynumber + 1 == len(logs):
                        await logmessage.clear_reactions()
                        for r in reactions:
                            await logmessage.add_reaction(r)
                    # if not the final page, display the next page
                    else:
                        entrynumber += 1
                        entry = logs[entrynumber]
                        userlogembed = discord.Embed(title=f"Logs for {userobj.name}#{userobj.discriminator}",
                                                     color=discord.Color.red())
                        userlogembed.add_field(name="Reason", value=entry['reason'], inline=False)
                        userlogembed.add_field(name="Action ID", value=entry['action_id'])
                        userlogembed.add_field(name="Date",
                                               value=f"{entry['action_date'].day}-{entry['action_date'].month}-{entry['action_date'].year}")
                        userlogembed.add_field(name="Type", value=entry['status'])
                        if entry['end_time'] is not None:
                            userlogembed.add_field(name="Timeout",
                                                   value=f"{entry['end_time'].strftime('%a, %d %b %Y %H:%M:%S')}")
                        userlogembed.add_field(name="Moderator",
                                               value=f"{(self.bot.get_user(entry['mod_id'])).name}#{(self.bot.get_user(entry['mod_id'])).discriminator}")
                        userlogembed.add_field(name="Active", value=str(entry['active']))
                        userlogembed.set_footer(text=f"Page {abs(entrynumber + 1)} of {pages}")
                        await logmessage.clear_reactions()
                        await logmessage.edit(embed=userlogembed)
                        for r in reactions:
                            await logmessage.add_reaction(r)

    @commands.command(usage="[mod]", brief="Displays actions taken by a specific moderator")
    @modcheck()
    async def cnc_mod_log(self, ctx, *args):
        # connects to the database
        conn = self.bot.pool
        # parses out user ID and checks for existence
        try:
            mod = ' '.join(args[:])
            mod = await commands.converter.MemberConverter().convert(ctx, mod)
        except commands.BadArgument:
            await ctx.send(
                "That user does not appear to exist. User information is case and spelling sensitive.")
            return
        # if the user doesn't appear to be a moderator
        uroles = [r.id for r in mod.roles]
        if 928889638888812586 not in uroles:
            await ctx.send("That user does not appear to be a CnC moderator.")
            return
        # fetch the logs
        logs = await conn.fetch('''SELECT * FROM blacklist WHERE mod_id = $1 ORDER BY action_date DESC;''',
                                mod.id)
        # get the user object
        userobj = self.bot.get_user(mod.id)
        # if the moderator hasn't taken any actions
        if len(logs) == 0:
            await ctx.send("That mod has no action record.")
            return
        # if there is only one entry, display the log
        if len(logs) == 1:
            entry = logs[0]
            user = self.bot.get_user(entry['user_id'])
            modlogembed = discord.Embed(title=f"Moderation logs for {userobj.name}#{userobj.discriminator}",
                                        color=discord.Color.red())
            modlogembed.add_field(name="User", value=f"{user.name}#{user.discriminator}")
            modlogembed.add_field(name="Reason", value=entry['reason'], inline=False)
            modlogembed.add_field(name="Action ID", value=entry['action_id'])
            modlogembed.add_field(name="Date",
                                  value=f"{entry['action_date'].day}-{entry['action_date'].month}-{entry['action_date'].year}")
            modlogembed.add_field(name="Type", value=entry['status'])
            if entry['end_time'] is not None:
                modlogembed.add_field(name="Timeout",
                                      value=f"{strftime('%a, %d %b %Y %H:%M:%S %Z', entry['end_time'])}")
            modlogembed.add_field(name="Active", value=str(entry['active']))
            await ctx.send(embed=modlogembed)
            return
        # if there is more than one entry, prepare the log pages
        if len(logs) > 1:
            # back, stop, forward reactions
            reactions = ['\U000025c0', '\U0000274c', '\U000025b6']
            entrynumber = 0
            pages = len(logs)
            entry = logs[entrynumber]
            user = self.bot.get_user(entry['user_id'])
            modlogembed = discord.Embed(title=f"Moderation logs for {userobj.name}#{userobj.discriminator}",
                                        color=discord.Color.red())
            modlogembed.add_field(name="User", value=f"{user.name}#{user.discriminator}")
            modlogembed.add_field(name="Reason", value=entry['reason'], inline=False)
            modlogembed.add_field(name="Action ID", value=entry['action_id'])
            modlogembed.add_field(name="Date",
                                  value=f"{entry['action_date'].day}-{entry['action_date'].month}-{entry['action_date'].year}")
            modlogembed.add_field(name="Type", value=entry['status'])
            if entry['end_time'] is not None:
                modlogembed.add_field(name="Timeout",
                                      value=f"{strftime('%a, %d %b %Y %H:%M:%S %Z', entry['end_time'])}")
            modlogembed.add_field(name="Active", value=str(entry['active']))
            modlogembed.set_footer(text=f"Page {abs(entrynumber + 1)} of {pages}")
            logmessage = await ctx.send(embed=modlogembed)
            for r in reactions:
                await logmessage.add_reaction(r)
            while True:

                # the check for the emojis
                def reasoncheck(reaction, user):
                    return user == ctx.message.author and str(reaction.emoji)

                try:
                    reaction, mod = await self.bot.wait_for('reaction_add', timeout=180, check=reasoncheck)
                except asyncio.TimeoutError:
                    await logmessage.clear_reactions()
                    await logmessage.edit(content="Logs timed out.", embed=None)
                    break
                # if the reaction is back
                if str(reaction) == '\U000025c0':
                    # if the reaction is back and we are at entry 1
                    if entrynumber == 0:
                        await logmessage.clear_reactions()
                        for r in reactions:
                            await logmessage.add_reaction(r)
                    # if the page is not the last, go back a page
                    else:
                        entrynumber -= 1
                        entry = logs[entrynumber]
                        user = self.bot.get_user(entry['user_id'])
                        modlogembed = discord.Embed(
                            title=f"Moderation logs for {userobj.name}#{userobj.discriminator}",
                            color=discord.Color.red())
                        modlogembed.add_field(name="User", value=f"{user.name}#{user.discriminator}")
                        modlogembed.add_field(name="Reason", value=entry['reason'], inline=False)
                        modlogembed.add_field(name="Action ID", value=entry['action_id'])
                        modlogembed.add_field(name="Date",
                                              value=f"{entry['action_date'].day}-{entry['action_date'].month}-{entry['action_date'].year}")
                        modlogembed.add_field(name="Type", value=entry['status'])
                        if entry['end_time'] is not None:
                            modlogembed.add_field(name="Timeout",
                                                  value=f"{strftime('%a, %d %b %Y %H:%M:%S %Z', entry['end_time'])}")
                        modlogembed.add_field(name="Active", value=str(entry['active']))
                        modlogembed.set_footer(text=f"Page {abs(entrynumber - 1)} of {pages}")
                        await logmessage.clear_reactions()
                        await logmessage.edit(embed=modlogembed)
                        for r in reactions:
                            await logmessage.add_reaction(r)
                # if the reaction is close
                if str(reaction) == "\U0000274c":
                    await logmessage.clear_reactions()
                    await logmessage.edit(content="Closed.", embed=None)
                    break
                # if the reaction is forward
                if str(reaction) == "\U000025b6":
                    # if the current page is the final page
                    if entrynumber + 1 == len(logs):
                        await logmessage.clear_reactions()
                        for r in reactions:
                            await logmessage.add_reaction(r)
                    # if it is not the final page, display the next page
                    else:
                        entrynumber += 1
                        entry = logs[entrynumber]
                        user = self.bot.get_user(entry['user_id'])
                        modlogembed = discord.Embed(
                            title=f"Moderation logs for {userobj.name}#{userobj.discriminator}",
                            color=discord.Color.red())
                        modlogembed.add_field(name="User", value=f"{user.name}#{user.discriminator}")
                        modlogembed.add_field(name="Reason", value=entry['reason'], inline=False)
                        modlogembed.add_field(name="Action ID", value=entry['action_id'])
                        modlogembed.add_field(name="Date",
                                              value=f"{entry['action_date'].day}-{entry['action_date'].month}-{entry['action_date'].year}")
                        modlogembed.add_field(name="Type", value=entry['status'])
                        if entry['end_time'] is not None:
                            modlogembed.add_field(name="Timeout",
                                                  value=f"{strftime('%a, %d %b %Y %H:%M:%S %Z', entry['end_time'])}")
                        modlogembed.add_field(name="Active", value=str(entry['active']))
                        modlogembed.set_footer(text=f"Page {abs(entrynumber + 1)} of {pages}")
                        await logmessage.clear_reactions()
                        await logmessage.edit(embed=modlogembed)
                        for r in reactions:
                            await logmessage.add_reaction(r)

    @commands.command(usage="[action id]", brief="Displays information about a specific moderation action")
    @modcheck()
    async def cnc_mod_action(self, ctx, action: int):
        # connects to the database
        conn = self.bot.pool
        # parses out user ID and checks for existence
        log = await conn.fetchrow('''SELECT * FROM blacklist WHERE action_id = $1;''')
        if log is None:
            await ctx.send("That action does not appear to exist.")
            return
        entry = log
        user = self.bot.get_user(entry['user_id'])
        userlogembed = discord.Embed(title=f"Action #{action}",
                                     color=discord.Color.red())
        userlogembed.add_field(name="User", value=f"{user.name}#{user.discriminator}")
        userlogembed.add_field(name="Reason", value=entry['reason'], inline=False)
        userlogembed.add_field(name="Action ID", value=entry['action_id'])
        userlogembed.add_field(name="Date",
                               value=f"{entry['action_date'].day}-{entry['action_date'].month}-{entry['action_date'].year}")
        userlogembed.add_field(name="Type", value=entry['status'])
        if entry['end_time'] is not None:
            userlogembed.add_field(name="Timeout", value=f"{strftime('%a, %d %b %Y %H:%M:%S %Z', entry['end_time'])}")
        userlogembed.add_field(name="Moderator",
                               value=f"{(self.bot.get_user(entry['mod_id'])).name}#{(self.bot.get_user(entry['mod_id'])).discriminator}")
        userlogembed.add_field(name="Active", value=str(entry['active']))
        await ctx.send(embed=userlogembed)
        return

    @commands.command(usage="[province id] [hexcode]", brief="Recolors a province")
    @modcheck()
    async def cnc_paint_province(self, ctx, provinceid: int, hexcode: str):
        try:
            loop = self.bot.loop
            conn = self.bot.pool
            pinfo = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', provinceid)
            if pinfo is None:
                await ctx.send("That province doesn't exist.")
                return
            await loop.run_in_executor(None, self.map_color, provinceid, pinfo['cord'][0:2],
                                       hexcode)
            await ctx.send(f"Done! Province #{provinceid} is now {hexcode}")
        except ValueError:
            await ctx.send("That doesn't seem to be a proper hexcode.")

    @commands.command(brief="Checks all provinces and ensures proper map color")
    @modcheck()
    async def cnc_map_check(self, ctx):
        map = Image.open(fr"{self.map_directory}/Maps/wargame_blank_save.png").convert("RGBA")
        map.save(fr"{self.map_directory}/Maps/wargame_provinces.png")
        conn = self.bot.pool
        loop = self.bot.loop
        users = await conn.fetch('''SELECT username, usercolor FROM cncusers;''')
        usersncolors = dict()
        for u in users:
            usersncolors.update({u['username']: u['usercolor']})
        provinces = await conn.fetch('''SELECT * FROM provinces WHERE owner_id != 0;''')
        async with ctx.typing():
            for p in provinces:
                p_id = p['id']
                p_cord = p['cord'][0:2]
                p_owner = p['owner']
                if p_owner != '':
                    color = usersncolors[p_owner]
                else:
                    color = "#808080"
                if p_owner == p['occupier']:
                    await loop.run_in_executor(None, self.map_color, p_id, p_cord,
                                               color)
                if p_owner != p['occupier']:
                    occupier_color = usersncolors[p['occupier']]
                    await loop.run_in_executor(None, self.occupy_color, p_id, p_cord, occupier_color, color)
        await ctx.send("All owned provinces checked and colored.")

    # ---------------------Updating------------------------------

    @commands.command(brief="Displays the status of the CNC turn loop")
    @commands.is_owner()
    async def cnc_turn_status(self, ctx):
        if self.turn_loop.is_running():
            await ctx.send("Turn loop running")
        else:
            await ctx.send("Turn loop not running.")

    @tasks.loop(hours=6, reconnect=False)
    async def turn_loop(self):
        crashchannel = self.bot.get_channel(835579413625569322)
        try:
            # channel to send to
            cncchannel = self.bot.get_channel(927288304301387816)
            # connects to the database
            conn = self.bot.pool
            # fetches all the users and makes a list
            users = await conn.fetch('''SELECT user_id FROM cncusers;''')
            userids = [ids['user_id'] for ids in users]
            # for every user in the list
            for u in userids:
                user = self.bot.get_user(u)
                credits_added = 0
                # pull out the data and get a list of provinces and trade routes
                userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', u)
                provinces = userinfo['provinces_owned']
                # for every province, collect manpower data, trade value, local Unrest, troops, and city, port,
                # and fort data
                initial_manpower = userinfo['manpower']
                # calculate tax income and deductions
                tax_rate = userinfo['taxation'] / 100
                taxes = initial_manpower * tax_rate
                military_upkeep = userinfo['military_upkeep'] / 100
                public_services = userinfo['public_services'] / 100
                taxes *= 1 - (military_upkeep + public_services)
                credits_added += taxes
                # establish variables
                trade_routes = userinfo['trade_routes']
                initial_trade_value = 0
                total_troops = 0
                civil_war = False
                # fort/city/port/trade route limit update
                if len(userinfo['provinces_owned']) <= 5:
                    await conn.execute(
                        '''UPDATE cncusers SET citylimit = $1, portlimit = $2, fortlimit = $3 WHERE user_id = $4;'''
                        , [userinfo['citylimit'][0], 1], [userinfo['portlimit'][0], 1],
                        [userinfo['fortlimit'][0], 1],
                        userinfo['user_id'])
                elif len(userinfo['provinces_owned']) > 5:
                    fortlimit = math.floor((len(userinfo['provinces_owned']) - 5) / 5) + 1
                    portlimit = math.floor((len(userinfo['provinces_owned']) - 5) / 3) + 1
                    citylimit = math.floor((len(userinfo['provinces_owned']) - 5) / 7) + 1
                    if userinfo['focus'] == 's':
                        fortlimit += fortlimit + 1
                    if userinfo['focus'] == 'e':
                        portlimit += portlimit + 1
                    await conn.execute(
                        '''UPDATE cncusers SET citylimit = $1, portlimit = $2, fortlimit = $3 WHERE user_id = $4;'''
                        , [userinfo['citylimit'][0], citylimit], [userinfo['portlimit'][0], portlimit],
                        [userinfo['fortlimit'][0], fortlimit],
                        userinfo['user_id'])
                trade_route_limit = 0
                # if the user is a great power, +1 trade route
                if userinfo['great_power']:
                    trade_route_limit += 1
                if userinfo['capital'] != 0:
                    trade_route_limit += 1
                # for every city +1 and for every two ports +1
                trade_route_limit += userinfo['citylimit'][0]
                trade_route_limit += math.floor(userinfo['portlimit'][0] / 2)
                # if the current trade route number is too high, close a random trade route
                if trade_routes[0] > trade_route_limit:
                    for i in range(trade_route_limit - trade_routes[0]):
                        closed_interaction = await conn.fetchrow('''SELECT * FROM interactions WHERE sender = $1 OR 
                        recipient = $1 AND type = 'trade' AND active = True ORDER BY RANDOM();''', userinfo['username'])
                        await conn.execute('''UPDATE interactions SET active = False WHERE id = $1;''',
                                           closed_interaction['id'])
                trade_routes = userinfo['trade_routes']
                trade_routes[2] = trade_route_limit
                tax_rate *= 100
                military_upkeep *= 100
                public_services *= 100
                # check national Unrest for civil war and add national Unrest
                national_unrest = userinfo['national_unrest']
                # if the national unrest is above 80
                if len(provinces) > 9:
                    if national_unrest >= 80:
                        # roll a d100
                        unrest_roll = randint(0, 100)
                        # if the d100 is below or equal to the national unrest, trigger civil war
                        if unrest_roll <= national_unrest:
                            provinces_owned = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1 AND
                            occupier_id = $1;''', user.id)
                            provinces_owned = [p['id'] for p in provinces_owned]
                            half_owned = math.floor(len(provinces_owned) / 2)
                            provinces_rebelling = sample(provinces_owned, half_owned)
                            for pr in provinces_rebelling:
                                p_info = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', pr)
                                if p_info is None:
                                    continue
                                provinces_owned.remove(pr)
                                undeployed = userinfo['undeployed']
                                troops_remaining = p_info['troops'] - (p_info['manpower'] * 2)
                                if troops_remaining <= 0:
                                    troops_remaining = 0
                                await conn.execute('''UPDATE cncusers SET provinces_owned = $1, undeployed = $2 WHERE 
                                user_id = $3;''', provinces_owned, undeployed + troops_remaining, u)
                                await conn.execute('''UPDATE provinces SET owner = '', owner_id = '0', occupier = '', 
                                 occupier_id = 0, unrest = 0, troops = $1 WHERE id = $2;''', p_info['manpower'] * 2, pr)
                                await self.bot.loop.run_in_executor(None, self.map_color, pr, p_info['cord'][0:2],
                                                                    "#808080", True)
                            provinces_rebelling.sort()
                            provinces_rebelling_string = ', '.join(str(e) for e in provinces_rebelling)
                            await user.send(f"Province(s) {provinces_rebelling_string} have rebelled in a civil war!")
                            civil_war = True
                # add national Unrest
                national_unrest = 0
                tax_unrest = math.ceil(10 * (1 + 1) ** ((tax_rate / 5) - 1))
                military_upkeep_unrest = -round((1 * (1 + 1) ** (military_upkeep / 5.75 - 1)) + ((1 * (1 + 1) ** (
                        military_upkeep / 10 - 1)) * 0.75))
                if public_services < 15:
                    public_service_unrest = round(30 - public_services * 2)
                else:
                    public_service_unrest = -round((3 * (1 + 0.75) ** ((public_services - 23) / 5) - 1))
                if userinfo['great_power'] is False:
                    if len(provinces) > 50:
                        national_unrest += math.ceil(10 * (1 + 1) ** (((len(provinces) - 50) / 5) - 1))
                else:
                    if len(provinces) > 75:
                        national_unrest += math.ceil(10 * (1 + 1) ** (((len(provinces) - 75) / 5) - 1))
                national_unrest += tax_unrest + public_service_unrest + military_upkeep_unrest
                await conn.execute('''UPDATE cncusers SET national_unrest = $1 WHERE user_id = $2;''',
                                   national_unrest, u)
                # gather each province information
                provinces_rebelled = list()
                structures_destroyed = 0
                for p in provinces:
                    if p == 0:
                        continue
                    p_info = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', p)
                    if p_info['uprising']:
                        if p_info['unrest'] < randint(1, 100):
                            await conn.execute('''UPDATE provinces SET uprising = False WHERE id = $1;''', p)
                            pass
                        else:
                            unrest = 0
                            troops_unrest = p_info['troops'] / -100
                            if userinfo['great_power']:
                                troops_unrest *= 2
                            tax_unrest = math.ceil(10 * (1 + 1) ** ((tax_rate / 5) - 1))
                            military_upkeep_unrest = -round(
                                (1 * (1 + 1) ** (military_upkeep / 5.75 - 1)) + ((1 * (1 + 1) ** (
                                        military_upkeep / 10 - 1)) * 0.75))
                            if public_services < 15:
                                public_service_unrest = round(30 - public_services * 2)
                            else:
                                public_service_unrest = -round((3 * (1 + 0.75) ** ((public_services - 23) / 5) - 1))
                            unrest += tax_unrest + public_service_unrest + military_upkeep_unrest + troops_unrest
                            await conn.execute('''UPDATE provinces SET unrest = $1 WHERE id = $2;''', unrest, p)
                            continue
                    total_troops += p_info['troops']
                    province_value = p_info['trade_value']
                    if p_info['city'] and p_info['port']:
                        province_value *= 1.6
                    elif p_info['city']:
                        province_value *= 1.1
                    elif p_info['port']:
                        province_value *= 1.5
                    initial_trade_value += province_value
                    # check local Unrest for local uprising and add local Unrest
                    local_unrest = p_info['unrest']
                    # if the local Unrest is greater than 50
                    if len(provinces) > 4:
                        if local_unrest >= 50:
                            # roll a d100
                            unrest_roll = randint(0, 100)
                            # if the d100 is greater than the local Unrest, trigger an uprising
                            if unrest_roll <= local_unrest:
                                # trigger uprising effects
                                if p_info['city']:
                                    if randint(1, 100) >= 80:
                                        structures_destroyed += 1
                                        await conn.execute('''UPDATE provinces SET city = False WHERE id = $1;''', p)
                                        citylimit = userinfo['citylimit'][0] - 1
                                        await conn.execute(
                                            '''UPDATE cnc_users SET citylimit = $1 WHERE user_id = $2;''', citylimit, u)
                                if p_info['fort']:
                                    if randint(1, 100) >= 90:
                                        structures_destroyed += 1
                                        await conn.execute('''UPDATE provinces SET fort = False WHERE id = $1;''', p)
                                        fortlimit = userinfo['fortlimit'][0] - 1
                                        await conn.execute(
                                            '''UPDATE cnc_users SET portlimit = $1 WHERE user_id = $2;''', fortlimit, u)
                                if p_info['port']:
                                    if randint(1, 100) >= 80:
                                        structures_destroyed += 1
                                        await conn.execute('''UPDATE provinces SET port = False WHERE id = $1;''', p)
                                        portlimit = userinfo['portlimit'][0] - 1
                                        await conn.execute(
                                            '''UPDATE cnc_users SET portlimit = $1 WHERE user_id = $2;''', portlimit, u)
                                troops_attacked = p_info['troops'] - \
                                                  (randint((p_info['manpower']) / 2, p_info['manpower']))
                                if troops_attacked < 0:
                                    troops_attacked = 0
                                await conn.execute('''UPDATE provinces SET uprising = True, troops = $2
                                WHERE id = $1;''', p, troops_attacked)
                                provinces_rebelled.append(p)
                    # add Unrest
                    unrest = 0
                    if civil_war:
                        unrest -= 20
                    troops_unrest = p_info['troops'] / -100
                    tax_unrest = math.ceil(10 * (1 + 1) ** ((tax_rate / 5) - 1))
                    military_upkeep_unrest = -round((1 * (1 + 1) ** (military_upkeep / 5.75 - 1)) + ((1 * (1 + 1) ** (
                            military_upkeep / 10 - 1)) * 0.75))
                    if public_services < 15:
                        public_service_unrest = round(30 - public_services * 2)
                    else:
                        public_service_unrest = -round((3 * (1 + 0.75) ** ((public_services - 23) / 5) - 1))
                    unrest += tax_unrest + public_service_unrest + military_upkeep_unrest + troops_unrest
                    await conn.execute('''UPDATE provinces SET unrest = $1 WHERE id = $2;''', unrest, p)
                if len(provinces_rebelled) != 0:
                    provinces_rebelled_string = ', '.join(str(p) for p in provinces_rebelled)
                    await user.send(f"The population of province(s) {provinces_rebelled_string} "
                                    f"have risen up due to high unrest! {structures_destroyed} structures have been"
                                    f"destroyed by the rioters.")
                # calculate unrest and occupation cost for occupied provinces
                occupation_uprising = list()
                provinces_occupied = await conn.fetchrow('''SELECT * FROM provinces WHERE occupier_id = $1 AND
                owner_id != $1;''', u)
                if provinces_occupied is True:
                    for p in provinces_occupied:
                        # calculate unrest
                        unrest = 0
                        # add base occupation unrest
                        unrest += 25
                        troops_unrest = p['troops'] / -100
                        tax_unrest = math.ceil(10 * (1 + 1) ** ((tax_rate / 5) - 1))
                        military_upkeep_unrest = -round(
                            (1 * (1 + 1) ** (military_upkeep / 5.75 - 1)) + ((1 * (1 + 1) ** (
                                    military_upkeep / 10 - 1)) * 0.75))
                        if public_services < 15:
                            public_service_unrest = round(30 - public_services * 2)
                        else:
                            public_service_unrest = -round((3 * (1 + 0.75) ** ((public_services - 23) / 5) - 1))
                        unrest += tax_unrest + public_service_unrest + military_upkeep_unrest + troops_unrest
                        # if the unrest is greater than 50, roll a d100-25 to see if they rebel
                        if unrest >= 50:
                            unrest_roll = randint(1, 100) - 25
                            if unrest_roll <= 75:
                                owner_info = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1,''',
                                                                 p['owner'])
                                await self.bot.loop.run_in_executor(None, self.map_color, p['id'], p['cord'],
                                                                    owner_info['usercolor'])
                                occupation_uprising.append(p['id'])
                if occupation_uprising is True:
                    occupation_uprising_string = ', '.join(str(p) for p in occupation_uprising)
                    await user.send(f"The population of occupied province(s) {occupation_uprising_string} "
                                    f"have risen up due to high unrest and have returned to their "
                                    f"core owner's control!")

                # for every domestic trade route, +10%. For every foreign trade route, +5%
                trade_gain = initial_trade_value * (userinfo['trade_routes'][0] / 10)
                trade_gain += initial_trade_value * ((userinfo['trade_routes'][1] * 5) / 100)
                credits_added += trade_gain
                credits_added -= total_troops * 0.01
                # calculate manpower increase and max manpower
                max_manpower_raw = await conn.fetchrow('''SELECT sum(manpower::int) FROM provinces WHERE
                owner_id = $1 AND uprising = False;''', u)
                max_manpower = max_manpower_raw['sum']
                if max_manpower is None:
                    max_manpower = 3000
                added_manpower = (public_services / 100) * max_manpower
                added_manpower += userinfo['citylimit'][0] * 1000
                if userinfo['capital'] != 0:
                    if userinfo['capital'] in provinces:
                        added_manpower += 2500
                manpower = added_manpower + userinfo['manpower']
                if manpower > max_manpower:
                    manpower = max_manpower
                # calculates action points
                moves = 4
                if len(provinces) <= 10:
                    moves += 0
                elif len(provinces) > 10:
                    moves += math.floor((len(provinces) - 10) / 10)
                    if userinfo['focus'] == "s":
                        moves += math.floor(moves * .1)
                if userinfo['great_power']:
                    moves += 1
                # add all credits, manpower, moves to the user
                await conn.execute('''UPDATE cncusers SET resources = $1, manpower = $2, maxmanpower = $3, moves = $4, 
                trade_routes = $5 WHERE user_id = $6;''',
                                   credits_added + userinfo['resources'], manpower, max_manpower, moves, trade_routes,
                                   u)
                # great power calculations
                gp_points = 0
                gp_points += credits_added * 0.001
                gp_points += total_troops * 0.001
                gp_points += initial_manpower * 0.001
                gp_points += userinfo['fortlimit'][0] + userinfo['citylimit'][0]
                gp_points += len(provinces) * 0.5
                alliances = await conn.fetchrow(
                    '''SELECT COUNT(name) FROM relations WHERE name = $1 AND relation = 'alliance';''',
                    userinfo['username'])
                gp_points += alliances['count'] * 0.5
                await conn.execute('''UPDATE cncusers SET great_power_score = $1 WHERE username = $2;''',
                                   gp_points, userinfo['username'])
            await conn.execute('''UPDATE cncusers SET great_power = False;''')
            great_powers = await conn.fetch('''SELECT user_id, great_power_score FROM cncusers 
            ORDER BY great_power_score DESC LIMIT 3;''')
            for gp in great_powers:
                if gp['great_power_score'] > 50:
                    userid = gp['user_id']
                    await conn.execute('''UPDATE cncusers SET great_power = True WHERE user_id = $1;''', userid)
            turn = await conn.fetchrow('''SELECT data_value FROM cnc_data WHERE data_name = 'turns';''')
            await conn.execute('''UPDATE cnc_data SET data_value = $1 WHERE data_name = 'turns';''',
                               turn['data_value'] + 1)
            await cncchannel.send(f"New turn! It is now turn #{turn['data_value'] + 1}.")
        except Exception:
            self.bot.logger.warning(msg=traceback.format_exc())
            await crashchannel.send(content=f"```py\n{traceback.format_exc()}```")

    @commands.command()
    @commands.is_owner()
    async def cnc_force_turn(self, ctx):
        try:
            # channel to send to
            cncchannel = self.bot.get_channel(927288304301387816)
            # connects to the database
            conn = self.bot.pool
            # fetches all the users and makes a list
            users = await conn.fetch('''SELECT user_id FROM cncusers;''')
            userids = [ids['user_id'] for ids in users]
            # for every user in the list
            for u in userids:
                user = self.bot.get_user(u)
                credits_added = 0
                # pull out the data and get a list of provinces and trade routes
                userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', u)
                provinces = userinfo['provinces_owned']
                # for every province, collect manpower data, trade value, local Unrest, troops, and city, port,
                # and fort data
                initial_manpower = userinfo['manpower']
                # calculate tax income and deductions
                tax_rate = userinfo['taxation'] / 100
                taxes = initial_manpower * tax_rate
                military_upkeep = userinfo['military_upkeep'] / 100
                public_services = userinfo['public_services'] / 100
                taxes *= 1 - (military_upkeep + public_services)
                credits_added += taxes
                # establish variables
                trade_routes = userinfo['trade_routes']
                initial_trade_value = 0
                total_troops = 0
                civil_war = False
                # fort/city/port/trade route limit update
                if len(userinfo['provinces_owned']) <= 5:
                    await conn.execute(
                        '''UPDATE cncusers SET citylimit = $1, portlimit = $2, fortlimit = $3 WHERE user_id = $4;'''
                        , [userinfo['citylimit'][0], 1], [userinfo['portlimit'][0], 1],
                        [userinfo['fortlimit'][0], 1],
                        userinfo['user_id'])
                elif len(userinfo['provinces_owned']) > 5:
                    fortlimit = math.floor((len(userinfo['provinces_owned']) - 5) / 5) + 1
                    portlimit = math.floor((len(userinfo['provinces_owned']) - 5) / 3) + 1
                    citylimit = math.floor((len(userinfo['provinces_owned']) - 5) / 7) + 1
                    if userinfo['focus'] == 's':
                        fortlimit += fortlimit + 1
                    if userinfo['focus'] == 'e':
                        portlimit += portlimit + 1
                    await conn.execute(
                        '''UPDATE cncusers SET citylimit = $1, portlimit = $2, fortlimit = $3 WHERE user_id = $4;'''
                        , [userinfo['citylimit'][0], citylimit], [userinfo['portlimit'][0], portlimit],
                        [userinfo['fortlimit'][0], fortlimit],
                        userinfo['user_id'])
                trade_route_limit = 0
                # if the user is a great power, +1 trade route
                if userinfo['great_power']:
                    trade_route_limit += 1
                if userinfo['capital'] != 0:
                    trade_route_limit += 1
                # for every city +1 and for every two ports +1
                trade_route_limit += userinfo['citylimit'][0]
                trade_route_limit += math.floor(userinfo['portlimit'][0] / 2)
                # if the current trade route number is too high, close a random trade route
                if trade_routes[0] > trade_route_limit:
                    for i in range(trade_route_limit - trade_routes[0]):
                        closed_interaction = await conn.fetchrow('''SELECT * FROM interactions WHERE sender = $1 OR 
                        recipient = $1 AND type = 'trade' AND active = True ORDER BY RANDOM();''', userinfo['username'])
                        await conn.execute('''UPDATE interactions SET active = False WHERE id = $1;''',
                                           closed_interaction['id'])
                trade_routes = userinfo['trade_routes']
                trade_routes[2] = trade_route_limit
                tax_rate *= 100
                military_upkeep *= 100
                public_services *= 100
                # check national Unrest for civil war and add national Unrest
                national_unrest = userinfo['national_unrest']
                # if the national unrest is above 80
                if len(provinces) > 9:
                    if national_unrest >= 80:
                        # roll a d100
                        unrest_roll = randint(0, 100)
                        # if the d100 is below or equal to the national unrest, trigger civil war
                        if unrest_roll <= national_unrest:
                            provinces_owned = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1 AND
                            occupier_id = $1;''', user.id)
                            provinces_owned = [p['id'] for p in provinces_owned]
                            half_owned = math.floor(len(provinces_owned) / 2)
                            provinces_rebelling = sample(provinces_owned, half_owned)
                            for pr in provinces_rebelling:
                                p_info = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', pr)
                                if p_info is None:
                                    continue
                                provinces_owned.remove(pr)
                                undeployed = userinfo['undeployed']
                                troops_remaining = p_info['troops'] - (p_info['manpower'] * 2)
                                if troops_remaining <= 0:
                                    troops_remaining = 0
                                await conn.execute('''UPDATE cncusers SET provinces_owned = $1, undeployed = $2 WHERE 
                                user_id = $3;''', provinces_owned, undeployed + troops_remaining, u)
                                await conn.execute('''UPDATE provinces SET owner = '', owner_id = '0', occupier = '', 
                                 occupier_id = 0, unrest = 0, troops = $1 WHERE id = $2;''', p_info['manpower'] * 2, pr)
                                await self.bot.loop.run_in_executor(None, self.map_color, pr, p_info['cord'][0:2],
                                                                    "#808080", True)
                            provinces_rebelling.sort()
                            provinces_rebelling_string = ', '.join(str(e) for e in provinces_rebelling)
                            await user.send(f"Province(s) {provinces_rebelling_string} have rebelled in a civil war!")
                            civil_war = True
                # add national Unrest
                national_unrest = 0
                tax_unrest = math.ceil(10 * (1 + 1) ** ((tax_rate / 5) - 1))
                military_upkeep_unrest = -round((1 * (1 + 1) ** (military_upkeep / 5.75 - 1)) + ((1 * (1 + 1) ** (
                        military_upkeep / 10 - 1)) * 0.75))
                if public_services < 15:
                    public_service_unrest = round(30 - public_services * 2)
                else:
                    public_service_unrest = -round((3 * (1 + 0.75) ** ((public_services - 23) / 5) - 1))
                if userinfo['great_power'] is False:
                    if len(provinces) > 50:
                        national_unrest += math.ceil(10 * (1 + 1) ** (((len(provinces) - 50) / 5) - 1))
                else:
                    if len(provinces) > 75:
                        national_unrest += math.ceil(10 * (1 + 1) ** (((len(provinces) - 75) / 5) - 1))
                national_unrest += tax_unrest + public_service_unrest + military_upkeep_unrest
                await conn.execute('''UPDATE cncusers SET national_unrest = $1 WHERE user_id = $2;''',
                                   national_unrest, u)
                # gather each province information
                provinces_rebelled = list()
                structures_destroyed = 0
                for p in provinces:
                    if p == 0:
                        continue
                    p_info = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', p)
                    if p_info['uprising']:
                        if p_info['unrest'] < randint(1, 100):
                            await conn.execute('''UPDATE provinces SET uprising = False WHERE id = $1;''', p)
                            pass
                        else:
                            unrest = 0
                            troops_unrest = p_info['troops'] / -100
                            if userinfo['great_power']:
                                troops_unrest *= 2
                            tax_unrest = math.ceil(10 * (1 + 1) ** ((tax_rate / 5) - 1))
                            military_upkeep_unrest = -round(
                                (1 * (1 + 1) ** (military_upkeep / 5.75 - 1)) + ((1 * (1 + 1) ** (
                                        military_upkeep / 10 - 1)) * 0.75))
                            if public_services < 15:
                                public_service_unrest = round(30 - public_services * 2)
                            else:
                                public_service_unrest = -round((3 * (1 + 0.75) ** ((public_services - 23) / 5) - 1))
                            unrest += tax_unrest + public_service_unrest + military_upkeep_unrest + troops_unrest
                            await conn.execute('''UPDATE provinces SET unrest = $1 WHERE id = $2;''', unrest, p)
                            continue
                    total_troops += p_info['troops']
                    province_value = p_info['trade_value']
                    if p_info['city'] and p_info['port']:
                        province_value *= 1.6
                    elif p_info['city']:
                        province_value *= 1.1
                    elif p_info['port']:
                        province_value *= 1.5
                    initial_trade_value += province_value
                    # check local Unrest for local uprising and add local Unrest
                    local_unrest = p_info['unrest']
                    # if the local Unrest is greater than 50
                    if len(provinces) > 4:
                        if local_unrest >= 50:
                            # roll a d100
                            unrest_roll = randint(0, 100)
                            # if the d100 is greater than the local Unrest, trigger an uprising
                            if unrest_roll <= local_unrest:
                                # trigger uprising effects
                                if p_info['city']:
                                    if randint(1, 100) >= 80:
                                        structures_destroyed += 1
                                        await conn.execute('''UPDATE provinces SET city = False WHERE id = $1;''', p)
                                        citylimit = userinfo['citylimit'][0] - 1
                                        await conn.execute(
                                            '''UPDATE cnc_users SET citylimit = $1 WHERE user_id = $2;''', citylimit, u)
                                if p_info['fort']:
                                    if randint(1, 100) >= 90:
                                        structures_destroyed += 1
                                        await conn.execute('''UPDATE provinces SET fort = False WHERE id = $1;''', p)
                                        fortlimit = userinfo['fortlimit'][0] - 1
                                        await conn.execute(
                                            '''UPDATE cnc_users SET portlimit = $1 WHERE user_id = $2;''', fortlimit, u)
                                if p_info['port']:
                                    if randint(1, 100) >= 80:
                                        structures_destroyed += 1
                                        await conn.execute('''UPDATE provinces SET port = False WHERE id = $1;''', p)
                                        portlimit = userinfo['portlimit'][0] - 1
                                        await conn.execute(
                                            '''UPDATE cnc_users SET portlimit = $1 WHERE user_id = $2;''', portlimit, u)
                                troops_attacked = p_info['troops'] - \
                                                  (randint((p_info['manpower']) / 2, p_info['manpower']))
                                if troops_attacked < 0:
                                    troops_attacked = 0
                                await conn.execute('''UPDATE provinces SET uprising = True, troops = $2
                                WHERE id = $1;''', p, troops_attacked)
                                provinces_rebelled.append(p)
                    # add Unrest
                    unrest = 0
                    if civil_war:
                        unrest -= 20
                    troops_unrest = p_info['troops'] / -100
                    tax_unrest = math.ceil(10 * (1 + 1) ** ((tax_rate / 5) - 1))
                    military_upkeep_unrest = -round((1 * (1 + 1) ** (military_upkeep / 5.75 - 1)) + ((1 * (1 + 1) ** (
                            military_upkeep / 10 - 1)) * 0.75))
                    if public_services < 15:
                        public_service_unrest = round(30 - public_services * 2)
                    else:
                        public_service_unrest = -round((3 * (1 + 0.75) ** ((public_services - 23) / 5) - 1))
                    unrest += tax_unrest + public_service_unrest + military_upkeep_unrest + troops_unrest
                    await conn.execute('''UPDATE provinces SET unrest = $1 WHERE id = $2;''', unrest, p)
                if len(provinces_rebelled) != 0:
                    provinces_rebelled_string = ', '.join(str(p) for p in provinces_rebelled)
                    await user.send(f"The population of province(s) {provinces_rebelled_string} "
                                    f"have risen up due to high unrest! {structures_destroyed} structures have been"
                                    f"destroyed by the rioters.")
                # calculate unrest and occupation cost for occupied provinces
                occupation_uprising = list()
                provinces_occupied = await conn.fetchrow('''SELECT * FROM provinces WHERE occupier_id = $1 AND
                owner_id != $1;''', u)
                if provinces_occupied is True:
                    for p in provinces_occupied:
                        # calculate unrest
                        unrest = 0
                        # add base occupation unrest
                        unrest += 25
                        troops_unrest = p['troops'] / -100
                        tax_unrest = math.ceil(10 * (1 + 1) ** ((tax_rate / 5) - 1))
                        military_upkeep_unrest = -round(
                            (1 * (1 + 1) ** (military_upkeep / 5.75 - 1)) + ((1 * (1 + 1) ** (
                                    military_upkeep / 10 - 1)) * 0.75))
                        if public_services < 15:
                            public_service_unrest = round(30 - public_services * 2)
                        else:
                            public_service_unrest = -round((3 * (1 + 0.75) ** ((public_services - 23) / 5) - 1))
                        unrest += tax_unrest + public_service_unrest + military_upkeep_unrest + troops_unrest
                        # if the unrest is greater than 50, roll a d100-25 to see if they rebel
                        if unrest >= 50:
                            unrest_roll = randint(1, 100) - 25
                            if unrest_roll <= 75:
                                owner_info = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1,''',
                                                                 p['owner'])
                                await self.bot.loop.run_in_executor(None, self.map_color, p['id'], p['cord'],
                                                                    owner_info['usercolor'])
                                occupation_uprising.append(p['id'])
                if occupation_uprising is True:
                    occupation_uprising_string = ', '.join(str(p) for p in occupation_uprising)
                    await user.send(f"The population of occupied province(s) {occupation_uprising_string} "
                                    f"have risen up due to high unrest and have returned to their "
                                    f"core owner's control!")

                # for every domestic trade route, +10%. For every foreign trade route, +5%
                trade_gain = initial_trade_value * (userinfo['trade_routes'][0] / 10)
                trade_gain += initial_trade_value * ((userinfo['trade_routes'][1] * 5) / 100)
                credits_added += trade_gain
                credits_added -= total_troops * 0.01
                # calculate manpower increase and max manpower
                max_manpower_raw = await conn.fetchrow('''SELECT sum(manpower::int) FROM provinces WHERE
                owner_id = $1 AND uprising = False;''', u)
                max_manpower = max_manpower_raw['sum']
                if max_manpower is None:
                    max_manpower = 3000
                added_manpower = (public_services / 100) * max_manpower
                added_manpower += userinfo['citylimit'][0] * 1000
                if userinfo['capital'] != 0:
                    if userinfo['capital'] in provinces:
                        added_manpower += 2500
                manpower = added_manpower + userinfo['manpower']
                if manpower > max_manpower:
                    manpower = max_manpower
                # calculates action points
                moves = 4
                if len(provinces) <= 10:
                    moves += 0
                elif len(provinces) > 10:
                    moves += math.floor((len(provinces) - 10) / 10)
                    if userinfo['focus'] == "s":
                        moves += math.floor(moves * .1)
                if userinfo['great_power']:
                    moves += 1
                # add all credits, manpower, moves to the user
                await conn.execute('''UPDATE cncusers SET resources = $1, manpower = $2, maxmanpower = $3, moves = $4, 
                trade_routes = $5 WHERE user_id = $6;''',
                                   credits_added + userinfo['resources'], manpower, max_manpower, moves, trade_routes,
                                   u)
                # great power calculations
                gp_points = 0
                gp_points += credits_added * 0.001
                gp_points += total_troops * 0.001
                gp_points += initial_manpower * 0.001
                gp_points += userinfo['fortlimit'][0] + userinfo['citylimit'][0]
                gp_points += len(provinces) * 0.5
                alliances = await conn.fetchrow(
                    '''SELECT COUNT(name) FROM relations WHERE name = $1 AND relation = 'alliance';''',
                    userinfo['username'])
                gp_points += alliances['count'] * 0.5
                await conn.execute('''UPDATE cncusers SET great_power_score = $1 WHERE username = $2;''',
                                   gp_points, userinfo['username'])
            await conn.execute('''UPDATE cncusers SET great_power = False;''')
            great_powers = await conn.fetch('''SELECT user_id, great_power_score FROM cncusers 
            ORDER BY great_power_score DESC LIMIT 3;''')
            for gp in great_powers:
                if gp['great_power_score'] > 50:
                    userid = gp['user_id']
                    await conn.execute('''UPDATE cncusers SET great_power = True WHERE user_id = $1;''', userid)
            turn = await conn.fetchrow('''SELECT data_value FROM cnc_data WHERE data_name = 'turns';''')
            await conn.execute('''UPDATE cnc_data SET data_value = $1 WHERE data_name = 'turns';''',
                               turn['data_value'] + 1)
            await cncchannel.send(f"New turn! It is now turn #{turn['data_value'] + 1}.")
        except Exception:
            self.bot.logger.warning(msg=traceback.format_exc())
            await ctx.send(f"```py\n{traceback.format_exc()}```")

    async def cncstartloop(self):
        try:
            await self.bot.wait_until_ready()
            # fetch the Shard testing channel
            shardchannel = self.bot.get_channel(835579413625569322)
            # ensure there is no lingering loop
            if self.turn_loop.is_running():
                await shardchannel.send("Already running on_ready.")
                return
            # grab the timezone and the curren time
            eastern = timezone('US/Eastern')
            now = datetime.datetime.now(eastern)
            # if the hour is less than midnight but not somehow also a negative hour (hey, it happens)
            if now.time() < datetime.time(hour=0):
                update = now.replace(hour=0, minute=0, second=0, microsecond=1)
                await shardchannel.send(f"Turn loop waiting until {update.strftime('%d %a %Y at %H:%M:%S %Z%z')}.")
                await discord.utils.sleep_until(update)
            # if the hour is less than 0600 but greater than 0600
            elif now.time() < datetime.time(hour=6):
                update = now.replace(hour=6, minute=0, second=0)
                await shardchannel.send(f"Turn loop waiting until {update.strftime('%d %a %Y at %H:%M:%S %Z%z')}.")
                await discord.utils.sleep_until(update)
            # if the hour is greater than 0600 but less than noon
            elif now.time() < datetime.time(hour=12):
                update = now.replace(hour=12, minute=0, second=0)
                await shardchannel.send(f"Turn loop waiting until {update.strftime('%d %a %Y at %H:%M:%S %Z%z')}.")
                await discord.utils.sleep_until(update)
            # if the hour is greater than noon but less than 1800
            elif now.time() < datetime.time(hour=18, minute=0):
                update = now.replace(hour=18, minute=0)
                await shardchannel.send(f"Turn loop waiting until {update.strftime('%d %a %Y at %H:%M:%S %Z%z')}.")
                await discord.utils.sleep_until(update)
            # if the hour is greater than 1800 but less than midnight
            elif now.time() > datetime.time(hour=18, minute=0):
                update = now.replace(hour=0, minute=0, second=0)
                update += datetime.timedelta(days=1)
                await shardchannel.send(f"Turn loop waiting until {update.strftime('%d %a %Y at %H:%M:%S %Z%z')}.")
                await discord.utils.sleep_until(update)
            self.turn_loop.start()
        except Exception:
            self.bot.logger.warning(msg=traceback.format_exc())


async def setup(bot: Shard):
    # define the cog, set the loop, set the turnloop running, and add the cog
    cog = CNC(bot)
    loop = bot.loop
    CNC.turn_task = loop.create_task(cog.cncstartloop())
    await bot.add_cog(cog)
