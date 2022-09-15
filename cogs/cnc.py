# cnc v2.0
import random
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
from customchecks import modcheck, SilentFail, WrongInput
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
import traceback
from cnc_research import Technology
from cnc_events import Events
from collections import Counter
import re


class CNC(commands.Cog):

    def __init__(self, bot: Shard):
        # self.map_directory = r"/root/Documents/Shard/CNC/Map Files/Maps/"
        # self.province_directory = r"/root/Documents/Shard/CNC/Map Files/Province Layers/"
        self.map_directory = r"/root/Documents/Shard/CNC/Map Files/Maps/"
        self.province_directory = r"/root/Documents/Shard/CNC/Map Files/Province Layers/"
        self.interaction_directory = r"/root/Documents/Shard/CNC/Interaction Files/"
        self.bot = bot

    def cog_unload(self):
        # stop the running turnloop
        self.turn_loop.cancel()
        # cancel the running turn task
        self.turn_task.cancel()

    turn_task = None
    banned_colors = ["#000000", "#ffffff", "#808080", "#0071BC", "#0084E2", "#2BA5E2"]
    version = "version 2.0 Teaching and Trading"

    async def cog_check(self, ctx):
        # if the sender is the owner, return true
        if ctx.author.id in [293518673417732098]:
            return True
        else:
            # if there this is in DMs, check the user id on the Thegye server to ensure proper role
            if ctx.guild is None:
                aroles = list()
                thegye = ctx.bot.get_guild(674259612580446230)
                member = thegye.get_member(ctx.author.id)
                for ar in member.roles:
                    aroles.append(ar.id)
                if 674260547897917460 not in aroles:
                    raise SilentFail
            # if this is a server, check to make sure the user has the right role and/or this is the right server
            elif ctx.guild is not None:
                aroles = list()
                if ctx.guild.id == 674259612580446230:
                    for ar in ctx.author.roles:
                        aroles.append(ar.id)
                    if 674260547897917460 not in aroles:
                        raise SilentFail
                else:
                    raise SilentFail
            # initiate connection
            conn = self.bot.pool
            blacklist = await conn.fetchrow('''SELECT * FROM blacklist WHERE user_id = $1 AND active = True;''',
                                            ctx.author.id)
            # if the user is on the blacklist, raise fails
            if blacklist is not None:
                if blacklist['end_time'] is None:
                    if blacklist['status'] == "mute":
                        raise SilentFail
                    if blacklist['status'] == "ban":
                        raise SilentFail
                # if the user should be off the blacklist, remove them
                if blacklist['end_time'] < datetime.datetime.now():
                    await conn.execute(
                        '''UPDATE blacklist SET active = False WHERE user_id = $1 AND end_time = $2;''',
                        ctx.author.id, blacklist['end_time'])
            else:
                return True

    def map_color(self, province, province_cord, hexcode, release: bool = False):
        # obtain the coordinate information
        province_cord = ((int(province_cord[0])), (int(province_cord[1])))
        # get color
        try:
            color = ImageColor.getrgb(hexcode)
        except ValueError:
            return ValueError("Hex code issue")
        # open the map and the province images
        map = Image.open(fr"{self.map_directory}wargame_provinces.png").convert("RGBA")
        prov = Image.open(fr"{self.province_directory}{province}.png").convert("RGBA")
        # obtain size and coordinate information
        width = prov.size[0]
        height = prov.size[1]
        cord = (province_cord[0], province_cord[1])
        # for every pixel, change the color to the owners
        for x in range(0, width):
            for y in range(0, height):
                data = prov.getpixel((x, y))
                if data != color:
                    if data != (0, 0, 0, 0):
                        if data !=(255, 255, 255, 0):
                            prov.putpixel((x, y), color)
        # if this is a release, change every color to neutral grey
        if release is True:
            color = ImageColor.getrgb("#808080")
            for x in range(0, prov.size[0]):
                for y in range(0, prov.size[1]):
                    data = prov.getpixel((x, y))
                    if data != color:
                        if data != (0, 0, 0, 0):
                            prov.putpixel((x, y), color)
        # convert, paste, and save the image
        prov = prov.convert("RGBA")
        map.paste(prov, box=cord, mask=prov)
        map.save(fr"{self.map_directory}wargame_provinces.png")

    def occupy_color(self, province, province_cord, occupy_color, owner_color):
        # get province information
        province_cord = ((int(province_cord[0])), (int(province_cord[1])))
        # get colors
        try:
            occupyer = ImageColor.getrgb(occupy_color)
            owner = ImageColor.getrgb(owner_color)
        except ValueError:
            return ValueError("Hex code issue")
        # open map, create draw object, and obtain province information
        map = Image.open(fr"{self.map_directory}wargame_provinces.png").convert("RGBA")
        prov = Image.open(fr"{self.province_directory}{province}.png").convert("RGBA")
        prov_draw = ImageDraw.Draw(prov)
        width = prov.size[0]
        height = prov.size[1]
        cord = (province_cord[0], province_cord[1])
        # set spacing and list of blank pixels
        space = 20
        not_colored = list()
        # for every non-colored pixel, add it to the list
        for x in range(0, width):
            for y in range(0, height):
                pixel = prov.getpixel((x, y))
                if pixel == (0, 0, 0, 0):
                    not_colored.append((x, y))
                else:
                    prov.putpixel((x, y), owner)
        # draw lines every 20 pixels with the occupier color
        for x in range(0, 1000*2, space):
            prov_draw.line([x, 0, x - 1000, 1000], width=5, fill=occupyer)
        # for every pixel in the non-colored list, remove that pixel
        for pix in not_colored:
            prov.putpixel(pix, (0, 0, 0, 0))
        map.paste(prov, box=cord, mask=prov)
        map.save(fr"{self.map_directory}wargame_provinces.png")

    def add_ids(self):
        # open map, open ids image, paste, and save
        bmap = Image.open(fr"{self.map_directory}wargame_provinces.png").convert("RGBA")
        ids = Image.open(fr"{self.map_directory}wargame numbers.png").convert("RGBA")
        bmap.paste(ids, box=(0, 0), mask=ids)
        bmap.save(fr"{self.map_directory}wargame_nations_map.png")

    def space_replace(self, userinput: str) -> str:
        # replaces user input with proper, url-friendly code
        to_regex = userinput.replace(" ", "_")
        return re.sub(r"[^a-zA-Z0-9_-]", ' ', to_regex)

    def underscore_replace(self, userinput: str) -> str:
        """Replaces underscores with spaces and lowers the text"""
        to_regex = userinput.replace("_", " ").title()
        return re.sub(r"[^a-zA-Z0-9_-]", ' ', to_regex)

    # ---------------------User Commands------------------------------

    @commands.command(brief="Displays information about the CNC system.")
    @commands.guild_only()
    async def cnc_info(self, ctx):
        # open connection and fetch data
        conn = self.bot.pool
        data = await conn.fetchrow('''SELECT data_value FROM cnc_data WHERE data_name = $1;''', "turn")

        player_count = await conn.fetchrow('''SELECT count(*) FROM cncusers;''')
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
        infoembed.add_field(name="Version", value=f"{self.version}")
        infoembed.add_field(name="Turns", value=f"It is currently turn {data['data_value']}.")
        infoembed.add_field(name="Active Players", value=f"{player_count['count']}")
        infoembed.add_field(name="Questions?",
                            value="Contact the creator: Lies Kryos#1734\n"
                                  "Contact a moderator: Lies Kryos#1734, [Insert_Person_Here]#6003")
        infoembed.set_thumbnail(url="https://i.ibb.co/gTpHmgq/Command-Conquest-symbol.png")
        # send embed
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
        data = await conn.fetchrow('''SELECT data_value FROM cnc_data WHERE data_name = $1;''', "turn")
        await ctx.send(f"It is currently turn #{data['data_value']}. "
                       f"Next turn is <t:{math.floor(turnjob.next_run_time.timestamp())}:R>")

    @commands.command(usage="[nation name] #[hexadecimal color id] [focus (m,e,s)]", brief="Registers a new nation")
    @commands.guild_only()
    async def cnc_register(self, ctx, nationame: str, color: str, focus: str):
        userid = ctx.author.id
        # connects to the database
        conn = self.bot.pool
        # checks to see if the user is registered
        registered = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', userid)
        if registered is not None:
            await ctx.send(f"You are already registered as {registered['username']}.")
            return
        # checks the focus and ensures proper reading
        focuses = ['m', 'e', 's']
        if focus.lower() not in focuses:
            await ctx.send("That is not a valid focus. Please use only `m`, `e`, or `s`.")
            return
        if focus.lower() == 'm':
            research = ["Basic Metalworking"]
        elif focus.lower() == 'e':
            research = ["Currency"]
        else:
            research = ["Writing"]
        # if the color is banned, dont allow
        if color in self.banned_colors:
            await ctx.send("That color is a reserved color. Please pick another color.")
            return
        color_check = await conn.fetchrow('''SELECT * FROM cncusers WHERE usercolor = $1;''', color)
        # if the color is in use, dont allow
        if color_check is not None:
            await ctx.send("That color is already taken by another user. Please pick another color.")
            return
        # try and get the color from the hex code
        try:
            ImageColor.getrgb(color)
        except ValueError:
            await ctx.send("That doesn't appear to be a valid hex color code. Include the `#` symbol.")
            return
        # inserts the user into the databases
        resources = randint(9000, 10000)
        await conn.execute(
            '''INSERT INTO cncusers (user_id, username, usercolor, resources, 
            focus, researched, undeployed, moves) VALUES ($1, $2, $3, $4, $5, $6, $7, $8);''',
            userid, nationame, color, resources, focus.lower(), research, 0, 5)
        await conn.execute('''INSERT INTO cnc_modifiers (user_id) VALUES ($1);''', userid)
        province = await conn.fetchrow('''SELECT * FROM provinces 
        WHERE occupier_id = 0 and owner_id = 0 and id NOT IN (130, 441, 442, 621, 622, 623, 65, 486, 215, 923, 926, 924,
         925, 771, 772,770, 769, 768, 909, 761, 762, 763, 764, 765, 766, 767, 1207, 
         1208, 1209, 1210, 1211, 1212, 1213, 1214, 744) ORDER BY random();''')
        await conn.execute('''UPDATE provinces SET occupier_id = $1, occupier = $2 , owner = $2, owner_id = $1 
        WHERE id = $3;''', userid, nationame, province['id'])
        await self.bot.loop.run_in_executor(None, self.map_color, province['id'], province['cord'], color)
        tech = Technology(nationame, ctx=ctx, techs=research)
        await tech.effects()
        await ctx.send(f"{ctx.author.name} has registered {nationame} in the Command and Conquer System\n"
                       f"{nationame} has been given **\u03FE{resources}**, **3000 manpower**, and "
                       f"**Province #{province['id']}**. Use these gifts wisely!")

    @commands.command(usage="<nation name or Discord username>", aliases=['cncv'],
                      brief="Displays information about a nation")
    async def cnc_view(self, ctx, *, args=None):
        # connects to the database
        conn = self.bot.pool
        nationname = args
        if nationname is None:
            # if the nationame is left blank, the author id is used to find the nation information
            author = ctx.author
            # grabs the nation information
            userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
            if userinfo is None:
                await ctx.send("You are not registered.")
            # sets the color properly
            if userinfo["usercolor"] == "":
                color = discord.Color.random()
                colorvalue = "No color set."
            else:
                color = discord.Color(int(userinfo["usercolor"].lstrip('#'), 16))
                colorvalue = color
            # grabs all provinces owned by the nation and makes them into a pretty list
            provinces_owned = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1;''',
                                               author.id)
            provinces_owned_but_occupied = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1 and 
            occupier_id != $1;''', author.id)
            if provinces_owned is None:
                provinces = "None"
                total_troops = userinfo['undeployed']
            else:
                provinces_owned = [p['id'] for p in provinces_owned]
                provinces_owned.sort()
                provinces_owned = [str(p) for p in provinces_owned]
                provinces_owned_but_occupied = [str(p['id']) for p in provinces_owned_but_occupied]
                for p in provinces_owned_but_occupied:
                    for op in provinces_owned:
                        if op == p:
                            p_index = provinces_owned.index(op)
                            provinces_owned[p_index] = f"__*{op}*__"
                provinces = ', '.join(str(i) for i in provinces_owned)
                total_troops = 0
                total_troops_raw = await conn.fetchrow('''SELECT sum(troops::int) FROM provinces 
                WHERE occupier_id = $1;''', author.id)
                if total_troops_raw['sum'] is not None:
                    total_troops += total_troops_raw['sum']
                total_troops += userinfo['undeployed']
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
            relations = await conn.fetch('''SELECT * FROM interactions WHERE (sender = $1 OR recipient = $1) 
            AND active = True;''', userinfo['username'])
            alliances = list()
            wars = list()
            for r in relations:
                if r['type'] == 'war':
                    if r['sender'] == userinfo['username']:
                        wars.append(r['recipient'])
                    else:
                        wars.append(r['sender'])
                if r['type'] == 'alliance':
                    if r['sender'] == userinfo['username']:
                        alliances.append(r['recipient'])
                    else:
                        alliances.append(r['sender'])
            if len(wars) != 0:
                wars.sort()
                wars = ', '.join(str(w) for w in wars)
            else:
                wars = "None"
            if len(alliances) != 0:
                alliances.sort()
                alliances = ', '.join(str(a) for a in alliances)
            else:
                alliances = "None"
            if userinfo['capital'] == 0:
                capital = "None"
            else:
                capital = f"Province #{userinfo['capital']}"
            # creates the embed item
            cncuserembed = discord.Embed(title=userinfo["username"], color=color,
                                         description=f"Registered nation of {self.bot.get_user(userinfo['user_id']).name}.")
            cncuserembed.add_field(name=f"Territory (Total: {len(provinces_owned)})", value=provinces, inline=False)
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
            snowflake = False
            user = None
            try:
                user = await commands.converter.MemberConverter().convert(ctx, nationname)
                snowflake = True
            except commands.BadArgument:
                pass
            if snowflake:
                userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''',
                                           user.id)
            else:
                userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE lower(username) = $1;''',
                                               nationname.lower())
            if userinfo is None:
                await ctx.send(f"`{nationname}` does not appear to be registered.")
                return
            # sets the color properly
            color = discord.Color(int(userinfo["usercolor"].lstrip('#'), 16))
            colorvalue = color
            # grabs all provinces owned by the nation and makes them into a pretty list
            provinces_owned = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1;''',
                                               userinfo['user_id'])
            provinces_owned_but_occupied = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1 and 
                        occupier_id != $1;''', userinfo['user_id'])
            if provinces_owned is None:
                provinces = "None"
                total_troops = userinfo['undeployed']
            else:
                provinces_owned = [p['id'] for p in provinces_owned]
                provinces_owned.sort()
                provinces_owned = [str(p) for p in provinces_owned]
                provinces_owned_but_occupied = [str(p['id']) for p in provinces_owned_but_occupied]
                for p in provinces_owned_but_occupied:
                    for op in provinces_owned:
                        if op == p:
                            p_index = provinces_owned.index(op)
                            provinces_owned[p_index] = f"__*{op}*__"
                provinces = ', '.join(str(i) for i in provinces_owned)
                total_troops = 0
                total_troops_raw = await conn.fetchrow('''SELECT sum(troops::int) FROM provinces 
                            WHERE occupier_id = $1;''', userinfo['user_id'])
                if total_troops_raw['sum'] is not None:
                    total_troops += total_troops_raw['sum']
                total_troops += userinfo['undeployed']
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
            relations = await conn.fetch('''SELECT * FROM interactions WHERE (sender = $1 OR recipient = $1) 
                        AND active = True;''', userinfo['username'])
            alliances = list()
            wars = list()
            for r in relations:
                if r['type'] == 'war':
                    if r['sender'] == userinfo['username']:
                        wars.append(r['recipient'])
                    else:
                        wars.append(r['sender'])
                if r['type'] == 'alliance':
                    if r['sender'] == userinfo['username']:
                        alliances.append(r['recipient'])
                    else:
                        alliances.append(r['sender'])
            if len(wars) != 0:
                wars.sort()
                wars = ', '.join(str(w) for w in wars)
            else:
                wars = "None"
            if len(alliances) != 0:
                alliances.sort()
                alliances = ', '.join(str(a) for a in alliances)
            else:
                alliances = "None"
            if userinfo['capital'] == 0:
                capital = "None"
            else:
                capital = f"Province #{userinfo['capital']}"
            # creates the embed item
            cncuserembed = discord.Embed(title=userinfo["username"], color=color,
                                         description=f"Registered nation of {self.bot.get_user(userinfo['user_id']).name}.")
            cncuserembed.add_field(name=f"Territory (Total: {len(provinces_owned)})", value=provinces, inline=False)
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

    @commands.command(aliases=['cncdv'], brief="Displays detailed information about a nation, privately")
    async def cnc_detailed_view(self, ctx):
        # connects to the database
        conn = self.bot.pool
        author = ctx.author
        # grabs the user information
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        if userinfo is None:
            await ctx.send("You are not registered.")
            return
        # fetches modifiers
        modifiers = await conn.fetchrow('''SELECT * FROM cnc_modifiers WHERE user_id = $1;''', author.id)
        # sets the color properly
        color = discord.Color(int(userinfo["usercolor"].lstrip('#'), 16))
        colorvalue = color
        # grabs all provinces owned by the nation and makes them into a pretty list
        provinces_owned = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1 and occupier_id = $1;''',
                                           author.id)
        if provinces_owned is None:
            provinces = "None"
            total_troops = userinfo['undeployed']
        else:
            provinces_owned = [p['id'] for p in provinces_owned]
            provinces_owned.sort()
            provinces = ', '.join(str(i) for i in provinces_owned)
            total_troops = 0
            total_troops_raw = await conn.fetchrow('''SELECT sum(troops::int) FROM provinces 
            WHERE occupier_id = $1;''', author.id)
            total_troops += total_troops_raw['sum']
            total_troops += userinfo['undeployed']
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
        relations = await conn.fetch('''SELECT * FROM interactions WHERE (sender = $1 OR recipient = $1) 
        AND active = True;''', userinfo['username'])
        alliances = list()
        wars = list()
        for r in relations:
            if r['type'] == 'war':
                if r['sender'] == userinfo['username']:
                    wars.append(r['recipient'])
                else:
                    wars.append(r['sender'])
            if r['type'] == 'alliance':
                if r['sender'] == userinfo['username']:
                    alliances.append(r['recipient'])
                else:
                    alliances.append(r['sender'])
        if len(wars) != 0:
            wars.sort()
            wars = ', '.join(str(w) for w in wars)
        else:
            wars = "None"
        if len(alliances) != 0:
            alliances.sort()
            alliances = ', '.join(str(a) for a in alliances)
        else:
            alliances = "None"
        # fetches all outgoing routes
        outgoing_routes = await conn.fetch('''SELECT * FROM interactions WHERE type = 'trade' AND active = True AND 
        sender_id = $1;''', author.id)
        routes_dict = dict()
        routes = ''
        outgoing_count = 0
        # counts the number of outgoing routes per recipient
        for t in outgoing_routes:
            routes_dict.update({t['recipient']: 0})
        for t in outgoing_routes:
            routes_dict[t['recipient']] += 1
            outgoing_count += 1
        for t in routes_dict:
            routes += f"{t} ({routes_dict[t]}), "
        routes = routes[:-2]
        # counts the number of incoming routes
        incoming_count = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE type = 'trade' AND
        active = True AND recipient_id = $1;''', author.id)
        if incoming_count['count'] is None:
            incoming_count = 0
        else:
            incoming_count = incoming_count['count']
        max_manpower = 0
        manpower_mod = userinfo['public_services'] / 100
        max_manpower_raw = await conn.fetchrow('''SELECT sum(manpower::int) FROM provinces WHERE owner_id = $1;''',
                                               author.id)
        if max_manpower_raw['sum'] is None:
            max_manpower_raw = 0
        else:
            max_manpower_raw = max_manpower_raw['sum']
        max_manpower += max_manpower_raw
        added_manpower = math.ceil((max_manpower * manpower_mod) * modifiers['manpower_mod'])
        # creates the embed item
        cncuserembed = discord.Embed(title=userinfo["username"], color=color,
                                     description=f"Registered nation of "
                                                 f"{self.bot.get_user(userinfo['user_id']).name}.")
        cncuserembed.add_field(name=f"Territory (Total: {len(provinces_owned)})", value=provinces, inline=False)
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
                               value=f"City Limit: {userinfo['citylimit']}\n"
                                     f"Port Limit: {userinfo['portlimit']}\n"
                                     f"Fort Limit: {userinfo['fortlimit']}")
        cncuserembed.add_field(name="Trade Route Overview",
                               value=f"Outgoing Routes: {outgoing_count}\n"
                                     f"Incoming Routes: {incoming_count}\n"
                                     f"Active Outgoing Routes ({outgoing_count}): {routes}\n"
                                     f"Max Routes: {userinfo['trade_route_limit']}")
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
        provinces_owned = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1 and occupier_id = $1;''',
                                           author.id)
        if provinces_owned is None:
            provinces_owned = [0]
        else:
            provinces_owned = [p['id'] for p in provinces_owned]
        provinces_owned.sort()
        # gets user's color in Discord format
        color = discord.Color(int(userinfo["usercolor"].lstrip('#'), 16))
        colorvalue = color
        # creates embed
        sv_emebed = discord.Embed(title=f"{userinfo['username']} - Strategic View",
                                  description="A strategic overlook at all troop placements and provinces.",
                                  color=colorvalue)
        # counts off numbers
        province_number = 0
        for p in provinces_owned:
            # fetches province information, adds it to the embed, and increases the count
            provinceinfo = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', p)
            structures = list()
            if provinceinfo['city']:
                structures.append('City')
            if provinceinfo['port']:
                structures.append('Port')
            if provinceinfo['fort']:
                structures.append('Fort')
            if len(structures) == 0:
                structures = "None"
            else:
                structures = ', '.join(s for s in structures)
            sv_emebed.add_field(name=f"**Province #{p}**",
                                value=f"Troops: {provinceinfo['troops']:,}\nTrade Value: {provinceinfo['value']}"
                                      f"\nManpower: {provinceinfo['manpower']:,}\nUnrest: {provinceinfo['unrest']}\n"
                                      f"Structures: {structures}")
            province_number += 1
            # if there are 15 provinces queued, send the embed, clear it, and start over
            # (unless this is the last set)
            if province_number % 15 == 0 and province_number != len(provinces_owned):
                await author.send(embed=sv_emebed)
                sv_emebed.clear_fields()
                continue
            # if the maximum provinces have been reached, send the final set
            if province_number == len(provinces_owned):
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
        provinces_owned = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1 and occupier_id = $1;''',
                                           user_info['user_id'])
        if provinces_owned is None:
            provinces_owned = 0
        for province in provinces_owned:
            if province == 0:
                break
            await conn.execute('''UPDATE provinces  SET owner_id = 0, owner = '', troops = 0 WHERE id = $1;''',
                               province['id'])
            color = "#808080"
            cord = await conn.fetchrow('''SELECT cord FROM provinces WHERE id = $1;''', province['id'])
            await loop.run_in_executor(None, self.map_color, province['id'], cord['cord'][0:2], color, True)
        await ctx.send("Deletion complete.")
        user = self.bot.get_user(user_info["user_id"])
        if reason is None:
            reason = "Your registered Command and Conquest account has been terminated for an unlisted reason. " \
                     "If you have further questions, contact a moderator."
        await user.send(
            f"Your registered Command and Conquer account, {nationamesave['username']}, "
            f"has been deleted by moderator {ctx.author} for the following reason:```{reason}```")

    @commands.command(usage="[item being edited (color, focus, name)]", brief="Changes a nation's information")
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
            provinces_owned = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1 and occupier_id = $1;''',
                                               author.id)
            if provinces_owned is None:
                provinces_owned = 0
            for p in provinces_owned:
                if p['id'] == 0:
                    break
                cord = (p['cord'][0], p['cord'][1])
                await loop.run_in_executor(None, self.map_color, p['id'], cord, colorreply.content)
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
        # if the name is being edited
        if editing.lower() == "name":
            await ctx.send("What is your new nation name?")

            def authorcheck(message):
                return ctx.author == message.author and ctx.channel == message.channel

            # waits for a reply
            try:
                namereply = await self.bot.wait_for('message', check=authorcheck, timeout=60)
            # if 60 seconds pass, timeout
            except asyncio.TimeoutError:
                return await ctx.send("Timed out. Please answer me next time!")
            # makes sure name is not banned or taken
            registered = await conn.fetch('''SELECT * FROM cncusers;''')
            if namereply.content.lower() in ["name", "nation", "natives", "moderator", "mod"]:
                await ctx.send("That name is a reserved name. Please pick another name.")
                return
            names = [u['username'].lower() for u in registered]
            if namereply.content.lower() in names:
                await ctx.send("That name is already taken by another user. Please pick another name.")
                return
            # updates all tables
            await conn.execute('''UPDATE cncusers SET username = $1 WHERE username = $2;''',
                               namereply.content, usereditinfo['username'])
            await conn.execute('''UPDATE interactions SET sender = $1 WHERE sender = $2;''',
                               namereply.content, usereditinfo['username'])
            await conn.execute('''UPDATE interactions SET recipient = $1 WHERE recipient = $2;''',
                               namereply.content, usereditinfo['username'])
            await conn.execute('''UPDATE pending_interactions SET sender = $1 WHERE sender = $2;''',
                               namereply.content, usereditinfo['username'])
            await conn.execute('''UPDATE pending_interactions SET recipient = $1 WHERE recipient = $2;''',
                               namereply.content, usereditinfo['username'])
            await conn.execute('''UPDATE provinces SET owner = $1 WHERE owner = $2;''',
                               namereply.content, usereditinfo['username'])
            await conn.execute('''UPDATE provinces SET occupier = $1 WHERE occupier = $2;''',
                               namereply.content, usereditinfo['username'])
            await ctx.send(f"Success! Your nation name is now {namereply.content}.")
            return
        else:
            # if the editing argument is not the proper argument
            await ctx.send(f"`{editing}` is not a viable option for this command!")
            return

    # --------------------Technology & Event Commands--------------------------

    @commands.command(usage="[technology name]", brief="Displays technology information.", aliases=['cnct'])
    @commands.guild_only()
    async def cnc_tech(self, ctx, *, args):
        # creates tech object
        techinfo = Technology(ctx=ctx, nation="None", tech=args)
        # initiates lookup
        await techinfo.lookup()

    @commands.command(usage="[technology name]", brief="Researches a technology.")
    @commands.guild_only()
    async def cnc_research(self, ctx, *, args):
        # creates pool
        conn = self.bot.pool
        # confirms user existance
        user = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', ctx.author.id)
        if user is None:
            await ctx.send("You are not registered.")
            return
        tech = Technology(nation=user['username'], ctx=ctx, tech=args)
        await tech.research()

    @commands.command(brief="Displays information about current research.")
    @commands.guild_only()
    async def cnc_researching(self, ctx):
        # creates pool
        conn = self.bot.pool
        # confirms user existance
        user = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', ctx.author.id)
        if user is None:
            await ctx.send("You are not registered.")
            return
        # fetches researching
        researching = await conn.fetchrow('''SELECT * FROM cnc_researching WHERE user_id = $1;''', ctx.author.id)
        # if nothing is being researched
        if researching is None:
            await ctx.send(f"{user['username']} is not currently researching any technology.")
            return
        else:
            await ctx.send(f"{user['username']} is researching {self.underscore_replace(researching['tech'])}.\n"
                           f"It will be done researching in **{researching['turns']} turns.**")

    @commands.command(brief="Sends the technology tree.")
    @commands.guild_only()
    async def cnc_tech_tree(self, ctx):
        # creates pool
        conn = self.bot.pool
        # confirms user existance
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', ctx.author.id)
        if userinfo is None:
            await ctx.send("You are not registered.")
            return
        tech = Technology(nation=userinfo['username'], ctx=ctx)
        await tech.tree()

    @commands.command(brief="Sends a list of all current modifiers.", aliases=['cncmods'])
    async def cnc_modifiers(self, ctx):
        # creates pool
        conn = self.bot.pool
        # confirms user existance
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', ctx.author.id)
        if userinfo is None:
            await ctx.send("You are not registered.")
            return
        modifiers = await conn.fetchrow('''SELECT * FROM cnc_modifiers WHERE user_id = $1;''', userinfo['user_id'])
        modifiers_string_list = {"Wool Mod": modifiers['wool_mod'],
                                 "Fish Mod": modifiers['fish_mod'],
                                 "Fur Mod": modifiers['fur_mod'],
                                 "Grain Mod": modifiers['grain_mod'],
                                 "Livestock Mod": modifiers['livestock_mod'],
                                 "Salt Mod": modifiers['salt_mod'],
                                 "Wine Mod": modifiers['wine_mod'],
                                 "Copper Mod": modifiers['copper_mod'],
                                 "Iron Mod": modifiers['iron_mod'],
                                 "Precious Goods Mod": modifiers['precious_goods_mod'],
                                 "Spices Mod": modifiers['spices_mod'],
                                 "Tea And Coffee Mod": modifiers['tea_and_coffee_mod'],
                                 "Chocolate Mod": modifiers['chocolate_mod'],
                                 "Cotton Mod": modifiers['cotton_mod'],
                                 "Sugar Mod": modifiers['sugar_mod'],
                                 "Tobacco Mod": modifiers['tobacco_mod'],
                                 "Dyes Mod": modifiers['dyes_mod'],
                                 "Silk Mod": modifiers['silk_mod'],
                                 "Rare Wood Mod": modifiers['rare_wood_mod'],
                                 "Glass Mod": modifiers['glass_mod'],
                                 "Paper Mod": modifiers['paper_mod'],
                                 "Precious Stones Mod": modifiers['precious_stones_mod'],
                                 "Coal Mod": modifiers['coal_mod'],
                                 "Fruits Mod": modifiers['fruits_mod'],
                                 "Raw Stone Mod": modifiers['raw_stone_mod'],
                                 "Wood Mod": modifiers['wood_mod'],
                                 "Tin Mod": modifiers['tin_mod'],
                                 "Ivory Mod": modifiers['ivory_mod'],
                                 "Income Mod": modifiers['income_mod'],
                                 "Workshop Production Mod": modifiers['workshop_production_mod'],
                                 "Production Mod": modifiers['production_mod'],
                                 "Trade Route": modifiers['trade_route'],
                                 "Trade Route Efficiency Mod": modifiers['trade_route_efficiency_mod'],
                                 "National Unrest Suppression Mod": modifiers[
                                     'national_unrest_suppression_efficiency_mod'],
                                 "Local Unrest Suppression Efficiency Mod": modifiers[
                                     'local_unrest_suppression_efficiency_mod'],
                                 "Defense Level": modifiers['defense_level'],
                                 "Attack Level": modifiers['attack_level'],
                                 "Movement Cost Mod": modifiers['movement_cost_mod'],
                                 "Army Limit": modifiers['army_limit'],
                                 "Manpower Gain Mod": modifiers['manpower_mod'],
                                 "Troop Upkeep Mod": modifiers['troop_upkeep_mod'],
                                 "Research Speed Mod": modifiers['research_mod']}
        tech_string = ""
        for mod, value in modifiers_string_list.items():
            tech_string += f"`{mod}"
            for n in range(50 - len(mod)):
                tech_string += " "
            tech_string += f"` `{value}`"
            tech_string += "\n"
        te_embed = discord.Embed(title="Technology Modifiers", description=tech_string)
        await ctx.author.send(embed=te_embed)
        if ctx.guild is not None:
            await ctx.send("Sent!")

    @commands.command(brief="Sends information about an event.", usage="<event name>")
    async def cnc_event(self, ctx, *, args = None):
        event = Events(ctx=ctx, event=args)
        await event.event_info()

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
            if province['occupier'] == '':
                occupier = 'Rebels'
            else:
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
        provinceembed.add_field(name="Trade Good", value=province['value'])
        provinceembed.add_field(name="Production", value=province['production'])
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
        await conn.execute('''UPDATE provinces SET owner = '', owner_id = 0, occupier = '', occupier_id = 0,
         troops = $2 WHERE id = $1;''', provinceid, troops)
        await conn.execute('''UPDATE cncusers SET undeployed = $1 WHERE user_id = $3;''',
                           provinceinfo['troops'], author.id)
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
        await conn.execute('''UPDATE provinces  SET troops = 0 WHERE id = $1;''', provinceid)
        await conn.execute('''UPDATE cncusers SET undeployed = undeployed + $1 WHERE user_id = $3;''',
                           provinceinfo['troops'], author.id)
        # adds province to recipient
        recipientinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE lower(username) = $1;''',
                                            recipient.lower())
        # sets province owner info
        await conn.execute('''UPDATE provinces  SET owner = $1, owner_id = $2, occupier = $1, occupier_id = $2
         WHERE id = $3;''', recipientinfo['username'], recipientinfo['user_id'], provinceid)
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
            # fetch all interactions
            interactions = await conn.fetch('''SELECT * FROM interactions WHERE (sender_id = $1 OR recipient_id = $1) 
            ORDER BY id DESC;''', author.id)
            # build interactions text
            interactions_text = ''
            for i in interactions:
                interactions_text += f"Interaction ID: {i['id']}\n"
                interactions_text += f"Sender: {i['sender']}\n"
                interactions_text += f"Recipient: {i['recipient']}\n"
                interactions_text += f"Type: {i['type']}\n"
                interactions_text += f"Terms: {i['terms']}\n"
                interactions_text += f"Active: {i['active']}\n\n"
            with open(f"{self.interaction_directory}{author.id}.txt", "w") as interactions_file:
                interactions_file.write(interactions_text)
            with open(f"{self.interaction_directory}{author.id}.txt", "rb") as interactions_file:
                await author.send(file=discord.File(interactions_file, f"Interactions Log for {author.id}.txt"))
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
            with open(f"{self.interaction_directory}{interaction['id']}.txt", "w") as interaction_file:
                interaction_file.write(interaction['terms'])
                interaction_file.close()
                await ctx.send(file=discord.File(interaction_file, f"{interaction['id']}.txt"))

    @commands.command(usage="[offer id]", brief="Displays a specific offer with information")
    async def cnc_offer(self, ctx, offerid: int):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        offer = await conn.fetchrow('''SELECT * FROM pending_interactions WHERE id = $1;''', offerid)
        # if there is no such offer, say so
        if offer is None:
            await ctx.send("No such pending offer.")
            return
        # if the user is not authorized to view that offer
        if offer['sender_id'] != author.id and offer['recipient_id'] != author.id:
            await ctx.send("You are not authorized to view that offer.")
            return
        # if the terms are longer than 1024 characters, upload a file
        upload = False
        if len(offer['terms']) > 1024:
            terms = "See File Upload"
            upload = True
        else:
            terms = offer['terms']
        # create and send the embed + file if necessary
        embed = discord.Embed(title=f"Offer #{offer['id']}",
                              description=f"An offer of {offer['type']} from {offer['sender']}.")
        embed.add_field(name="Offer Type", value=f"{offer['type'].title()}")
        embed.add_field(name="Sender", value=f"{offer['sender']}")
        embed.add_field(name="Terms", value=f"{terms}", inline=False)
        await ctx.send(embed=embed)
        if upload is True:
            with open(f"{self.interaction_directory}{offer['id']}.txt", "w") as offer_file:
                offer_file.write(offer['terms'])
            with open(f"{self.interaction_directory}{offer['id']}.txt", "w") as offer_file:
                await ctx.send(file=discord.File(offer_file, f"{offer['id']}.txt"))

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
                    if sender_occupied:
                        owner_color = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1;''',
                                                          pending_int['recipient'])
                        owner_color = owner_color['usercolor']
                        troops = 0
                        for p in sender_occupied:
                            await self.bot.loop.run_in_executor(None, self.map_color, p['id'], p['cord'], owner_color)
                            await conn.execute(
                                '''UPDATE provinces SET occupier = $1, occupier_id = $2 WHERE id = $3;''',
                                p['owner'], p['owner_id'], p['id'])
                            troops += p['troops']
                        await conn.execute('''UPDATE cncusers SET undeployed = $1 WHERE user_id = $2;''',
                                           troops + owner_color['undeployed'], owner_color['user_id'])
                    if recip_occupied:
                        owner_color = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1;''',
                                                          pending_int['sender'])
                        owner_color = owner_color['usercolor']
                        troops = 0
                        for p in recip_occupied:
                            await self.bot.loop.run_in_executor(None, self.map_color, p['id'], p['cord'], owner_color)
                            await conn.execute(
                                '''UPDATE provinces SET occupier = $1, occupier_id = $2 WHERE id = $3;''',
                                p['owner'], p['owner_id'], p['id'])
                            troops += p['troops']
                        await conn.execute('''UPDATE cncusers SET undeployed = $1 WHERE user_id = $2;''',
                                           troops + owner_color['undeployed'], owner_color['user_id'])
                # get user object and send message
                sender = self.bot.get_user(pending_int['sender_id'])
                await sender.send(
                    f"{pending_int['recipient']} has accepted your offer of a(n) {pending_int['type']}. "
                    f"To view this, use `$cnc_view_interaction {interactionid}`.")
                await ctx.send("Accepted.")
            if interaction.lower() == "reject":
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
                await ctx.send("Wars must be resolved using the peace command.")
                return
            # ensures authority
            if (interact['recipient_id'] != author.id) and (interact['sender_id'] != author.id) and (
                    not self.bot.is_owner(author)):
                await ctx.send("You are not authorized to cancel that interaction.")
                return
            sender = interact['sender']
            recipient = interact['recipient']
            # updates interaction data
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
            raise commands.UserInputError
        rrecipient = data[0]
        text = data[1]
        text = text.lstrip(' ')
        if text == "":
            raise commands.UserInputError
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
        # ensures no alliance and no existing war
        relations = await conn.fetch('''SELECT * FROM interactions 
        WHERE (sender = $1 and recipient = $2) or (sender = $2 and recipient = $1) AND active = True;''',
                                     sender, recipient)
        for r in relations:
            if r['type'] == 'war':
                await ctx.send(
                    f"It is not possible to declare war on {recipient} when you are already at war with them!")
                return
            elif r['type'] == 'alliance':
                await ctx.send(f"It is not possible to declare war on {recipient} when you have an alliance with them!")
                return
        # inserts information into interactions
        await conn.execute('''INSERT INTO interactions (id, type, sender, sender_id, recipient,
                recipient_id, terms, active) VALUES($1, $2, $3, $4, $5, $6, $7, $8);''', aid, atype, sender,
                           sender_id,
                           recipient,
                           recipient_id, terms, True)
        # updates trade routes
        trade_interactions = await conn.fetch('''SELECT * FROM interactions WHERE (type = 'trade' AND 
                                active = True) AND (sender = $1 AND recipient = $2 OR sender = $2 AND recipient = $1);''',
                                              sender, recipient)
        for t in trade_interactions:
            await conn.execute('''UPDATE interactions SET active = False WHERE id = $1;''', t['id'])
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
        if text == "":
            raise commands.UserInputError
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
        war = await conn.fetch('''SELECT * FROM interactions 
        WHERE (sender = $1 and recipient = $2) or (sender = $2 and recipient = $1) 
        AND active = True AND type = 'war';''', sender, recipient)
        if war is None:
            await ctx.send(f"You cannot negotiate peace with {sender} if you are not at war!")
            return
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
        # pulls data for the recipient
        recipient = args
        recip_info = await conn.fetchrow('''SELECT * FROM cncusers WHERE lower(username) = $1;''',
                                         recipient.lower())
        # if the recipient doesn't exist
        if recip_info is None:
            await ctx.send(f"`{recipient}` does not appear to be registered.")
            return
        # if the sender does not have enough moves
        if userinfo['moves'] <= 0:
            await ctx.send("You do not have enough action points for that!")
            return
        # if the user has the maximum outgoing trade routes
        trade_route_count = await conn.fetchrow('''SELECT count(*) FROM interactions 
        WHERE type = 'trade' AND sender_id = $1 AND active = True;''', author.id)
        if trade_route_count['count'] is None:
            trade_route_count = 0
        else:
            trade_route_count = trade_route_count['count']
        if userinfo['trade_route_limit'] <= trade_route_count:
            await ctx.send("You do not have enough available trade routes to establish a new one.")
            return
        pending_route = await conn.fetchrow('''SELECT * FROM pending_interactions 
        WHERE sender_id = $1 AND recipient = $2 AND type = 'trade';''', author.id, recip_info['username'])
        if pending_route is not None:
            await ctx.send(f"You have a trade route offer already pending for {recip_info['username']}.")
            return
        war = await conn.fetch('''SELECT * FROM interactions 
        WHERE (sender = $1 and recipient = $2) or (sender = $2 and recipient = $1) 
        AND active = True AND type = 'war';''', userinfo['username'], recipient)
        if war is not None:
            await ctx.send("You cannot send a trade route to someone you are at war with!")
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
            # define city, port, and trade route limit information
            trade_route_limit = userinfo['trade_route_limit']
            # fetch modifiers
            modifiers = await conn.fetchrow('''SELECT * FROM cnc_modifiers WHERE user_id = $1;''', userinfo['user_id'])
            # fetch outgoing trade route information
            outgoing_count = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE type = 'trade' AND 
                                          active = True AND sender_id = $1;''', userinfo['user_id'])
            outgoing_info = await conn.fetchrow('''SELECT * FROM interactions WHERE type = 'trade' AND 
                                          active = True AND sender_id = $1;''', userinfo['user_id'])
            if outgoing_count['count'] is None:
                outgoing_count = 0
            else:
                outgoing_count = outgoing_count['count']
            # fetch incoming trade route information
            incoming_count = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE type = 'trade' AND 
                                                         active = True AND recipient_id = $1;''', userinfo['user_id'])
            if incoming_count['count'] is None:
                incoming_count = 0
            else:
                incoming_count = incoming_count['count']
            # if the outgoing count is over the trade route limit, add a debuff
            trade_debuff = 1
            if outgoing_count > trade_route_limit:
                for i in range(trade_route_limit - outgoing_count):
                    trade_debuff -= .02
            # define initial trade access
            initial_trade_access = 0.5
            # for every domestic trade route, +10% access. For every foreign trade route, +5% access
            if outgoing_count != 0:
                outgoing_recipients = list()
                for o in outgoing_info:
                    outgoing_recipients.append(o['recipient'])
                outgoing_repeat = Counter(outgoing_recipients)
                # for every repeat trade route, decrease by 2% down to 0%
                for r in outgoing_repeat:
                    if r >= 6:
                        initial_trade_access = .3
                    else:
                        initial_trade_access += (10 - (r - 1) * r) / 100 * (
                            modifiers['trade_route_efficiency_mod'])
            # calculate initial trade access
            initial_trade_access += (.05 * incoming_count) * trade_debuff
            # creates the projected resource gain data
            manpower = userinfo['manpower']
            taxation = userinfo['taxation']
            military_upkeep = userinfo['military_upkeep']
            public_services = userinfo['public_services']
            base_gain = 0
            tax_gain = manpower * (taxation / 100)
            tax_gain -= tax_gain * (military_upkeep / 100)
            tax_gain -= tax_gain * (public_services / 100)
            tax_gain = math.floor(tax_gain)
            # adds trade gain and subtracts troop upkeep
            total_troops = 0
            production_gain = 0
            workshops = 0
            products = list()
            provinces_owned = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1 and occupier_id = $1;''',
                                               author.id)
            if provinces_owned is None:
                provinces_owned = 0
            for p in provinces_owned:
                if p == 0:
                    break
                p_info = p
                if p_info['occupier_id'] != author.id:
                    continue
                total_troops += p_info['troops']
                # for every province, calculate local trade value
                # define production value, producing amount, market value modifiers, and workshop production
                production_value = 1
                market_value_mod = 1
                workshop_production = 0
                # for every city, add .5 production
                if p_info['city']:
                    production_value += 0.5
                # for every port, add 25% market value to the local good, if it is not gold or silver
                if p_info['port']:
                    if p_info['value'] not in ['Gold', 'Silver']:
                        market_value_mod += 0.25
                # for every workshop, add 1 * the production modifier
                if p_info['workshop']:
                    workshops += 1
                    workshop_production += 1 * modifiers['workshop_production_mod']
                # add all production to the base province production
                producing = p_info['production'] * (production_value + modifiers['production_mod'])
                # calculate local trade good value and total gain
                trade_good = await conn.fetchrow('''SELECT * FROM trade_goods WHERE name = $1;''', p_info['value'])
                products.append(p_info['value'])
                production_gain += (((trade_good['market_value'] +
                                      modifiers[f'{self.space_replace(p_info["value"]).lower()}_mod']) *
                                     market_value_mod) * producing) * initial_trade_access
                production_gain = math.floor(production_gain)
            # remove duplicate trade goods and create string
            products = list(dict.fromkeys(products))
            if len(products) == 0:
                products_string = "None"
            else:
                products_string = ", ".join(products)
            # troop upkeep cost
            troop_maintenance = total_troops * (0.01 * (modifiers['attack_level'] + modifiers['defense_level']))
            troop_maintenance = math.floor(troop_maintenance)
            # structure upkeep cost
            structure_cost = 0
            fortlimit = userinfo['fortlimit']
            portlimit = userinfo['portlimit']
            citylimit = userinfo['citylimit']
            cities = await conn.fetchrow(
                '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND city = True;''',
                userinfo['user_id'])
            ports = await conn.fetchrow(
                '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND port = True;''',
                userinfo['user_id'])
            forts = await conn.fetchrow(
                '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND fort = True;''',
                userinfo['user_id'])
            if cities['count'] > citylimit:
                structure_cost += 1000 * (cities['count'] - citylimit)
            if ports['count'] > portlimit:
                structure_cost += 500 * (ports['count'] - portlimit)
            if forts['count'] > fortlimit:
                structure_cost += 700 * (forts['count'] - fortlimit)
            # add gain
            base_gain += production_gain + tax_gain - troop_maintenance - structure_cost
            # sends the embed
            bankembed = discord.Embed(title=f"{userinfo['username']} - War Chest",
                                      description="An overview of the resource status of a nation.")
            bankembed.add_field(name="Current Resources", value=f"\u03FE{userinfo['resources']:,}", inline=False)
            bankembed.add_field(name="Total Projected Gain", value=f"\u03FE{int(math.ceil(base_gain)):,}")
            bankembed.add_field(name="Production Gain", value=f"\u03FE{int(production_gain):,}")
            bankembed.add_field(name="Tax Gain", value=f"\u03FE{int(tax_gain):,}")
            bankembed.add_field(name="Troop Maintenance Cost", value=f"\u03FE{int(troop_maintenance):,}")
            bankembed.add_field(name="Structure Maintenance Cost", value=f"\u03FE{int(structure_cost):,}")
            bankembed.add_field(name="\u200b", value="\u200b")
            bankembed.add_field(name="Trade Routes", value=f"{outgoing_count + incoming_count}")
            bankembed.add_field(name="Trade Access", value=f"{initial_trade_access * 100}%")
            bankembed.add_field(name="\u200b", value="\u200b")
            bankembed.add_field(name="Cities", value=cities['count'])
            bankembed.add_field(name="Ports", value=ports['count'])
            bankembed.add_field(name="Workshops", value=str(workshops))
            bankembed.add_field(name="National Products", value=products_string)
            await ctx.send(embed=bankembed)
        else:
            # if a nation is specified, fetch that information
            userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE lower(username) = $1;''', nationname.lower())
            # verifies user existance
            if userinfo is None:
                await ctx.send(f"No such nation as {nationname}.")
                return
            # define city, port, and trade route limit information
            trade_route_limit = userinfo['trade_route_limit']
            # fetch modifiers
            modifiers = await conn.fetchrow('''SELECT * FROM cnc_modifiers WHERE user_id = $1;''',
                                            userinfo['user_id'])
            # fetch outgoing trade route information
            outgoing_count = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE type = 'trade' AND 
                                                 active = True AND sender_id = $1;''', userinfo['user_id'])
            outgoing_info = await conn.fetchrow('''SELECT * FROM interactions WHERE type = 'trade' AND 
                                                 active = True AND sender_id = $1;''', userinfo['user_id'])
            if outgoing_count['count'] is None:
                outgoing_count = 0
            else:
                outgoing_count = outgoing_count['count']
            # fetch incoming trade route information
            incoming_count = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE type = 'trade' AND 
                                                                active = True AND recipient_id = $1;''',
                                                 userinfo['user_id'])
            if incoming_count['count'] is None:
                incoming_count = 0
            else:
                incoming_count = incoming_count['count']
            # if the outgoing count is over the trade route limit, add a debuff
            trade_debuff = 1
            if outgoing_count > trade_route_limit:
                for i in range(trade_route_limit - outgoing_count):
                    trade_debuff -= .02
            # define initial trade access
            initial_trade_access = 0.5
            # for every domestic trade route, +10% access. For every foreign trade route, +5% access
            if outgoing_count != 0:
                outgoing_recipients = list()
                for o in outgoing_info:
                    outgoing_recipients.append(o['recipient'])
                outgoing_repeat = Counter(outgoing_recipients)
                # for every repeat trade route, decrease by 2% down to 0%
                for r in outgoing_repeat:
                    if r >= 6:
                        initial_trade_access = .3
                    else:
                        initial_trade_access += (10 - (r - 1) * r) / 100 * (
                            modifiers['trade_route_efficiency_mod'])
            # calculate initial trade access
            initial_trade_access += (.05 * incoming_count) * trade_debuff
            # creates the projected resource gain data
            manpower = userinfo['manpower']
            taxation = userinfo['taxation']
            military_upkeep = userinfo['military_upkeep']
            public_services = userinfo['public_services']
            base_gain = 0
            tax_gain = manpower * (taxation / 100)
            tax_gain -= tax_gain * (military_upkeep / 100)
            tax_gain -= tax_gain * (public_services / 100)
            tax_gain = math.floor(tax_gain)
            # adds trade gain and subtracts troop upkeep
            total_troops = 0
            production_gain = 0
            workshops = 0
            products = list()
            provinces_owned = await conn.fetch(
                '''SELECT * FROM provinces WHERE owner_id = $1 and occupier_id = $1;''',
                author.id)
            if provinces_owned is None:
                provinces_owned = 0
            for p in provinces_owned:
                if p == 0:
                    break
                p_info = p
                if p_info['occupier_id'] != author.id:
                    continue
                total_troops += p_info['troops']
                # for every province, calculate local trade value
                # define production value, producing amount, market value modifiers, and workshop production
                production_value = 1
                market_value_mod = 1
                workshop_production = 0
                # for every city, add .5 production
                if p_info['city']:
                    production_value += 0.5
                # for every port, add 25% market value to the local good, if it is not gold or silver
                if p_info['port']:
                    if p_info['value'] not in ['Gold', 'Silver']:
                        market_value_mod += 0.25
                # for every workshop, add 1 * the production modifier
                if p_info['workshop']:
                    workshops += 1
                    workshop_production += 1 * modifiers['workshop_production_mod']
                # add all production to the base province production
                producing = p_info['production'] * (production_value + modifiers['production_mod'])
                # calculate local trade good value and total gain
                trade_good = await conn.fetchrow('''SELECT * FROM trade_goods WHERE name = $1;''', p_info['value'])
                products.append(p_info['value'])
                production_gain += (((trade_good['market_value'] +
                                      modifiers[f'{self.space_replace(p_info["value"]).lower()}_mod']) *
                                     market_value_mod) * producing) * initial_trade_access
                production_gain = math.floor(production_gain)
            # remove duplicate trade goods and create string
            products = list(dict.fromkeys(products))
            if len(products) == 0:
                products_string = "None"
            else:
                products_string = ", ".join(products)
            # troop upkeep cost
            troop_maintenance = total_troops * (0.01 * (modifiers['attack_level'] + modifiers['defense_level']))
            troop_maintenance = math.floor(troop_maintenance)
            # structure upkeep cost
            structure_cost = 0
            fortlimit = userinfo['fortlimit']
            portlimit = userinfo['portlimit']
            citylimit = userinfo['citylimit']
            cities = await conn.fetchrow(
                '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND city = True;''',
                userinfo['user_id'])
            ports = await conn.fetchrow(
                '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND port = True;''',
                userinfo['user_id'])
            forts = await conn.fetchrow(
                '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND fort = True;''',
                userinfo['user_id'])
            if cities['count'] > citylimit:
                structure_cost += 1000 * (cities['count'] - citylimit)
            if ports['count'] > portlimit:
                structure_cost += 500 * (ports['count'] - portlimit)
            if forts['count'] > fortlimit:
                structure_cost += 700 * (forts['count'] - fortlimit)
            # add gain
            base_gain += production_gain + tax_gain - troop_maintenance - structure_cost
            # sends the embed
            bankembed = discord.Embed(title=f"{userinfo['username']} - War Chest",
                                      description="An overview of the resource status of a nation.")
            bankembed.add_field(name="Current Resources", value=f"\u03FE{userinfo['resources']:,}", inline=False)
            bankembed.add_field(name="Total Projected Gain", value=f"\u03FE{int(math.ceil(base_gain)):,}")
            bankembed.add_field(name="Production Gain", value=f"\u03FE{int(production_gain):,}")
            bankembed.add_field(name="Tax Gain", value=f"\u03FE{int(tax_gain):,}")
            bankembed.add_field(name="Troop Maintenance Cost", value=f"\u03FE{int(troop_maintenance):,}")
            bankembed.add_field(name="Structure Maintenance Cost", value=f"\u03FE{int(structure_cost):,}")
            bankembed.add_field(name="\u200b", value="\u200b")
            bankembed.add_field(name="Trade Routes", value=f"{outgoing_count + incoming_count}")
            bankembed.add_field(name="Trade Access", value=f"{initial_trade_access * 100}%")
            bankembed.add_field(name="\u200b", value="\u200b")
            bankembed.add_field(name="Cities", value=cities['count'])
            bankembed.add_field(name="Ports", value=ports['count'])
            bankembed.add_field(name="Workshops", value=str(workshops))
            bankembed.add_field(name="National Products", value=products_string)
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
        modifiers = await conn.fetchrow('''SELECT * FROM cnc_modifiers WHERE user_id = $1;''', author.id)
        troop_count = await conn.fetchrow('''SELECT sum(troops) FROM provinces WHERE occupier_id = $1;''', author.id)
        nationname = userinfo['username']
        monies = userinfo['resources']
        manpower = ramount * 1000
        cost = ramount * (1000 * (modifiers['attack_level'] + modifiers['defense_level']))
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
                f"{nationname} does not have enough resources to purchase {ramount * 1000:,} troops at \u03FE{cost}.")
            return
        # if the nation does not have enough manpower
        elif manpower > userinfo['manpower']:
            await ctx.send(f"{nationname} does not have enough manpower to recruit {ramount * 1000:,} troops, "
                           f"lacking {-(userinfo['manpower'] - manpower)} manpower. ")
            return
        elif ramount * 1000 + troop_count['sum'] > modifiers['army_limit']:
            await ctx.send(f"{userinfo['username']} cannot recruit that many troops. "
                           f"The troop cap is {modifiers['army_limit']}.")
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
                f"{nationname} has recruited {ramount * 1000:,} troops to their recruitment pool. "
                f"\u03FE{cost} have been spent.")
            return
        else:
            # fetches all province ids and makes them into a list
            province = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', location)
            if province is None:
                await ctx.send(f"`{location}` is not a valid province ID.")
                return
            # if the location is not owned by the user
            if province['owner_id'] != author.id and province['occupier_id'] != author.id:
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
        await ctx.send(f"{nationname} has successfully deployed {ramount * 1000:,} to Province #{location}. "
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
        modifiers = await conn.fetchrow('''SELECT * FROM cnc_modifiers WHERE user_id = $1;''', author.id)
        provinces_owned = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1 and occupier_id = $1;''',
                                           author.id)
        if provinces_owned is None:
            await ctx.send("You own 0 provinces.")
            return
        else:
            provinces_owned = [p['id'] for p in provinces_owned]
        amount *= 1000
        manpower = amount * len(provinces_owned)
        cost = (amount * (modifiers['attack_level'] + modifiers['defense_level'])) * len(provinces_owned)
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
        for p in provinces_owned:
            troops = await conn.fetchrow('''SELECT troops FROM provinces  WHERE id = $1;''', p)
            await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                               (troops['troops'] + amount),
                               p)
        await ctx.send(
            f"{userinfo['username']} has succssfully deployed {amount} troops to all {len(provinces_owned)} provinces.")

    @commands.command(usage="[troop amount]", brief="Disbands a specified number of undeployed troops.")
    @commands.guild_only()
    async def cnc_disband(self, ctx, amount: int):
        # connects to database
        conn = self.bot.pool
        # defines author
        author = ctx.author
        # fetches userinfo
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        if userinfo is None:
            await ctx.send("You are not registered.")
            return
        # define undeployed and check for enough undeployed troops
        undeployed = userinfo['undeployed']
        if amount > undeployed:
            await ctx.send(f"{userinfo['username']} does not have {amount:,} undeployed troops.")
            return
        else:
            await conn.execute('''UPDATE cncusers SET undeployed = undeployed - $1 WHERE user_id = $2;''',
                               amount, author.id)
            await ctx.send(f"{userinfo['username']} as disbanded {amount:,} troops.")
            return

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

    # @commands.command(usage="[province id]", brief="Purchases a specified province")
    # @commands.guild_only()
    # async def cnc_purchase(self, ctx, provinceid: int):
    #     loop = asyncio.get_running_loop()
    #     author = ctx.author
    #     # connects to the database
    #     conn = self.bot.pool
    #     # fetches all user ids
    #     allusers = await conn.fetch('''SELECT user_id FROM cncusers''')
    #     alluserids = list()
    #     for id in allusers:
    #         alluserids.append(id['user_id'])
    #     # ensures author registration
    #     if author.id not in alluserids:
    #         await ctx.send(f"{author} not registered.")
    #         return
    #     # fetches all province ids
    #     allprovinces = await conn.fetch('''SELECT id FROM provinces''')
    #     allids = list()
    #     for pid in allprovinces:
    #         allids.append(pid['id'])
    #     # ensures province validity
    #     if provinceid not in allids:
    #         await ctx.send(f"Location id `{provinceid}` is not a valid ID.")
    #         return
    #     # fetches province and user information
    #     provinceowner = await conn.fetchrow('''SELECT * FROM provinces  WHERE id = $1;''', provinceid)
    #     userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1''', author.id)
    #     provinces_owned = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1 and occupier_id = $1;''',
    #                                        author.id)
    #     if provinces_owned is None:
    #         provinces_owned = [0]
    #     else:
    #         provinces_owned = [p['id'] for p in provinces_owned]
    #     cost = 3000
    #     # checks for economic focus
    #     if userinfo['focus'] == "e":
    #         cost = 3000 * uniform(.89, .99)
    #     # ensures user disownership
    #     if provinceid in provinces_owned:
    #         await ctx.send(f"{userinfo['username']} already owns Province #{provinceid}")
    #         return
    #     # ensures province availability
    #     elif provinceowner['owner_id'] != 0:
    #         await ctx.send(f"Province #{provinceid} is already owned!")
    #         return
    #     # ensures province's coastal proximity
    #     elif provinceowner['coast'] is False:
    #         await ctx.send(f"Province #{provinceid} is not a coastal province and cannot be purchased!")
    #         return
    #     # ensures resource sufficiency
    #     elif userinfo['resources'] < cost:
    #         difference = cost - userinfo['resources']
    #         await ctx.send(
    #             f"{userinfo['username']} possesses {math.ceil(difference)} fewer credit resources than needed to buy a province.")
    #         return
    #     # ensures that the user has less than 3 provinces
    #     elif len(provinces_owned) >= 2:
    #         await ctx.send(f"{userinfo['username']} already controls enough provinces and is not eligible to "
    #                        f"purchase another.")
    #         return
    #     else:
    #         # updates all relevant information
    #         await conn.execute('''UPDATE provinces  SET owner = $1, owner_id = $2, occupier = $1, occupier_id = $2,
    #         troops = 0 WHERE id = $3;''',
    #                            userinfo['username'], author.id, provinceid)
    #         await conn.execute('''UPDATE cncusers SET resources = $1 WHERE user_id = $2;''',
    #                            (userinfo['resources'] - cost), author.id)
    #         await ctx.send(f"{userinfo['username']} has purchased Province #{provinceid} successfully!")
    #         await loop.run_in_executor(None, self.map_color, provinceid, provinceowner['cord'][0:2],
    #                                    userinfo['usercolor'])
    #         return

    @commands.command(usage="[province id] [structure (fort, port, city, workshop, temple, capital, move_capital)]",
                      brief="Constructs a building in a specified province")
    @commands.guild_only()
    async def cnc_construct(self, ctx, provinceid: int, structure: str):
        author = ctx.author
        # connects to the database
        conn = self.bot.pool
        # fetches user info
        userinfo = await conn.fetchrow('''SELECT user_id FROM cncusers WHERE user_id = $1;''', author.id)
        if userinfo is None:
            await ctx.send(f"{author} not registered.")
            return
        # fetches all province ids
        p_info = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', provinceid)
        # ensures province validity
        if p_info is None:
            await ctx.send(f"Location id `{provinceid}` is not a valid ID.")
            return
        # fetches province and user information
        provinces_owned = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1 and occupier_id = $1;''',
                                           author.id)
        provinces_owned = [p['id'] for p in provinces_owned]
        # if the user does not own the provinces
        if provinceid not in provinces_owned:
            await ctx.send(f"{userinfo['username']} does not own Province #{provinceid}!")
            return
        # gathers city, port, and fort info
        cities = await conn.fetchrow(
            '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND city = True;''',
            userinfo['user_id'])
        ports = await conn.fetchrow(
            '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND port = True;''',
            userinfo['user_id'])
        forts = await conn.fetchrow(
            '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND fort = True;''',
            userinfo['user_id'])
        # checks input
        if structure.lower() not in ['fort', 'port', 'city', 'workshop', 'temple', 'capital', 'move_capital']:
            raise commands.UserInputError
        if structure.lower() == 'port':
            if "Dockyards" not in userinfo['researched']:
                await ctx.send("Constructing a port requires the Dockyards technology.")
                return
            pcost = 15000
            if p_info['coast'] is False:
                await ctx.send(f"Province #{provinceid} is not a coastal province.")
                return
            elif ports['count'] >= userinfo['portlimit']:
                await ctx.send(f"{userinfo['username']} has reached its port building limit.")
                return
            if userinfo['focus'] == "e":
                pcost = math.ceil(15000 * uniform(.89, .99))
            if userinfo['resources'] < pcost:
                difference = pcost - userinfo['resources']
                await ctx.send(f"{userinfo['username']} does not have enough credit resources to build a port."
                               f"\n**Resource Deficit:** \u03FE{math.ceil(difference):,}")
                return
            elif p_info['port'] is True:
                await ctx.send(f"Province #{provinceid} already has a port constructed!")
                return
            elif p_info['terrain'] == 5:
                await ctx.send("It is impossible to build a port on a mountain!")
                return
            else:
                await conn.execute('''UPDATE provinces  SET port = TRUE WHERE id = $1;''', provinceid)
                await conn.execute('''UPDATE cncusers SET resources = resources - $1 WHERE user_id = $2;''',
                                   pcost, author.id)
                await ctx.send(
                    f"{userinfo['username']} successfully constructed a port in province #{provinceid}.")
                return
        if structure.lower() == 'city':
            if "Cities" not in userinfo['researched']:
                await ctx.send("Constructing a city requires the Cities technology.")
            ccost = 30000
            if userinfo['resources'] < ccost:
                difference = ccost - userinfo['resources']
                await ctx.send(f"{userinfo['username']} does not have enough credit resources to build a city."
                               f"\n**Resource Deficit:** \u03FE{math.ceil(difference):,}")
                return
            elif cities['count'] >= userinfo['citylimit']:
                await ctx.send(f"{userinfo['username']} has reached its city building limit.")
                return
            elif p_info['city'] is True:
                await ctx.send(f"Province #{provinceid} already has a city constructed!")
                return
            elif p_info['terrain'] == 5:
                await ctx.send("It is impossible to build a port on a mountain!")
                return
            else:
                await conn.execute('''UPDATE provinces  SET city = TRUE WHERE id = $1;''',
                                   provinceid)
                await conn.execute('''UPDATE cncusers SET resources = resources - $1 WHERE user_id = $2;''',
                                   ccost, author.id)
                await ctx.send(
                    f"{userinfo['username']} successfully constructed a city in province #{provinceid}.")
                return
        if structure.lower() == 'fort':
            if "Fortifications" not in userinfo['researched']:
                await ctx.send("Constructing a fort requires the Fortifications technology.")
            fcost = 12500
            if userinfo['focus'] == "s":
                fcost = math.ceil(12500 * uniform(.89, .99))
            if userinfo['resources'] < fcost:
                difference = fcost - userinfo['resources']
                await ctx.send(f"{userinfo['username']} does not have enough credit resources to build a fort."
                               f"\n**Resource Deficit:** \u03FE{math.ceil(difference):,}")
                return
            elif forts['count'] >= userinfo['fortlimit']:
                await ctx.send(f"{userinfo['username']} has reached its fort building limit.")
                return
            elif p_info['fort'] is True:
                await ctx.send(f"Province #{provinceid} already has a fort constructed!")
                return
            elif p_info['terrain'] == 5:
                await ctx.send("Mountainous terrains are impossible to build forts on!")
                return
            else:
                await conn.execute('''UPDATE provinces  SET fort = TRUE WHERE id = $1;''', provinceid)
                await conn.execute('''UPDATE cncusers SET resources = resources - $1 WHERE user_id = $2;''',
                                   fcost, author.id)
                await ctx.send(
                    f"{userinfo['username']} successfully constructed a fort in province #{provinceid}.")
                return
        if structure.lower() == 'workshop':
            if "Workshops" not in userinfo['researched']:
                await ctx.send("Constructing a workshop requires the Workshops technology.")
                return
            cost = 20000
            if userinfo['focus'] == "e":
                cost = math.ceil(20000 * uniform(.89, .99))
            if userinfo['resources'] < cost:
                difference = cost - userinfo['resources']
                await ctx.send(f"{userinfo['username']} does not have enough credit resources to build a workshop."
                               f"\n**Resource Deficit:** \u03FE{math.ceil(difference):,}")
                return
            elif p_info['workshop'] is True:
                await ctx.send(f"Province #{provinceid} already has a workshop constructed!")
                return
            elif p_info['terrain'] == 5:
                await ctx.send("Mountainous terrains are impossible to build on!")
                return
            else:
                await conn.execute('''UPDATE cncusers SET resources = resrouces - $1 WHERE user_id = $2;''',
                                   cost, userinfo['user_id'])
                await conn.execute('''UPDATE provinces SET workshop = TRUE WHERE id = $1;''', provinceid)
                await ctx.send(
                    f"{userinfo['username']} successfully constructed a workshop in province #{provinceid}.")
                return
        if structure.lower() == 'temple':
            if "Temples" not in userinfo['researched']:
                await ctx.send("Constructing a temple requires the Temples technology.")
                return
            cost = 10000
            if userinfo['focus'] == "s":
                cost = math.ceil(10000 * uniform(.89, .99))
            if userinfo['resources'] < cost:
                difference = cost - userinfo['resources']
                await ctx.send(f"{userinfo['username']} does not have enough credit resources to build a temple."
                               f"\n**Resource Deficit:** \u03FE{math.ceil(difference):,}")
                return
            elif p_info['temple'] is True:
                await ctx.send(f"Province #{provinceid} already has a temple constructed!")
                return
            elif p_info['terrain'] == 5:
                await ctx.send("Mountainous terrains are impossible to build on!")
                return
            else:
                await conn.execute('''UPDATE cncusers SET resources = resrouces - $1 WHERE user_id = $2;''',
                                   cost, userinfo['user_id'])
                await conn.execute('''UPDATE provinces SET workshop = TRUE WHERE id = $1;''', provinceid)
                await ctx.send(
                    f"{userinfo['username']} successfully constructed a temple in province #{provinceid}.")
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
            if p_info['city'] is False:
                await ctx.send("A capital can only be built in a province with an existing city.")
                return
            await conn.execute('''UPDATE cncusers SET capital = $1, resources = resources - $2 WHERE user_id = $3;''',
                               provinceid, 50000, author.id)
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
            elif p_info['city'] is False:
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

    @commands.command(usage="[province id] [structure (fort, port, city,workshop, temple)]",
                      brief="Deconstructs a building in a specified province")
    @commands.guild_only()
    async def cnc_deconstruct(self, ctx, provinceid: int, structure: str):
        # defines the author and connects to the pool
        author = ctx.author
        conn = self.bot.pool
        # fetches province and user information
        p_info = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', provinceid)
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        # if that province does not exist
        if p_info is None:
            await ctx.send("No such province.")
            return
        # if the author does not own and occupy that province
        if p_info['owner_id'] and p_info['occupier_id'] != author.id:
            await ctx.send("You do not own and occupy that province.")
            return
        # if a fort is to be deconstructed
        if structure.lower() == "fort":
            # if no fort exists, return
            if not p_info['fort']:
                await ctx.send("There is no fort in that province.")
                return
            else:
                # set fort to false and update fortlimit
                await conn.execute('''UPDATE provinces SET fort = False WHERE id = $1;''', provinceid)
                await ctx.send(f"The fort in Province #{provinceid} successfully removed.")
                return
        # if a port is to be deconstructed
        elif structure.lower() == "port":
            # if no port exists, return
            if not p_info['port']:
                await ctx.send("There is no port in that province.")
                return
            else:
                # set port to false and update portlimit
                await conn.execute('''UPDATE provinces SET port = False WHERE id = $1;''', provinceid)
                await ctx.send(f"The port in Province #{provinceid} successfully removed.")
                return
        # if a city is to be deconstructed
        elif structure.lower() == "city":
            # if no port exists, return
            if not p_info['city']:
                await ctx.send("There is no city in that province.")
                return
            if userinfo['capital'] == provinceid:
                await ctx.send("You cannot remove your capital city.")
                return
            else:
                # set port to false and update citylimit
                await conn.execute('''UPDATE provinces SET city = False WHERE id = $1;''', provinceid)
                await ctx.send(f"The city in Province #{provinceid} successfully removed.")
                return
            # if a port is to be deconstructed
        elif structure.lower() == "workshop":
            # if no port exists, return
            if not p_info['workshop']:
                await ctx.send("There is no workshop in that province.")
                return
            else:
                # set workshop to false
                await conn.execute('''UPDATE provinces SET workshop = False WHERE id = $1;''', provinceid)
                await ctx.send(f"The workshop in Province #{provinceid} successfully removed.")
                return
        # if a city is to be deconstructed
        elif structure.lower() == "temple":
            # if no port exists, return
            if not p_info['temple']:
                await ctx.send("There is no temple in that province.")
                return
            else:
                # set temple to false
                await conn.execute('''UPDATE provinces SET temple = False WHERE id = $1;''', provinceid)
                await ctx.send(f"The temple in Province #{provinceid} successfully removed.")
                return
        else:
            await ctx.send_help(ctx.invoked_with)
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

    @commands.command(brief="Displays current value of all trade goods.")
    @commands.guild_only()
    async def cnc_market(self, ctx):
        # establish connection
        conn = self.bot.pool
        # fetch trade goods
        goods = await conn.fetch('''SELECT * FROM trade_goods ORDER BY name;''')
        inquiry_emojis = ['\U0001fa99', '\U0001f4e6']
        inquiry = await ctx.send("Select \U0001fa99 for market value. Select \U0001f4e6 for market good count.")
        for e in inquiry_emojis:
            await inquiry.add_reaction(e)

        # the check for the emojis
        def emojicheck(reaction, user):
            return user == ctx.message.author and str(reaction.emoji)

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=180, check=emojicheck)
        except asyncio.TimeoutError:
            await inquiry.delete()
            return
        if str(reaction) == '\U0001fa99':
            await inquiry.delete()
            # define page and list of strings
            page = 1
            goods_list = list()
            # for all goods
            for g in goods:
                # add the good name to the string
                good_string = ""
                good_string += f"`{g['name']} "
                # add 50 spaces, minus the name length
                for space in range(50 - len(g['name'])):
                    good_string += " "
                # add the value
                good_string += f"` | `{g['market_value']}`\n"
                # add dashes for table
                for space in range(70):
                    good_string += "-"
                good_string += "\n"
                goods_list.append(good_string)
            while True:
                # back, stop, and forward buttons
                reactions = ['\U000025c0', '\U0000274c', '\U000025b6']
                # define the upper limit and lower limit
                upper_limit = page * 10
                lower_limit = 0 + ((page - 1) * 10)
                goods_format = ""
                # for the list entries in the range
                for gs in range(lower_limit, upper_limit):
                    goods_format += goods_list[gs]
                # define the embed, add the formatted description, and send the embed
                goods_embed = discord.Embed(title="Trade Goods Market", description=goods_format)
                goods_embed.set_footer(text=f"Page {page} of 3")
                goods_sent = await ctx.send(embed=goods_embed)
                # add reactions
                for r in reactions:
                    await goods_sent.add_reaction(r)

                # the check for the emojis
                def reasoncheck(reaction, user):
                    return user == ctx.message.author and str(reaction.emoji)

                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=180, check=reasoncheck)
                except asyncio.TimeoutError:
                    await goods_sent.clear_reactions()
                    break
                # if the reaction is back
                if str(reaction) == '\U000025c0':
                    # if the reaction is back, and we are at entry 1
                    if page == 0:
                        await goods_sent.clear_reactions()
                        for r in reactions:
                            await goods_sent.add_reaction(r)
                        continue
                    # if the page is not the last, go back a page
                    else:
                        page -= 1
                        await goods_sent.delete()
                        continue
                # if the reaction is close
                if str(reaction) == "\U0000274c":
                    await goods_sent.clear_reactions()
                    break
                # if the reaction is forward
                if str(reaction) == "\U000025b6":
                    # if the current page is the final page
                    if page == 3:
                        await goods_sent.delete()
                    # if it is not the final page, display the next page
                    else:
                        page += 1
                        await goods_sent.delete()
                        continue
        if str(reaction) == '\U0001f4e6':
            await inquiry.delete()
            # define page and list of strings
            page = 1
            goods_list = list()
            # for all goods
            for g in goods:
                good_count = await conn.fetchrow('''SELECT count(*) FROM provinces WHERE value = $1;''', g['name'])
                # add the good name to the string
                good_string = ""
                good_string += f"`{g['name']} "
                # add 50 spaces, minus the name length
                for space in range(50 - len(g['name'])):
                    good_string += " "
                # add the value
                good_string += f"` | `{good_count['count']}`\n"
                # add dashes for table
                for space in range(70):
                    good_string += "-"
                good_string += "\n"
                goods_list.append(good_string)
            while True:
                # back, stop, and forward buttons
                reactions = ['\U000025c0', '\U0000274c', '\U000025b6']
                # define the upper limit and lower limit
                upper_limit = page * 10
                lower_limit = 0 + ((page - 1) * 10)
                goods_format = ""
                # for the list entries in the range
                for gs in range(lower_limit, upper_limit):
                    goods_format += goods_list[gs]
                # define the embed, add the formatted description, and send the embed
                goods_embed = discord.Embed(title="Trade Goods Market Count", description=goods_format)
                goods_embed.set_footer(text=f"Page {page} of 3")
                goods_sent = await ctx.send(embed=goods_embed)
                # add reactions
                for r in reactions:
                    await goods_sent.add_reaction(r)

                # the check for the emojis
                def reasoncheck(reaction, user):
                    return user == ctx.message.author and str(reaction.emoji)

                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=180, check=reasoncheck)
                except asyncio.TimeoutError:
                    await goods_sent.clear_reactions()
                    break
                # if the reaction is back
                if str(reaction) == '\U000025c0':
                    # if the reaction is back, and we are at entry 1
                    if page == 0:
                        await goods_sent.clear_reactions()
                        for r in reactions:
                            await goods_sent.add_reaction(r)
                        continue
                    # if the page is not the last, go back a page
                    else:
                        page -= 1
                        await goods_sent.delete()
                        continue
                # if the reaction is close
                if str(reaction) == "\U0000274c":
                    await goods_sent.clear_reactions()
                    break
                # if the reaction is forward
                if str(reaction) == "\U000025b6":
                    # if the current page is the final page
                    if page == 3:
                        await goods_sent.delete()
                    # if it is not the final page, display the next page
                    else:
                        page += 1
                        await goods_sent.delete()
                        continue

    @commands.command(brief="Displays current production of the nation's trade goods.")
    @commands.guild_only()
    async def cnc_production(self, ctx):
        # establish connection
        conn = self.bot.pool
        # ensure registration
        author = ctx.author
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        if userinfo is None:
            await ctx.send("You are not registered.")
            return
        # fetch trade goods
        goods = await conn.fetch('''SELECT * FROM trade_goods ORDER BY name;''')
        # define page and list of strings
        page = 1
        goods_list = list()
        # for all goods
        for g in goods:
            # count provinces producing the good
            production_count = await conn.fetch('''SELECT * FROM provinces 
            WHERE value = $1 AND owner_id = $2 AND occupier_id = $2;''', g['name'], author.id)
            count = 0
            for p in production_count:
                count += p['production']
            # add the good name to the string
            good_string = ""
            good_string += f"`{g['name']} "
            # add 50 spaces, minus the name length
            for space in range(50 - len(g['name'])):
                good_string += " "
            # add the value
            good_string += f"` | `{count}`\n"
            # add dashes for table
            for space in range(70):
                good_string += "-"
            good_string += "\n"
            goods_list.append(good_string)
        while True:
            # back, stop, and forward buttons
            reactions = ['\U000025c0', '\U0000274c', '\U000025b6']
            # define the upper limit and lower limit
            upper_limit = page * 10
            lower_limit = 0 + ((page - 1) * 10)
            goods_format = ""
            # for the list entries in the range
            for gs in range(lower_limit, upper_limit):
                goods_format += goods_list[gs]
            # define the embed, add the formatted description, and send the embed
            goods_embed = discord.Embed(title="Trade Goods Market", description=goods_format)
            goods_embed.set_footer(text=f"Page {page} of 3")
            goods_sent = await ctx.send(embed=goods_embed)
            # add reactions
            for r in reactions:
                await goods_sent.add_reaction(r)

            # the check for the emojis
            def reasoncheck(reaction, user):
                return user == ctx.message.author and str(reaction.emoji)

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=180, check=reasoncheck)
            except asyncio.TimeoutError:
                await goods_sent.clear_reactions()
                break
            # if the reaction is back
            if str(reaction) == '\U000025c0':
                # if the reaction is back, and we are at entry 1
                if page == 0:
                    await goods_sent.clear_reactions()
                    for r in reactions:
                        await goods_sent.add_reaction(r)
                    continue
                # if the page is not the last, go back a page
                else:
                    page -= 1
                    await goods_sent.delete()
                    continue
            # if the reaction is close
            if str(reaction) == "\U0000274c":
                await goods_sent.clear_reactions()
                break
            # if the reaction is forward
            if str(reaction) == "\U000025b6":
                # if the current page is the final page
                if page == 3:
                    await goods_sent.delete()
                # if it is not the final page, display the next page
                else:
                    page += 1
                    await goods_sent.delete()
                    continue

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
        WHERE occupier_id = $1;''', author.id)
        withdrawn = withdrawn_raw['sum']
        if withdrawn == 0:
            await ctx.send(f"{userinfo['username']} does not have any deployed troops.")
            return
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
        await ctx.send(f"{amount:,} troops deployed to all {len(occupied_provinces)} provinces.")
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

    @commands.command(usage="[stationed province] [target province] <attack force>", aliases=['cnca'],
                      brief="Attacks from one province to another")
    @commands.cooldown(5, 30, commands.BucketType.channel)
    @commands.guild_only()
    async def cnc_attack(self, ctx, stationed: int, target: int, force: int = None, debug: bool = None):
        # initiate
        attack = calculations(force, target, stationed, ctx, debug)
        await attack.combat()

    # ------------------Map Commands----------------------------

    @commands.command(brief="Displays the map")
    @commands.guild_only()
    @commands.max_concurrency(1, commands.BucketType.user)
    async def cnc_map(self, ctx, debug: bool = False):
        loop = asyncio.get_running_loop()
        reactions = ["\U0001f5fa", "\U000026f0", "\U0001f3f3", "\U0001f4cc", "\U0001fa99", "\U0000274c"]
        map = await ctx.send("https://i.ibb.co/6RtH47v/Terrain-with-Numbers-Map.png")
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
                    await map.edit(content="https://i.ibb.co/DwvJ2zc/Terrain-Map.png")
                    for react in reactions:
                        await map.add_reaction(react)
                    continue
                # numbers + terrain
                if str(reaction.emoji) == "\U0001f5fa":
                    await map.clear_reactions()
                    await map.edit(content="https://i.ibb.co/6RtH47v/Terrain-with-Numbers-Map.png")
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
                        with open(fr"{self.map_directory}wargame_nations_map.png", "rb") as preimg:
                            img = b64encode(preimg.read())
                        image = perf_counter()
                        params = {"key": "a64d9505a13854ff660980db67ee3596",
                                  "name": "Nations Map",
                                  "image": img,
                                  "expiration": 86400}
                        sleep(1)
                        upload_initate = perf_counter()
                        upload = await loop.run_in_executor(None, requests.post, "https://api.imgbb.com/1/upload",
                                                            params)
                        upload_complete = perf_counter()
                        response = upload.json()
                        await map.edit(content=response["data"]["url"])
                        if debug is True:
                            await ctx.send(
                                f"Image compiled = {image - initiate}\nStarted upload = {upload_initate - initiate}\n"
                                f"Upload Complete = {upload_complete - initiate}")
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
                # trade goods map
                if str(reaction.emoji) == "\U0001fa99":
                    await map.clear_reactions()
                    await map.edit(content="https://i.ibb.co/Zg6557y/Trade-Goods-Map.png")
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

    @commands.command(usage="[province id]", brief="Highlights a specific province.")
    @commands.guild_only()
    async def cnc_locate(self, ctx, province: int):
        # establish connection and loop
        conn = self.bot.pool
        loop = self.bot.loop
        # gather province info
        p_info = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', province)
        if p_info is None:
            await ctx.send(f"Province ID `{province}` is not a valid ID.")
            return
        else:
            loading = await ctx.send("Loading...")
            async with ctx.typing():
                # obtain the coordinate information
                province_cord = p_info['cord']
                province_cord = ((int(province_cord[0])), (int(province_cord[1])))
                # fetch map and province
                map = Image.open(fr"{self.map_directory}wargame_blank_save.png").convert("RGBA")
                prov = Image.open(fr"{self.province_directory}{province}.png").convert("RGBA")
                # get color
                color = ImageColor.getrgb("#FF00DC")
                # obtain size and coordinate information
                width = prov.size[0]
                height = prov.size[1]
                cord = (province_cord[0], province_cord[1])
                # for every pixel, change the color to the owners
                for x in range(0, width):
                    for y in range(0, height):
                        data = prov.getpixel((x, y))
                        if data != color:
                            if data != (0, 0, 0, 0):
                                if data != (255, 255, 255, 0):
                                    prov.putpixel((x, y), color)
                # convert, paste, and save the image
                prov = prov.convert("RGBA")
                map.paste(prov, box=cord, mask=prov)
                map.save(fr"{self.map_directory}highlight_map.png")
            with open(fr"{self.map_directory}highlight_map.png", "rb") as preimg:
                img = b64encode(preimg.read())
            params = {"key": "a64d9505a13854ff660980db67ee3596",
                      "image": img}
            sleep(1)
            upload = await loop.run_in_executor(None, requests.post, "https://api.imgbb.com/1/upload",
                                                params)
            response = upload.json()
            await loading.edit(content=response["data"]["url"])
            return

    @commands.command()
    @commands.is_owner()
    async def cnc_wipe_all_data_reset(self, ctx):
        # connects to the database
        conn = self.bot.pool
        await conn.execute('''DELETE FROM cncusers;''')
        await conn.execute('''DELETE FROM interactions;''')
        await conn.execute('''DELETE FROM pending_interactions;''')
        await conn.execute('''DELETE FROM cnc_researching;''')
        await conn.execute('''DELETE FROM cnc_modifiers;''')

        await conn.execute('''UPDATE provinces  SET owner = '', owner_id = 0, occupier = '', occupier_id = 0,
        troops = 0, unrest = 0, value = '', name = '', fort = False, city = False, port = False, workshop = False, 
        temple = False, uprising = False;''')
        provinces = await conn.fetch('''SELECT * FROM provinces;''')
        for p in provinces:
            if p['terrain'] == 0:
                if p['river']:
                    goods = ["Wool", "Wool", "Wool", "Wool", "Wool", "Wool", "Wool", "Wool", "Wool", "Wool",
                             "Fur", "Fur", "Fur", "Grain", "Grain", "Grain", "Grain", "Grain", "Grain", "Grain",
                             "Livestock", "Livestock", "Livestock", "Livestock", "Livestock", "Livestock", "Livestock",
                             "Precious Goods", "Spices", "Spices", "Tea and Coffee", "Tea and Coffee", "Tea and Coffee",
                             "Cotton", "Cotton", "Cotton", "Cotton", "Cotton", "Cotton",
                             "Sugar", "Sugar", "Sugar", "Tobacco", "Tobacco", "Tobacco", "Tobacco", "Rare Wood",
                             "Rare Wood", "Glass", "Glass", "Glass", "Glass", "Paper", "Paper", "Paper", "Paper",
                             "Paper", "Fruits", "Fruits", "Fruits", "Fruits", "Wood", "Wood", "Wood", "Wood", "Wood",
                             "Wood",
                             "Wood", "Ivory", "Ivory"]
                    if p['coast']:
                        goods.extend(["Fish", "Fish", "Fish"])
                    good = random.choice(goods)
                    await conn.execute('''UPDATE provinces SET value = $1 WHERE id = $2;''', good, p['id'])
                else:
                    goods = ["Wool", "Wool", "Wool", "Wool", "Wool", "Fur", "Fur", "Fur",
                             "Grain", "Grain", "Grain", "Grain", "Grain",
                             "Livestock", "Livestock", "Livestock", "Livestock", "Livestock", "Precious Goods",
                             "Spices", "Spices", "Tea and Coffee", "Tea and Coffee", "Cotton", "Cotton", "Cotton",
                             "Sugar", "Sugar", "Tobacco", "Tobacco", "Tobacco", "Rare Wood", "Rare Wood",
                             "Glass", "Glass", "Glass", "Glass", "Paper", "Paper", "Paper", "Paper", "Fruits", "Fruits",
                             "Fruits", "Wood", "Wood", "Wood", "Wood", "Wood", "Ivory", "Ivory"]
                    if p['coast']:
                        goods.extend(["Fish", "Fish", "Fish"])
                    good = random.choice(goods)
                    await conn.execute('''UPDATE provinces SET value = $1 WHERE id = $2;''', good, p['id'])
                await conn.execute(
                    '''UPDATE provinces SET troops = $1, manpower = $2 WHERE id = $3;''',
                    randrange(250, 400), randrange(3000, 5000), p['id'])
            if p['terrain'] == 1:
                goods = ['Dyes', 'Precious Stones', 'Spices', 'Spices', 'Glass', 'Glass', 'Glass', 'Glass',
                         'Paper', 'Paper', 'Paper', 'Paper', 'Precious Goods', 'Ivory', 'Ivory']
                if p['coast']:
                    goods.extend(["Fish", "Fish", "Fish"])
                good = random.choice(goods)
                await conn.execute('''UPDATE provinces SET value = $1 WHERE id = $2;''', good, p['id'])
                await conn.execute(
                    '''UPDATE provinces SET troops = $1, manpower = $2 WHERE id = $3;''',
                    randrange(100, 180), randrange(500, 800), p['id'])
            if p['terrain'] == 2:
                if p['river']:
                    goods = ['Fur', 'Fur', 'Fur', 'Grain', 'Grain', 'Grain', 'Grain', 'Grain', 'Grain', 'Grain',
                             'Livestock', 'Livestock', 'Livestock', 'Livestock', 'Livestock', 'Livestock', 'Livestock',
                             'Salt', 'Salt', 'Salt', 'Salt', 'Salt', 'Wine', 'Wine', 'Wine', 'Wine', 'Wine',
                             'Copper', 'Copper', 'Copper', 'Iron', 'Iron', 'Iron', 'Precious Goods', 'Spices', 'Spices',
                             'Tea and Coffee', 'Tea and Coffee', 'Tea and Coffee',
                             'Chocolate', 'Chocolate', 'Chocolate', 'Sugar', 'Sugar', 'Sugar',
                             'Tobacco', 'Tobacco', 'Tobacco', 'Tobacco', 'Rare Wood', 'Rare Wood',
                             'Glass', 'Glass', 'Glass', 'Glass', 'Paper', 'Paper', 'Paper', 'Paper', 'Paper', 'Paper',
                             'Fruits', 'Fruits', 'Fruits', 'Fruits',
                             'Wood', 'Wood', 'Wood', 'Wood', 'Wood', 'Wood', 'Wood',
                             'Tin', 'Tin', 'Tin', 'Ivory', 'Ivory']
                    if p['coast']:
                        goods.extend(["Fish", "Fish", "Fish"])
                    good = random.choice(goods)
                    await conn.execute('''UPDATE provinces SET value = $1 WHERE id = $2;''', good, p['id'])
                else:
                    goods = ['Fur', 'Fur', 'Fur', 'Grain', 'Grain', 'Grain', 'Grain', 'Grain',
                             'Livestock', 'Livestock', 'Livestock', 'Livestock', 'Livestock',
                             'Salt', 'Salt', 'Salt', 'Salt', 'Salt', 'Wine', 'Wine', 'Wine', 'Wine',
                             'Copper', 'Copper', 'Copper', 'Iron', 'Iron', 'Iron', 'Precious Goods', 'Spices', 'Spices',
                             'Tea and Coffee', 'Tea and Coffee',
                             'Chocolate', 'Chocolate', 'Sugar', 'Sugar',
                             'Tobacco', 'Tobacco', 'Tobacco', 'Rare Wood', 'Rare Wood',
                             'Glass', 'Glass', 'Glass', 'Glass', 'Paper', 'Paper', 'Paper', 'Paper',
                             'Fruits', 'Fruits', 'Fruits', 'Wood', 'Wood', 'Wood', 'Wood', 'Wood',
                             'Tin', 'Tin', 'Tin', 'Ivory', 'Ivory']
                    if p['coast']:
                        goods.extend(["Fish", "Fish", "Fish"])
                    good = random.choice(goods)
                    await conn.execute('''UPDATE provinces SET value = $1 WHERE id = $2;''', good, p['id'])
                await conn.execute(
                    '''UPDATE provinces SET troops = $1, manpower = $2 WHERE id = $3;''',
                    randrange(300, 400), randrange(2500, 4500), p['id'])
            if p['terrain'] == 5:
                goods = ['Salt', 'Salt', 'Salt', 'Salt', 'Salt', 'Copper', 'Copper', 'Copper', 'Iron', 'Iron', 'Iron',
                         'Precious Goods', 'Spices', 'Spices', 'Precious Stones', 'Precious Stones',
                         'Coal', 'Coal', 'Coal', 'Coal', 'Gold', 'Gold',
                         'Raw Stone', 'Raw Stone', 'Raw Stone', 'Raw Stone', 'Raw Stone',
                         'Silver', 'Silver', 'Silver', 'Tin', 'Tin', 'Tin']
                if p['coast']:
                    goods.extend(["Fish", "Fish", "Fish"])
                good = random.choice(goods)
                await conn.execute('''UPDATE provinces SET value = $1 WHERE id = $2;''', good, p['id'])
                await conn.execute(
                    '''UPDATE provinces SET troops = $1, manpower = $2 WHERE id = $3;''',
                    randrange(1000, 1300), randrange(600, 900), p['id'])
            if p['terrain'] == 7:
                goods = ['Precious Goods', 'Spices', 'Spices', 'Silk', 'Silk', 'Silk', 'Silk',
                         'Rare Wood', 'Rare Wood', 'Rare Wood', 'Glass', 'Glass', 'Glass', 'Glass',
                         'Paper', 'Paper', 'Paper', 'Paper', 'Coal', 'Coal', 'Coal', 'Coal', 'Ivory', 'Ivory']
                if p['coast']:
                    goods.extend(["Fish", "Fish", "Fish"])
                good = random.choice(goods)
                await conn.execute('''UPDATE provinces SET value = $1 WHERE id = $2;''', good, p['id'])
                await conn.execute(
                    '''UPDATE provinces SET troops = $1, manpower = $2 WHERE id = $3;''',
                    randrange(100, 180), randrange(150, 300), p['id'])
            if p['terrain'] == 9:
                goods = ['Fur', 'Fur', 'Fur', 'Precious Goods', 'Spices', 'Glass', 'Glass', 'Glass', 'Glass',
                         'Ivory']
                if p['coast']:
                    goods.extend(["Fish", "Fish", "Fish"])
                good = random.choice(goods)
                await conn.execute('''UPDATE provinces SET value = $1 WHERE id = $2;''', good, p['id'])
                await conn.execute(
                    '''UPDATE provinces SET troops = $1, manpower = $2, port = FALSE, city = FALSE, fort = FALSE 
                    WHERE id = $3;''',
                    randrange(100, 200), randrange(150, 300), p['id'])
        names = ["Athyastoroklis", "Seva", "Kezubenu", "Napby", "Djacahdet", "Sepsai", "Kisrimeru", "Sapoyut",
                 "Tarnouru",
                 "Sasotaten", "Bema", "Gesso", "Shari", "Acne", "Menrusiris", "Shapo", "Senebenu", "Tabe", "Behbu",
                 "Dessasiris", "Sepdjesut", "Tarre", "Khepeset", "Nemtadjed", "Behzum", "Tjendepet", "Cupo",
                 "Wasbumunein", "Kerdjerma", "Khemabesheh", "Kenupis", "Boroupoli", "Epione", "Pelyma", "Golgona",
                 "Thebekion", "Juktorus", "Phanipolis", "Tyraphos", "Pavlosse", "Eubacus", "Rhodyrgos", "Myrolgi",
                 "Setrias", "Massipolis", "Corcyreum", "Megarina", "Laodigona", "Posane", "Panteselis", "Arsaistos",
                 "Rhegenes", "Abymna", "Lampsens", "Benion", "Golgarae", "Aytippia", "Thespeucia", "Mallaza",
                 "Cythene", "Agrinaclea", "Zuivild", "Thisruil", "Ilvynyln", "Teapost", "Starmore", "Strawshire",
                 "Hollowgarde", "Mossmore", "Tabanteki", "Wolrion", "Kimnia", "Arakuru", "Gobafidi", "Narakare",
                 "Qamatlong", "Mesane", "Mandujang", "Mankalane", "Mobane", "Seria", "Wolmadanha", "Omanie",
                 "Genthanie", "Babong", "Quseng", "Meweng", "Lethagonami", "Danzibanyatsi", "Kulembu", "Salkal",
                 "Saldakuwa", "Kawa", "Lahandja", "Namaferu", "Moine", "Hukuhaba", "Malume", "Vulembu", "Allanrys",
                 "Kilanga", "Okashapi", "Oshirara", "Lofale", "Pokojea", "Selerobe", "Tlothe", "Iwagata",
                 "Mutsutsukawa", "Changchong", "Meishui", "Khairmani", "Nogoonkh", "Kangwon", "Hamsu", "Taewang",
                 "Hamchaek", "Sinuihung", "Sinuicheon", "Taigaa", "Sogusi", "Nurhakisla", "Jirozmian", "Yasousar",
                 "As", "Sasiyyah", "Etadfa", "Mirut", "Wadifer", "Sakarout", "Mneesayr", "Masyamas", "Rafhamloj",
                 "Wadireg", "Choinuur", "Pingrao", "Panchun", "Yatori", "Kumaraha", "Yahakonai", "Qahanieh",
                 "Arisyoun", "Tel", "Khanayah", "As", "Saysan", "Khorranab", "Alaroft", "Iliborlu", "Adankum",
                 "Seafurah", "Kivuadi", "Rausoka", "Barekawa", "Tanimotu", "Rakawald", "Okairuru", "Niupia",
                 "Utusi", "Fetofesia", "Fohi", "Geelide", "Seafave", "Vumbavua", "Sobalevu", "Tekatiratai",
                 "Nuotebiki", "Hokitakere", "Mapuapara", "Faleamalo", "A'ufaga", "Telefuiva", "Lofakulei",
                 "Ivorgarde", "Glockrath", "Charward", "Ivoryham", "Dawnglen", "Dreadwall", "Aerahaben", "Legstead",
                 "Tattingstein", "Flammore", "Sleetdrift", "Ycemire", "Fljot", "Meoalfell", "Hraunaheior",
                 "Hagbarosholmr", "Kollsvik", "Hafsloekr", "Hrafnstoptir", "Eskiholt", "Jokulsarhlio",
                 "Hafgrimsfjoror", "Riocarí", "Jagar", "Architanas", "Nulriel", "Tonnéte", "Sinra", "Immia",
                 "Makourama", "Pago", "Abenastina", "Tápiz", "Ejimare", "Limonum", "Caudium", "Armorica",
                 "Dianinum", "Emporiae", "Bilbilis", "Ostium", "Sinope", "Atrans", "Concangis", "Tuder",
                 "Selymbria", "Cannabiaca", "Vinovium", "Catania", "Portus", "Odessus", "Tenedo", "Mursa", "Velipa",
                 "Seveyungri", "Yelalabuga", "Anarechny", "Calacadis", "Abylune", "Liquasa", "Puritin", "Posegia",
                 "Belipis", "Thelor", "Tsunareth", "Tynea", "Geythis", "Tempemon", "Thalareth", "Liqucadis",
                 "Tethton", "Paciris", "Nepturia", "Levialean", "Boyrem", "Aciolis", "Hydgia", "Sireria", "Liquiri",
                 "Navathis", "Liquasa", "Salania", "Aciopis", "Berylora", "Riverem", "Merlean", "Amphireth",
                 "Nereicada", "Abyrey", "Scylor", "Belilean", "Donoch", "Levialore", "Aquasa", "Ashamon", "Salaren",
                 "Tsuloch", "Hytin", "Chaszuth", "Microd", "Kaliz", "Taltahrar", "Vazulzak", "Tunkhudduk",
                 "Miggiddoz", "Kaakrahnath", "Joggrox", "Nakkuss", "Zukkross", "Rutago", "Gato", "Yirbark",
                 "Ellaba", "Maganango", "Ruhenhengeri", "Buye", "Ufecad", "Mamo", "Mlankindu", "Biharari", "Jira",
                 "Kampagazi", "Apayo", "Kamudo", "Atrophy", "Scythe", "Carthage", "Dawnbury", "Quellton", "Isolone",
                 "Termina", "Krslav", "Vsekolov", "Democaea", "Myrini", "Tylamnus", "Lamesus", "Alyros", "Demike",
                 "Thyrespiae", "Eretrissos", "Heraclymna", "Thuriliki", "Kyratrea", "Lampsomenus", "Mareos",
                 "Phliesos", "Oncheron", "Cumespiae", "Myndasae", "Acomenion", "Psychrinitida", "Cumakros",
                 "Aigous", "Gelaclea", "Gythagoria", "Elaticus", "Morgocaea", "Leontinitida", "Orastro", "Himos",
                 "Losse", "Gorgox", "Paphateia", "Lefkanthus", "Hierinope", "Onchapetra", "Olamum", "Rhypada",
                 "Himarnacia", "Katyros", "Thasseron", "Thassofa", "Metens", "Moleporobe", "Nokapi", "Qetika",
                 "Qetithing", "Omudu", "Otjimna", "Ekanbron", "Mitief", "Kwano", "Movone", "Lobashe", "Lotrowe",
                 "Noma", "Thayatseng", "Ongwema", "Okahadive", "Kruba", "Allankal", "Nsabasena", "Dulevise",
                 "Kubuye", "Saldanus", "Soha", "Rehovi", "Oshidja", "Meyokabei", "Pihane", "Molepodibe",
                 "Thamalala", "Westwall", "Freyview", "Bayhollow", "Frostvalley", "Smallstrand", "Grimbay",
                 "Limestar", "Southborough", "Wintermoor", "Arrowstrand", "Borville", "Marilet", "Borgueu",
                 "Ironfield", "Ruststar", "Silenttown", "Silvershore", "Avinia", "Cálma", "Virtos", "Orodorm",
                 "Tomadura", "Bulle", "Andanea", "Grallón", "Gipuscay", "Cagona", "Zamostile", "Alzilavega",
                 "Outiva", "Zaravila", "Sagoza", "Rouyonne", "Bacourt", "Cololimar", "Grelly", "Sarsart", "Vinmont",
                 "Beaufort", "Puroux", "Marlimar", "Orsier", "Whisperpeak", "Lowbellow", "Thingorge", "Quickpeak",
                 "Talonhallow", "Copperstead", "Bonetrail", "Barebank", "Onyxpeak", "Wrycanyon", "Starkpeaks",
                 "Buelita", "Nueco", "Pola", "Quecos", "Recalco", "Rejanes", "Yusquile", "Carcos", "Jinoral",
                 "Guacan", "Ditos", "Wiwiya", "Talaba", "Cuyatal", "Rerio", "Aposonate", "Atijutla", "Mipiles",
                 "Sarillos", "Jalacho", "Volnola", "Quilica", "Priguaque", "Trujirito", "Salamento", "Aguanahu",
                 "Cojulupe", "Atinal", "Jara", "Trinilores", "Ponlants", "Hepmagne", "Clerbiens", "Sarfannfik",
                 "Oqaattaq", "Napaluitsup", "Cajemoros", "Penjachuca", "Chitecas", "Chesmore", "Scarmouth",
                 "Canterster", "Autumncester", "Greenwall", "Brighstone", "Ocosingo", "Xalacoco", "Jiutelende",
                 "Sirapaluk", "Nutaarhivik", "Kuumtu", "Burdiac", "Garmis", "Lebridge", "Flushgard", "Thistlehelm",
                 "Mekkadale", "Sparkwall", "Plumewatch", "Freelmorg", "Mummadogh", "Finkipplurg", "Fili", "Keenfa",
                 "Dintindeck", "Glostos", "Imblin", "Fonnipporp", "Wigglegate", "Landbrunn", "Gerasweg", "Antberge",
                 "Knokberge", "Périssons", "Caluçon", "Gailkirchen", "Ansholz", "Macvan", "Mullindoran", "Dikkerk",
                 "Asdaal", "Spreitenbach", "Appenlach", "Poyslach", "Oudenhout", "Valès", "Brugleeuw", "Cassons",
                 "Tangerschau", 'Spalion', 'Rethyndra', 'Kaisasina', 'Grervara', 'Miadananitra', 'Tsarasirabe',
                 'Soavinatanana', 'Antsinimena', 'Fandrabava', 'Arikaraka', 'Fandravola', 'Wokagee', 'Lesliaj',
                 'Kryeliku', 'Llalot', 'Xhataj', 'Xhycyrë', 'Budakovec', 'Bullajt', 'Neuschlag', 'Ebreichdeck',
                 'Amdenz', 'Vöcklabühel', 'Hollaweil', 'Lustenstein', 'Dornnau', 'Ermoulonghi', 'Prevedri', 'Heravala',
                 'Polipoi', 'Vavamanitra', 'Antsolaona', 'Amparatsetra', 'Betatra', 'Berovombe', 'Antafolotra',
                 'Vohimavony', 'Booriwa', 'Ceras', 'Mamumarë', 'Rrogolenë', 'Vërkopi', 'Livasekë', 'Kugjun', 'Pasekë',
                 'Ansten', 'Wolfstadt', 'Götkreis', 'Altental', 'Kirchdenz', 'Terben', 'Gänsernkirchen', 'Floliada',
                 'Metarni', 'Vounina', 'Edestiada', 'Tsalangwe', 'Mitunte', 'Domamasi', 'Blalaomo', 'Mponera',
                 'Limlanje', 'Ngache', 'Poonbilli', 'Toko', 'Šipojaš', 'Stijki', 'Bijeldor', 'Kalengrad', 'Trehać',
                 'Caska', 'Sherpenwerpen', 'Dillaas', 'Nieuwport', 'Halstraten', 'Torstraten', 'Westden',
                 'Landtals', 'Messimezia', 'Sassarence', 'Bitoraele', 'Scabria', 'Thyochenza', 'Maloji', 'Chitiza',
                 'Chikutete', 'Phade', 'Nathenkota', 'Malaotheche', 'Myamine', 'Neslavgrad', 'Jazin', 'Viška',
                 'Traboj', 'Čapčac', 'Čedanj', 'Milišća', 'Zothout', 'Dikzen', 'Korteind', 'Oudenhal', 'Dammuide',
                 'Weststraten', 'Nieuwschot', 'Lamellino', 'Cagliana', 'Collesaro', 'Baghetonto', 'Xabuto',
                 'Naputo', 'Moatida', 'Chikulo', 'Macilacuala', 'Mutuabo', 'Lilo', 'Balloundra', 'Rakopan',
                 'Blagoevski', 'Svobol', 'Provarna', 'Stamvishte', 'Kubvo', 'Gabrobrod', 'Alenlet', 'Besanluire',
                 'Martoise', 'Aviçon', 'Bergessonne', 'Vierbonne', 'Aurigneux', 'Civilerno', 'Cinisto', 'Faersala',
                 'Modivia', 'Marralacuala', 'Xane', 'Mansano', 'Mansano', 'Resdica', 'Monba', 'Nampulimane',
                 'Cooldong', 'Samovin', 'Pavlikovski', 'Petshte', 'Ikhlene', 'Tutravo', 'Pomolikeni', 'Petva',
                 'Chaveil', 'Avignan', 'Angousart', 'Narzon', 'Sarsier', 'Bournoît', 'Boursier', 'Almacos',
                 'Reniche', 'Guavoa', 'Guija', 'Chabezi', 'Solengwa', 'Lundashi', 'Kabogwe', 'Kawamzongwe',
                 'Mponlunga', 'Zambewezi', 'Caideena', 'Bremobor', 'Krikovar', 'Samorinja', 'Stovar', 'Vula',
                 'Kutivača', 'Orarica', 'Großbruck', 'Lüdinghöring', 'Elsterbog', 'Elmroda', 'Gailhude',
                 'Dillenwig', 'Eltershafen', 'Manguache', 'Esmoxa', 'Batejo', 'Meamoz', 'Maabwe', 'Luwinwezi',
                 'Sibombwe', 'Mpila', 'Lugwi', 'Lukusama', 'Kapupo', 'Manlang', 'Jezejevec', 'Opatilok',
                 'Križepina', 'Dubropin', 'Slatizerce', 'Bjegrad', 'Ilorovo', 'Adebog', 'Osterlein', 'Cuxkamp',
                 'Romroda', 'Gladenhude', 'Ersten', 'Alsschau', 'Trasmo', 'Vibos', 'Camagal', 'Gafarosa',
                 'Lupagani', 'Mazoru', 'Buton', 'Gwani', 'Raffirowa', 'Chimanira', 'Chakage', 'Turbawa', 'Sušiles',
                 'Iličani', 'Vevto', 'Skoplesta', 'Belmica', 'Bikov', 'Lojašeišta', 'Dublee', 'Clonkilty',
                 'Granderry', 'Tullanard', 'Tullahal', 'Newney', 'Dunford', 'Cavila', 'Guarcia', 'Galirez',
                 'Ávirón', 'Penhati', 'Bindugora', 'Chitunwayo', 'Gopanzi', 'Goni', 'Shamdu', 'Marondera',
                 'Gooneragan', 'Dojrovo', 'Poja', 'Zabar', 'Velša', 'Krivotovo', 'Brvenijusa', 'Mirabruševo',
                 'Macgar', 'Clonakee', 'Maccommon', 'Shanway', 'Castlegheda', 'Naran', 'Dubtowel', 'Raelellón',
                 'Márrol', 'Seria', 'Orova', 'Vaceni', 'Doroteşti', 'Gioba', 'Târrest', 'Cernarşa', 'Piterşa',
                 'Conmon', 'Amersdaal', 'Zoetermegen', 'Staventer', 'Devenberg', 'Dierburg', 'Blokstadt', 'Asren',
                 'Zamovia', 'Valejón', 'Zastela', 'Riorez', 'Balgăşani', 'Panteghetu', 'Bârftea', 'Timirad',
                 'Buhuşiţa', 'Fetegalia', 'Slojud', 'Waaloord', 'Amerskerk', 'Ashuizen', 'Slolo', 'Amstelstadt',
                 'Emmelzaal', 'Ashof', 'Knjazamane', 'Stanirig', 'Konica', 'Arankinda', 'Panzar', 'Šavor',
                 'Granovci', 'Laustätten', 'Wädensberg', 'Kreuzstein', 'Opthal', 'Opnacht', 'Friseen', 'Freienbach',
                 'Kragudište', 'Belvor', 'Novac', 'Arirug', 'Aramane', 'Kraguvac', 'Panrig', 'Reilach', 'Laufenkon',
                 'Herneuve', 'Menbon', 'Steffisborn', 'Ostermance', 'Ergen', 'Konice', 'Dravovica', 'Črnolavž',
                 'Trbojice', 'Murskem', 'Rogaje', 'Beltinci', 'Spojba', 'Jerice', 'Škofkem', 'Noše', 'Mujana',
                 'Ratina', 'Jagogaška', 'Kongehus', 'Skjoldbæk', 'Vejlev', 'Guldhus', 'Dybborg', 'Smedestrup',
                 'Karlsborg', 'Fladbæk', 'Vestergård', 'Vindholt', 'Halrup', 'Kirkehus', 'Tubbokaye', 'Kalintsa',
                 'Pizhany', 'Zhytkakaw', 'Dudok', 'Vesterkilde', 'Birkestrup', 'Enshus', 'Lillerup', 'Møllerup',
                 'Strandstrup', 'Guldskov', 'Silkeholt', 'Rødhavn', 'Karlsbæk', 'Bjørnbæk', 'Rødkilde', 'Vitsyezyr',
                 'Skitrykaw', 'Shchusna', 'Navapotsavichy', 'Narostavy', 'Tammme', 'Tamvi', 'Vilsi', 'Pärpina',
                 'Kärva', 'Kiviõtu', 'Räru', 'Kärpina', 'Otesuu', 'Kaldi', 'Kiviõna', 'Kargeva', 'Litště',
                 'Vsebram', 'Kobíč', 'Těkolov', 'Valapa', 'Palde', 'Sinsa', 'Räpila', 'Karski', 'Karngi', 'Põllin',
                 'Kurepää', 'Kiviõsalu', 'Abgeva', 'Narme', 'Tajandi', 'Rapli', 'Uhernec', 'Valabem', 'Hrakov',
                 'Kroměkolov', 'Chomusou', 'Heisaari', 'Mänranta', 'Ähtäkumpu', 'Juanni', 'Kuripunki', 'Juanttinen',
                 'Kokekola', 'Keusämäki', 'Kitali', 'Ylöpula', 'Heissa', 'Pietarni', 'Balota', 'Töson', 'Szartak',
                 'Lajojosmizse', 'Oroszna', 'Riihivalta', 'Orimamäki', 'Valkeani', 'Huisuu', 'Nosiä', 'Ylövala',
                 'Niniemi', 'Haniemi', 'Raaseko', 'Raittinen', 'Kanttila', 'Ulranta', 'Kiskunta', 'Keszna', 'Tatak',
                 'Karnor', 'Szenbóvár', 'Hólhólmur', 'Mosfellssós', 'Reykvöllur', 'Hvolsfjörður', 'Keflajahlíð',
                 'Grundarsker', 'Blönnarnes', 'Eyrarjarhverfi', 'Þórsnesi', 'Dalnes', 'Garðaseyri', 'Dalkrókur',
                 'Comspol', 'Strănești', 'Rîșcamenca', 'Străză', 'Cupdul', 'Vopnaholt', 'Hvanseyri', 'Hnífshólar',
                 'Seyðissey', 'Þórsnes', 'Vestvöllur', 'Stukhólar', 'Garðaganes', 'Þorlákshólmur', 'Keflasós',
                 'Kópafjörður', 'Seltjarhöfn', 'Vatroca', 'Hînceriopol', 'Tereni', 'Iana', 'Rîșcați', 'Grolupe',
                 'Lienci', 'Vipils', 'Aluklosta', 'Salactene', 'Ziceni', 'Prielsi', 'Sigulda', 'Salacele',
                 'Jauncut', 'Vigazilani', 'Salaclozi', 'Piwice', 'Świmyśl', 'Łomkary', 'Kory', 'Śląnin', 'Jurlava',
                 'Bauslava', 'Sabidava', 'Strenza', 'Ligatnas', 'Aknibe', 'Alodava', 'Kargava', 'Valdone', 'Limnda',
                 'Varakgriva', 'Sabigums', 'Chezno', 'Chenowo', 'Piebunalski', 'Płowiec', 'Soworzno', 'Mažeikda',
                 'Priegara', 'Daugbrade', 'Druskiai', 'Marijventis', 'Grigtos', 'Dusetme', 'Drusštas', 'Rudišninka',
                 'Priecininkai', 'Utnai', 'Mažeiklute', 'Căliraolt', 'Galanaia', 'Dolhadiru', 'Ciatina', 'Ovilonta',
                 'Ramysiejai', 'Ignalbarkas', 'Gargbalis', 'Dusetkiai', 'Jieztavas', 'Kaiškuva', 'Plunjoji',
                 'Radkruojis', 'Jurkule', 'Šventai', 'Vergiai', 'Dukvas', 'Orășa', 'Însudud', 'Bohoi', 'Bebiu',
                 'Armănești', 'Grimhelle', 'Oshammer', 'Hokkbu', 'Molbak', 'Osstrøm', 'Varros', 'Verdalhelle',
                 'Ulsteinfjord', 'Arenstad', 'Elvik', 'Grimhalsen', 'Hønekim', 'Snivo', 'Zlačín', 'Dunajňava',
                 'Svärica', 'Stropky', 'Asrum', 'Søgjøen', 'Finnros', 'Tromvåg', 'Ålerum', 'Farsøor', 'Statjøen',
                 'Breksøra', 'Harvern', 'Brønnøystrøm', 'Kongsden', 'Verdaljøen', 'Dudintár', 'Ilajov', 'Návičovo',
                 'Baršiná', 'Marhovec', 'Torsholm', 'Oxelöhall', 'Landskil', 'Ulricellefteå', 'Bollbro',
                 'Gammaltorp', 'Bollbro', 'Österstad', 'Oxelötorp', 'Finburg', 'Uppbo', 'Borgsås', 'Uzhhove',
                 'Ochadilsk', 'Berchyn', 'Uzhkivka', 'Ananruch', 'Mjölsås', 'Östlänge', 'Huskhamn', 'Gamlesele',
                 'Djurskil', 'Fagerbacka', 'Sundbyvalla', 'Skogby', 'Oxelögrund', 'Bollhärad', 'Uddekoga',
                 'Eskilfors', 'Zbodiach', 'Polonihiv', 'Henirad', 'Chervonivka', 'Illinyk', 'Dalabey', 'Begegaç',
                 'Sivriyayla', 'Badekoyunlu', 'Pirakapi', 'Kocame', 'Kemeca', 'Sivrikisla', 'Khorashtar',
                 'Kashavar', 'Herist', 'Ahvaft', 'Ahvalard', 'Behbast', 'Abayaan', 'Kilaqqez', 'Nibjah', 'Quditha',
                 'Ctesirah', 'Balasit', 'Tall-Qubayr', 'Momadi', 'Zakhobil', 'Al-Hasyoun', 'Khushawai', 'Al-Kareya',
                 'Sammar', 'Purbel', 'Mongrieng', 'Dammum', 'Nearey', 'Moluos', 'Mongrom', 'Rômbel', 'Probokal',
                 'Pekandung', 'Palangjung', 'Pekawang', 'Cirebau', 'Lhoklaya', 'Paloda', 'Pemadiun', 'Lukah', 'Samagat',
                 'Bhatok', 'Manratok', 'Banmat', 'Kanochang', 'Patangor', 'Belabatangan', 'Maigapu', 'Aungbwe',
                 'Aungde', 'Senneko', 'Kakant', 'Cidan', 'Namhpadan', 'Nyaungshi', 'Dumadal', 'Samamoc', 'Mabalacurong',
                 'Taguvotas', 'Galisay', 'Escapalay', 'Antipi', 'Baido', 'Hobulla', 'Cragool', 'Goulbick', 'Rowvegie',
                 'Situmri', 'Lekamawai', 'Lumika', 'Sisowai', 'Benuamaiku', 'Tabuiki', 'Tebwatao',
                 'Aeneamaiaki', 'Faiwald', 'Pararaumu', 'Makelaga', 'Manatangata', 'Savaleolo', 'Famalava',
                 'Guatasaga', 'Ninipunga', 'Katua', 'Elsons Abyss', 'Eastrock Cliffs']
        conn = self.bot.pool
        provs = await conn.fetch('''SELECT * FROM provinces WHERE name = '';''')
        iterations = 0
        production = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        for p in provs:
            await conn.execute('''UPDATE provinces SET name = $1, production = $2 WHERE id = $3;''',
                               names[iterations], choice(production), p['id'])
            iterations += 1
        await conn.execute('''UPDATE cnc_data SET data_value = $1 WHERE data_name = $2;''', 0, "turn")
        await conn.execute('''UPDATE cnc_data SET data_value = $1 WHERE data_name = $2;''', 0, "resources")
        await conn.execute('''UPDATE cnc_data SET data_value = $1 WHERE data_name = $2;''', 0, "deaths")
        await ctx.send("https://tenor.com/view/finished-elijah-wood-lord-of-the-rings-lava-fire-gif-5894611")
        return

    @commands.command()
    @commands.is_owner()
    async def cnc_reset_map(self, ctx):
        map = Image.open(fr"{self.map_directory}wargame_blank_save.png").convert("RGBA")
        map.save(fr"{self.map_directory}wargame_provinces.png")
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

    # @commands.command(usage="[nation name] [province] [reason]", brief="Gives a specified nation a specified province")
    # @modcheck()
    # async def cnc_cede(self, ctx, username: str, province: int, *args):
    #     # connects to the database
    #     conn = self.bot.pool
    #     author = ctx.author
    #     reason = ' '.join(args[:])
    #     # if it is not a release
    #     if username != "0":
    #         # checks user existence
    #         allusers = await conn.fetch('''SELECT username FROM cncusers;''')
    #         allusers = [u['username'].lower() for u in allusers]
    #         if username.lower() not in allusers:
    #             await ctx.send(f"{username} does not appear to be registered")
    #
    #             return
    #         # fetches user info
    #         user = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1;''', username)
    #         provinceinfo = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', province)
    #         if provinceinfo is None:
    #             await ctx.send("That province does not seem to exist.")
    #
    #             return
    #         # if the province is owned by the natives
    #         if provinceinfo['owner_id'] == 0:
    #             # updateds all relevant information
    #             await conn.execute('''UPDATE provinces SET owner = $1, owner_id = $2, troops = 0 WHERE id = $3;''',
    #                                user['username'], user['user_id'], province)
    #             owned_list = user['provinces_owned'].append(province)
    #             await conn.execute('''UPDATE cncusers SET provinces_owned = $1 WHERE user_id = $2;''',
    #                                owned_list, user['user_id'])
    #             self.map_color(province, provinceinfo['cord'], user['usercolor'])
    #             await conn.execute('''INSERT INTO mod_logs(id, mod_id, action, reason) VALUES($1,$2,$3,$4);''',
    #                                ctx.message.id, author.id, f"ceded province {province} to {user['username']}",
    #                                reason)
    #             await ctx.send(f"Province #{province} awarded to {user['username']}.")
    #             return
    #         # if the province is owned
    #         elif provinceinfo['owner_id'] != 0:
    #             # fetches province owner information and removes province id
    #             owner = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', provinceinfo['owner_id'])
    #             stationedtroops = provinceinfo['troops']
    #             owner_ownedlist = owner['provinces_owned']
    #             owner_ownedlist.remove(province)
    #             # updates relevant information
    #             await conn.execute('''UPDATE provinces SET owner = $1, owner_id = $2, troops = 0 WHERE id = $3;''',
    #                                user['username'], user['user_id'], province)
    #             owned_list = user['provinces_owned'].append(province)
    #             await conn.execute('''UPDATE cncusers SET provinces_owned = $1 WHERE user_id = $2;''',
    #                                owned_list, user['user_id'])
    #             await conn.execute(
    #                 '''UPDATE cncusers SET undeployed = undeployed + $1 WHERE user_id = $3;''',
    #                 stationedtroops, owner['user_id'])
    #             self.map_color(province, provinceinfo['cord'], user['usercolor'])
    #             await conn.execute('''INSERT INTO mod_logs(id, mod_id, action, reason) VALUES($1,$2,$3,$4);''',
    #                                ctx.message.id, author.id,
    #                                f"ceded province #{province} from {owner['username']} to {user['username']}",
    #                                reason)
    #             await ctx.send(
    #                 f"Province #{province} has been ceded from {owner['username']} to {user['username']}."
    #                 f"All {stationedtroops} in the province have been returned to the undeployed stockpile.")
    #             await owner['user_id'].send(f"Province #{province} has been removed from your control for the "
    #                                         f"following reason: ```{reason}```")
    #             return
    #     # if the province needs to be released
    #     elif username == "0":
    #         # fetch province and owner info
    #         provinceinfo = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', province)
    #         if provinceinfo is None:
    #             await ctx.send("That province does not seem to exist.")
    #             return
    #         if provinceinfo['owner_id'] == 0:
    #             await ctx.send("You cannot force-release a province that is not owned by a user.")
    #             return
    #         owner = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', provinceinfo['owner_id'])
    #         stationedtroops = provinceinfo['troops']
    #         # execute updating information
    #         await conn.execute('''UPDATE cncusers SET undeployed = + $1 WHERE user_id = $3;''',
    #                            stationedtroops, owner['user_id'])
    #         self.map_color(province, provinceinfo['cord'], "#000000", True)
    #         await conn.execute('''INSERT INTO mod_logs(id, mod_id, action, reason) VALUES($1,$2,$3,$4);''',
    #                            ctx.message.id, author.id, f"released province #{province} from {owner['username']}",
    #                            reason)
    #         await ctx.send(f"Province #{province} has been released from {owner['username']}'s control."
    #                        f"All {stationedtroops} in the province have been returned to the undeployed stockpile.")
    #         await owner['user_id'].send(f"Province #{province} has been removed from your control for the "
    #                                     f"following reason: ```{reason}```")
    #         return

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
        async with ctx.typing():
            map = Image.open(fr"{self.map_directory}wargame_blank_save.png").convert("RGBA")
            map.save(fr"{self.map_directory}wargame_provinces.png")
            conn = self.bot.pool
            loop = self.bot.loop
            users = await conn.fetch('''SELECT username, usercolor FROM cncusers;''')
            usersncolors = dict()
            for u in users:
                usersncolors.update({u['username']: u['usercolor']})
            provinces = await conn.fetch('''SELECT * FROM provinces WHERE owner_id != 0;''')
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
                    if p['occupier'] == '':
                        occupier_color = "#000000"
                    else:
                        occupier_color = usersncolors[p['occupier']]
                    await loop.run_in_executor(None, self.occupy_color, p_id, p_cord, occupier_color, color)
        await ctx.send("All owned provinces checked and colored.")

    @commands.command(brief="Checks all provinces and ensures proper ownership.")
    @modcheck()
    async def cnc_owned_check(self, ctx):
        conn = self.bot.pool
        users = await conn.fetch('''SELECT * FROM cncusers;''')
        for u in users:
            owned_provinces = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1;''', u['user_id'])
            p_list = list()
            for p in owned_provinces:
                p_list.append(p['id'])
            await conn.execute('''UPDATE cncusers SET provinces_owned = $1 WHERE user_id = $2;''',
                               p_list, u['user_id'])
        await ctx.send("Done!")

    @commands.command(brief="Sets all trade good colors.")
    @modcheck()
    async def cnc_trade_goods_check(self, ctx):
        conn = self.bot.pool
        provinces = await conn.fetch('''SELECT * FROM provinces;''')
        map = Image.open(fr"{self.map_directory}wargame_blank_save.png").convert("RGBA")
        working = await ctx.send("Working...")
        async with ctx.typing():
            for p in provinces:
                good_color = await conn.fetchrow('''SELECT * FROM trade_goods WHERE name = $1;''', p['value'])
                # obtain the coordinate information
                province_cord = ((int(p['cord'][0])), (int(p['cord'][1])))
                # get color
                try:
                    color = ImageColor.getrgb(good_color['color'])
                except ValueError:
                    return ValueError("Hex code issue")
                # open the map and the province images
                prov = Image.open(fr"{self.province_directory}{p['id']}.png").convert("RGBA")
                # obtain size and coordinate information
                width = prov.size[0]
                height = prov.size[1]
                cord = (province_cord[0], province_cord[1])
                # for every pixel, change the color to the owners
                for x in range(0, width):
                    for y in range(0, height):
                        data = prov.getpixel((x, y))
                        if data != (0, 0, 0, 0):
                            if data != (255, 255, 255, 0):
                                prov.putpixel((x, y), color)
                # convert, paste, and save the image
                prov = prov.convert("RGBA")
                map.paste(prov, box=cord, mask=prov)
            map.save(fr"{self.map_directory}Trade Goods Map.png")
        await working.edit(content="Done!")

    @commands.command(brief="Sets all trade goods.")
    @commands.is_owner()
    async def cnc_set_trade_goods(self, ctx):
        conn = self.bot.pool
        provs = await conn.fetch('''SELECT * FROM provinces;''')
        for p in provs:
            if p['terrain'] == 0:
                if p['river']:
                    goods = ["Wool", "Wool", "Wool", "Wool", "Wool", "Wool", "Wool", "Wool", "Wool", "Wool",
                             "Fur", "Fur", "Fur", "Grain", "Grain", "Grain", "Grain", "Grain", "Grain", "Grain",
                             "Livestock", "Livestock", "Livestock", "Livestock", "Livestock", "Livestock", "Livestock",
                             "Precious Goods", "Spices", "Spices", "Tea and Coffee", "Tea and Coffee", "Tea and Coffee",
                             "Cotton", "Cotton", "Cotton", "Cotton", "Cotton", "Cotton",
                             "Sugar", "Sugar", "Sugar", "Tobacco", "Tobacco", "Tobacco", "Tobacco", "Rare Wood",
                             "Rare Wood", "Glass", "Glass", "Glass", "Glass", "Paper", "Paper", "Paper", "Paper",
                             "Paper", "Fruits", "Fruits", "Fruits", "Fruits", "Wood", "Wood", "Wood", "Wood", "Wood",
                             "Wood",
                             "Wood", "Ivory", "Ivory"]
                    if p['coast']:
                        goods.extend(["Fish", "Fish", "Fish"])
                    good = random.choice(goods)
                    await conn.execute('''UPDATE provinces SET value = $1 WHERE id = $2;''', good, p['id'])
                else:
                    goods = ["Wool", "Wool", "Wool", "Wool", "Wool", "Fur", "Fur", "Fur",
                             "Grain", "Grain", "Grain", "Grain", "Grain",
                             "Livestock", "Livestock", "Livestock", "Livestock", "Livestock", "Precious Goods",
                             "Spices", "Spices", "Tea and Coffee", "Tea and Coffee", "Cotton", "Cotton", "Cotton",
                             "Sugar", "Sugar", "Tobacco", "Tobacco", "Tobacco", "Rare Wood", "Rare Wood",
                             "Glass", "Glass", "Glass", "Glass", "Paper", "Paper", "Paper", "Paper", "Fruits", "Fruits",
                             "Fruits", "Wood", "Wood", "Wood", "Wood", "Wood", "Ivory", "Ivory"]
                    if p['coast']:
                        goods.extend(["Fish", "Fish", "Fish"])
                    good = random.choice(goods)
                    await conn.execute('''UPDATE provinces SET value = $1 WHERE id = $2;''', good, p['id'])
            if p['terrain'] == 1:
                goods = ['Dyes', 'Precious Stones', 'Spices', 'Spices', 'Glass', 'Glass', 'Glass', 'Glass',
                         'Paper', 'Paper', 'Paper', 'Paper', 'Precious Goods', 'Ivory', 'Ivory']
                if p['coast']:
                    goods.extend(["Fish", "Fish", "Fish"])
                good = random.choice(goods)
                await conn.execute('''UPDATE provinces SET value = $1 WHERE id = $2;''', good, p['id'])
            if p['terrain'] == 2:
                if p['river']:
                    goods = ['Fur', 'Fur', 'Fur', 'Grain', 'Grain', 'Grain', 'Grain', 'Grain', 'Grain', 'Grain',
                             'Livestock', 'Livestock', 'Livestock', 'Livestock', 'Livestock', 'Livestock', 'Livestock',
                             'Salt', 'Salt', 'Salt', 'Salt', 'Salt', 'Wine', 'Wine', 'Wine', 'Wine', 'Wine',
                             'Copper', 'Copper', 'Copper', 'Iron', 'Iron', 'Iron', 'Precious Goods', 'Spices', 'Spices',
                             'Tea and Coffee', 'Tea and Coffee', 'Tea and Coffee',
                             'Chocolate', 'Chocolate', 'Chocolate', 'Sugar', 'Sugar', 'Sugar',
                             'Tobacco', 'Tobacco', 'Tobacco', 'Tobacco', 'Rare Wood', 'Rare Wood',
                             'Glass', 'Glass', 'Glass', 'Glass', 'Paper', 'Paper', 'Paper', 'Paper', 'Paper', 'Paper',
                             'Fruits', 'Fruits', 'Fruits', 'Fruits',
                             'Wood', 'Wood', 'Wood', 'Wood', 'Wood', 'Wood', 'Wood',
                             'Tin', 'Tin', 'Tin', 'Ivory', 'Ivory']
                    if p['coast']:
                        goods.extend(["Fish", "Fish", "Fish"])
                    good = random.choice(goods)
                    await conn.execute('''UPDATE provinces SET value = $1 WHERE id = $2;''', good, p['id'])
                else:
                    goods = ['Fur', 'Fur', 'Fur', 'Grain', 'Grain', 'Grain', 'Grain', 'Grain',
                             'Livestock', 'Livestock', 'Livestock', 'Livestock', 'Livestock',
                             'Salt', 'Salt', 'Salt', 'Salt', 'Salt', 'Wine', 'Wine', 'Wine', 'Wine',
                             'Copper', 'Copper', 'Copper', 'Iron', 'Iron', 'Iron', 'Precious Goods', 'Spices', 'Spices',
                             'Tea and Coffee', 'Tea and Coffee',
                             'Chocolate', 'Chocolate', 'Sugar', 'Sugar',
                             'Tobacco', 'Tobacco', 'Tobacco', 'Rare Wood', 'Rare Wood',
                             'Glass', 'Glass', 'Glass', 'Glass', 'Paper', 'Paper', 'Paper', 'Paper',
                             'Fruits', 'Fruits', 'Fruits', 'Wood', 'Wood', 'Wood', 'Wood', 'Wood',
                             'Tin', 'Tin', 'Tin', 'Ivory', 'Ivory']
                    if p['coast']:
                        goods.extend(["Fish", "Fish", "Fish"])
                    good = random.choice(goods)
                    await conn.execute('''UPDATE provinces SET value = $1 WHERE id = $2;''', good, p['id'])
            if p['terrain'] == 5:
                goods = ['Salt', 'Salt', 'Salt', 'Salt', 'Salt', 'Copper', 'Copper', 'Copper', 'Iron', 'Iron', 'Iron',
                         'Precious Goods', 'Spices', 'Spices', 'Precious Stones', 'Precious Stones',
                         'Coal', 'Coal', 'Coal', 'Coal', 'Gold', 'Gold',
                         'Raw Stone', 'Raw Stone', 'Raw Stone', 'Raw Stone', 'Raw Stone',
                         'Silver', 'Silver', 'Silver', 'Tin', 'Tin', 'Tin']
                if p['coast']:
                    goods.extend(["Fish", "Fish", "Fish"])
                good = random.choice(goods)
                await conn.execute('''UPDATE provinces SET value = $1 WHERE id = $2;''', good, p['id'])
            if p['terrain'] == 7:
                goods = ['Precious Goods', 'Spices', 'Spices', 'Silk', 'Silk', 'Silk', 'Silk',
                         'Rare Wood', 'Rare Wood', 'Rare Wood', 'Glass', 'Glass', 'Glass', 'Glass',
                         'Paper', 'Paper', 'Paper', 'Paper', 'Coal', 'Coal', 'Coal', 'Coal', 'Ivory', 'Ivory']
                if p['coast']:
                    goods.extend(["Fish", "Fish", "Fish"])
                good = random.choice(goods)
                await conn.execute('''UPDATE provinces SET value = $1 WHERE id = $2;''', good, p['id'])
            if p['terrain'] == 9:
                goods = ['Fur', 'Fur', 'Fur', 'Precious Goods', 'Spices', 'Glass', 'Glass', 'Glass', 'Glass',
                         'Ivory']
                if p['coast']:
                    goods.extend(["Fish", "Fish", "Fish"])
                good = random.choice(goods)
                await conn.execute('''UPDATE provinces SET value = $1 WHERE id = $2;''', good, p['id'])
        await ctx.send("Done")

    @commands.command(brief="Sets all terrain colors.")
    @commands.is_owner()
    async def cnc_terrain_check(self, ctx):
        conn = self.bot.pool
        provinces = await conn.fetch('''SELECT * FROM provinces;''')
        map = Image.open(fr"{self.map_directory}wargame_blank_save.png").convert("RGBA")
        working = await ctx.send("Working...")
        async with ctx.typing():
            for p in provinces:
                terrain_color = await conn.fetchrow('''SELECT * FROM terrains WHERE id = $1;''', p['terrain'])
                # obtain the coordinate information
                province_cord = ((int(p['cord'][0])), (int(p['cord'][1])))
                # get color
                try:
                    color = ImageColor.getrgb(terrain_color['color'])
                except ValueError:
                    return ValueError("Hex code issue")
                # open the map and the province images
                prov = Image.open(fr"{self.province_directory}{p['id']}.png").convert("RGBA")
                # obtain size and coordinate information
                width = prov.size[0]
                height = prov.size[1]
                cord = (province_cord[0], province_cord[1])
                # for every pixel, change the color to the owners
                for x in range(0, width):
                    for y in range(0, height):
                        data = prov.getpixel((x, y))
                        if data != (0, 0, 0, 0):
                            if data != (255, 255, 255, 0):
                                prov.putpixel((x, y), color)
                # convert, paste, and save the image
                prov = prov.convert("RGBA")
                map.paste(prov, box=cord, mask=prov)
            map.save(fr"{self.map_directory}CNC Terrain Map.png")
        await working.edit(content="Done!")

    @commands.command(brief="Gives names.")
    @commands.is_owner()
    async def cnc_name_all(self, ctx):
        names = ["Seva", "Kezubenu", "Napby", "Djacahdet", "Sepsai", "Kisrimeru", "Sapoyut", "Tarnouru", "Sasotaten",
                 "Bema", "Gesso", "Shari", "Acne", "Menrusiris", "Shapo", "Senebenu", "Tabe", "Behbu", "Dessasiris",
                 "Sepdjesut", "Tarre", "Khepeset", "Nemtadjed", "Behzum", "Tjendepet", "Cupo", "Wasbumunein",
                 "Kerdjerma", "Khemabesheh", "Kenupis", "Boroupoli", "Epione", "Pelyma", "Golgona", "Thebekion",
                 "Juktorus", "Phanipolis", "Tyraphos", "Pavlosse", "Eubacus", "Rhodyrgos", "Myrolgi", "Setrias",
                 "Massipolis", "Corcyreum", "Megarina", "Laodigona", "Posane", "Panteselis", "Arsaistos", "Rhegenes",
                 "Abymna", "Lampsens", "Benion", "Golgarae", "Aytippia", "Thespeucia", "Mallaza", "Cythene",
                 "Agrinaclea", "Zuivild", "Thisruil", "Ilvynyln", "Teapost", "Starmore", "Strawshire", "Hollowgarde",
                 "Mossmore", "Tabanteki", "Wolrion", "Kimnia", "Arakuru", "Gobafidi", "Narakare", "Qamatlong", "Mesane",
                 "Mandujang", "Mankalane", "Mobane", "Seria", "Wolmadanha", "Omanie", "Genthanie", "Babong", "Quseng",
                 "Meweng", "Lethagonami", "Danzibanyatsi", "Kulembu", "Salkal", "Saldakuwa", "Kawa", "Lahandja",
                 "Namaferu", "Moine", "Hukuhaba", "Malume", "Vulembu", "Allanrys", "Kilanga", "Okashapi", "Oshirara",
                 "Lofale", "Pokojea", "Selerobe", "Tlothe", "Iwagata", "Mutsutsukawa", "Changchong", "Meishui",
                 "Khairmani", "Nogoonkh", "Kangwon", "Hamsu", "Taewang", "Hamchaek", "Sinuihung", "Sinuicheon",
                 "Taigaa", "Sogusi", "Nurhakisla", "Jirozmian", "Yasousar", "As", "Sasiyyah", "Etadfa", "Mirut",
                 "Wadifer", "Sakarout", "Mneesayr", "Masyamas", "Rafhamloj", "Wadireg", "Choinuur", "Pingrao",
                 "Panchun", "Yatori", "Kumaraha", "Yahakonai", "Qahanieh", "Arisyoun", "Tel", "Khanayah", "As",
                 "Saysan", "Khorranab", "Alaroft", "Iliborlu", "Adankum", "Seafurah", "Kivuadi", "Rausoka", "Barekawa",
                 "Tanimotu", "Rakawald", "Okairuru", "Niupia", "Utusi", "Fetofesia", "Fohi", "Geelide", "Seafave",
                 "Vumbavua", "Sobalevu", "Tekatiratai", "Nuotebiki", "Hokitakere", "Mapuapara", "Faleamalo", "A'ufaga",
                 "Telefuiva", "Lofakulei", "Ivorgarde", "Glockrath", "Charward", "Ivoryham", "Dawnglen", "Dreadwall",
                 "Aerahaben", "Legstead", "Tattingstein", "Flammore", "Sleetdrift", "Ycemire", "Fljot", "Meoalfell",
                 "Hraunaheior", "Hagbarosholmr", "Kollsvik", "Hafsloekr", "Hrafnstoptir", "Eskiholt", "Jokulsarhlio",
                 "Hafgrimsfjoror", "Riocarí", "Jagar", "Architanas", "Nulriel", "Tonnéte", "Sinra", "Immia",
                 "Makourama", "Pago", "Abenastina", "Tápiz", "Ejimare", "Limonum", "Caudium", "Armorica", "Dianinum",
                 "Emporiae", "Bilbilis", "Ostium", "Sinope", "Atrans", "Concangis", "Tuder", "Selymbria", "Cannabiaca",
                 "Vinovium", "Catania", "Portus", "Odessus", "Tenedo", "Mursa", "Velipa", "Seveyungri", "Yelalabuga",
                 "Anarechny", "Calacadis", "Abylune", "Liquasa", "Puritin", "Posegia", "Belipis", "Thelor", "Tsunareth",
                 "Tynea", "Geythis", "Tempemon", "Thalareth", "Liqucadis", "Tethton", "Paciris", "Nepturia",
                 "Levialean", "Boyrem", "Aciolis", "Hydgia", "Sireria", "Liquiri", "Navathis", "Liquasa", "Salania",
                 "Aciopis", "Berylora", "Riverem", "Merlean", "Amphireth", "Nereicada", "Abyrey", "Scylor", "Belilean",
                 "Donoch", "Levialore", "Aquasa", "Ashamon", "Salaren", "Tsuloch", "Hytin", "Chaszuth", "Microd",
                 "Kaliz", "Taltahrar", "Vazulzak", "Tunkhudduk", "Miggiddoz", "Kaakrahnath", "Joggrox", "Nakkuss",
                 "Zukkross", "Rutago", "Gato", "Yirbark", "Ellaba", "Maganango", "Ruhenhengeri", "Buye", "Ufecad",
                 "Mamo", "Mlankindu", "Biharari", "Jira", "Kampagazi", "Apayo", "Kamudo", "Atrophy", "Scythe",
                 "Carthage", "Dawnbury", "Quellton", "Isolone", "Termina", "Krslav", "Vsekolov", "Democaea", "Myrini",
                 "Tylamnus", "Lamesus", "Alyros", "Demike", "Thyrespiae", "Eretrissos", "Heraclymna", "Thuriliki",
                 "Kyratrea", "Lampsomenus", "Mareos", "Phliesos", "Oncheron", "Cumespiae", "Myndasae", "Acomenion",
                 "Psychrinitida", "Cumakros", "Aigous", "Gelaclea", "Gythagoria", "Elaticus", "Morgocaea",
                 "Leontinitida", "Orastro", "Himos", "Losse", "Gorgox", "Paphateia", "Lefkanthus", "Hierinope",
                 "Onchapetra", "Olamum", "Rhypada", "Himarnacia", "Katyros", "Thasseron", "Thassofa", "Metens",
                 "Moleporobe", "Nokapi", "Qetika", "Qetithing", "Omudu", "Otjimna", "Ekanbron", "Mitief", "Kwano",
                 "Movone", "Lobashe", "Lotrowe", "Noma", "Thayatseng", "Ongwema", "Okahadive", "Kruba", "Allankal",
                 "Nsabasena", "Dulevise", "Kubuye", "Saldanus", "Soha", "Rehovi", "Oshidja", "Meyokabei", "Pihane",
                 "Molepodibe", "Thamalala", "Westwall", "Freyview", "Bayhollow", "Frostvalley", "Smallstrand",
                 "Grimbay", "Limestar", "Southborough", "Wintermoor", "Arrowstrand", "Borville", "Marilet", "Borgueu",
                 "Ironfield", "Ruststar", "Silenttown", "Silvershore", "Avinia", "Cálma", "Virtos", "Orodorm",
                 "Tomadura", "Bulle", "Andanea", "Grallón", "Gipuscay", "Cagona", "Zamostile", "Alzilavega", "Outiva",
                 "Zaravila", "Sagoza", "Rouyonne", "Bacourt", "Cololimar", "Grelly", "Sarsart", "Vinmont", "Beaufort",
                 "Puroux", "Marlimar", "Orsier", "Whisperpeak", "Lowbellow", "Thingorge", "Quickpeak", "Talonhallow",
                 "Copperstead", "Bonetrail", "Barebank", "Onyxpeak", "Wrycanyon", "Starkpeaks", "Buelita", "Nueco",
                 "Pola", "Quecos", "Recalco", "Rejanes", "Yusquile", "Carcos", "Jinoral", "Guacan", "Ditos", "Wiwiya",
                 "Talaba", "Cuyatal", "Rerio", "Aposonate", "Atijutla", "Mipiles", "Sarillos", "Jalacho", "Volnola",
                 "Quilica", "Priguaque", "Trujirito", "Salamento", "Aguanahu", "Cojulupe", "Atinal", "Jara",
                 "Trinilores", "Ponlants", "Hepmagne", "Clerbiens", "Sarfannfik", "Oqaattaq", "Napaluitsup",
                 "Cajemoros", "Penjachuca", "Chitecas", "Chesmore", "Scarmouth", "Canterster", "Autumncester",
                 "Greenwall", "Brighstone", "Ocosingo", "Xalacoco", "Jiutelende", "Sirapaluk", "Nutaarhivik", "Kuumtu",
                 "Burdiac", "Garmis", "Lebridge", "Flushgard", "Thistlehelm", "Mekkadale", "Sparkwall", "Plumewatch",
                 "Freelmorg", "Mummadogh", "Finkipplurg", "Fili", "Keenfa", "Dintindeck", "Glostos", "Imblin",
                 "Fonnipporp", "Wigglegate", "Landbrunn", "Gerasweg", "Antberge", "Knokberge", "Périssons", "Caluçon",
                 "Gailkirchen", "Ansholz", "Macvan", "Mullindoran", "Dikkerk", "Asdaal", "Spreitenbach", "Appenlach",
                 "Poyslach", "Oudenhout", "Valès", "Brugleeuw", "Cassons", "Tangerschau", 'Spalion', 'Rethyndra',
                 'Kaisasina', 'Grervara', 'Miadananitra', 'Tsarasirabe', 'Soavinatanana',
                 'Antsinimena', 'Fandrabava', 'Arikaraka', 'Fandravola', 'Wokagee', 'Lesliaj', 'Kryeliku', 'Llalot',
                 'Xhataj', 'Xhycyrë', 'Budakovec', 'Bullajt', 'Neuschlag', 'Ebreichdeck', 'Amdenz', 'Vöcklabühel',
                 'Hollaweil', 'Lustenstein', 'Dornnau', 'Ermoulonghi', 'Prevedri', 'Heravala', 'Polipoi', 'Vavamanitra',
                 'Antsolaona', 'Amparatsetra', 'Betatra', 'Berovombe', 'Antafolotra', 'Vohimavony', 'Booriwa', 'Ceras',
                 'Mamumarë', 'Rrogolenë', 'Vërkopi', 'Livasekë', 'Kugjun', 'Pasekë', 'Ansten', 'Wolfstadt', 'Götkreis',
                 'Altental', 'Kirchdenz', 'Terben', 'Gänsernkirchen', 'Floliada', 'Metarni', 'Vounina', 'Edestiada',
                 'Tsalangwe', 'Mitunte', 'Domamasi', 'Blalaomo', 'Mponera', 'Limlanje', 'Ngache', 'Poonbilli', 'Toko',
                 'Šipojaš', 'Stijki', 'Bijeldor', 'Kalengrad', 'Trehać', 'Caska', 'Sherpenwerpen', 'Dillaas',
                 'Nieuwport', 'Halstraten', 'Torstraten', 'Westden', 'Landtals', 'Messimezia', 'Sassarence',
                 'Bitoraele', 'Scabria', 'Thyochenza', 'Maloji', 'Chitiza', 'Chikutete', 'Phade', 'Nathenkota',
                 'Malaotheche', 'Myamine', 'Neslavgrad', 'Jazin', 'Viška', 'Traboj', 'Čapčac', 'Čedanj', 'Milišća',
                 'Zothout', 'Dikzen', 'Korteind', 'Oudenhal', 'Dammuide', 'Weststraten', 'Nieuwschot', 'Lamellino',
                 'Cagliana', 'Collesaro', 'Baghetonto', 'Xabuto', 'Naputo', 'Moatida', 'Chikulo', 'Macilacuala',
                 'Mutuabo', 'Lilo', 'Balloundra', 'Rakopan', 'Blagoevski', 'Svobol', 'Provarna', 'Stamvishte', 'Kubvo',
                 'Gabrobrod', 'Alenlet', 'Besanluire', 'Martoise', 'Aviçon', 'Bergessonne', 'Vierbonne', 'Aurigneux',
                 'Civilerno', 'Cinisto', 'Faersala', 'Modivia', 'Marralacuala', 'Xane', 'Mansano', 'Mansano', 'Resdica',
                 'Monba', 'Nampulimane', 'Cooldong', 'Samovin', 'Pavlikovski', 'Petshte', 'Ikhlene', 'Tutravo',
                 'Pomolikeni', 'Petva', 'Chaveil', 'Avignan', 'Angousart', 'Narzon', 'Sarsier', 'Bournoît', 'Boursier',
                 'Almacos', 'Reniche', 'Guavoa', 'Guija', 'Chabezi', 'Solengwa', 'Lundashi', 'Kabogwe', 'Kawamzongwe',
                 'Mponlunga', 'Zambewezi', 'Caideena', 'Bremobor', 'Krikovar', 'Samorinja', 'Stovar', 'Vula',
                 'Kutivača', 'Orarica', 'Großbruck', 'Lüdinghöring', 'Elsterbog', 'Elmroda', 'Gailhude', 'Dillenwig',
                 'Eltershafen', 'Manguache', 'Esmoxa', 'Batejo', 'Meamoz', 'Maabwe', 'Luwinwezi', 'Sibombwe', 'Mpila',
                 'Lugwi', 'Lukusama', 'Kapupo', 'Manlang', 'Jezejevec', 'Opatilok', 'Križepina', 'Dubropin',
                 'Slatizerce', 'Bjegrad', 'Ilorovo', 'Adebog', 'Osterlein', 'Cuxkamp', 'Romroda', 'Gladenhude',
                 'Ersten', 'Alsschau', 'Trasmo', 'Vibos', 'Camagal', 'Gafarosa', 'Lupagani', 'Mazoru', 'Buton', 'Gwani',
                 'Raffirowa', 'Chimanira', 'Chakage', 'Turbawa', 'Sušiles', 'Iličani', 'Vevto', 'Skoplesta', 'Belmica',
                 'Bikov', 'Lojašeišta', 'Dublee', 'Clonkilty', 'Granderry', 'Tullanard', 'Tullahal', 'Newney',
                 'Dunford', 'Cavila', 'Guarcia', 'Galirez', 'Ávirón', 'Penhati', 'Bindugora', 'Chitunwayo', 'Gopanzi',
                 'Goni', 'Shamdu', 'Marondera', 'Gooneragan', 'Dojrovo', 'Poja', 'Zabar', 'Velša', 'Krivotovo',
                 'Brvenijusa', 'Mirabruševo', 'Macgar', 'Clonakee', 'Maccommon', 'Shanway', 'Castlegheda', 'Naran',
                 'Dubtowel', 'Raelellón', 'Márrol', 'Seria', 'Orova', 'Vaceni', 'Doroteşti', 'Gioba', 'Târrest',
                 'Cernarşa', 'Piterşa', 'Conmon', 'Amersdaal', 'Zoetermegen', 'Staventer', 'Devenberg', 'Dierburg',
                 'Blokstadt', 'Asren', 'Zamovia', 'Valejón', 'Zastela', 'Riorez', 'Balgăşani', 'Panteghetu', 'Bârftea',
                 'Timirad', 'Buhuşiţa', 'Fetegalia', 'Slojud', 'Waaloord', 'Amerskerk', 'Ashuizen', 'Slolo',
                 'Amstelstadt', 'Emmelzaal', 'Ashof', 'Knjazamane', 'Stanirig', 'Konica', 'Arankinda', 'Panzar',
                 'Šavor', 'Granovci', 'Laustätten', 'Wädensberg', 'Kreuzstein', 'Opthal', 'Opnacht', 'Friseen',
                 'Freienbach', 'Kragudište', 'Belvor', 'Novac', 'Arirug', 'Aramane', 'Kraguvac', 'Panrig', 'Reilach',
                 'Laufenkon', 'Herneuve', 'Menbon', 'Steffisborn', 'Ostermance', 'Ergen', 'Konice', 'Dravovica',
                 'Črnolavž', 'Trbojice', 'Murskem', 'Rogaje', 'Beltinci', 'Spojba', 'Jerice', 'Škofkem', 'Noše',
                 'Mujana', 'Ratina', 'Jagogaška', 'Kongehus', 'Skjoldbæk', 'Vejlev', 'Guldhus', 'Dybborg', 'Smedestrup',
                 'Karlsborg', 'Fladbæk', 'Vestergård', 'Vindholt', 'Halrup', 'Kirkehus', 'Tubbokaye', 'Kalintsa',
                 'Pizhany', 'Zhytkakaw', 'Dudok', 'Vesterkilde', 'Birkestrup', 'Enshus', 'Lillerup', 'Møllerup',
                 'Strandstrup', 'Guldskov', 'Silkeholt', 'Rødhavn', 'Karlsbæk', 'Bjørnbæk', 'Rødkilde', 'Vitsyezyr',
                 'Skitrykaw', 'Shchusna', 'Navapotsavichy', 'Narostavy', 'Tammme', 'Tamvi', 'Vilsi', 'Pärpina', 'Kärva',
                 'Kiviõtu', 'Räru', 'Kärpina', 'Otesuu', 'Kaldi', 'Kiviõna', 'Kargeva', 'Litště', 'Vsebram', 'Kobíč',
                 'Těkolov', 'Valapa', 'Palde', 'Sinsa', 'Räpila', 'Karski', 'Karngi', 'Põllin', 'Kurepää', 'Kiviõsalu',
                 'Abgeva', 'Narme', 'Tajandi', 'Rapli', 'Uhernec', 'Valabem', 'Hrakov', 'Kroměkolov', 'Chomusou',
                 'Heisaari', 'Mänranta', 'Ähtäkumpu', 'Juanni', 'Kuripunki', 'Juanttinen', 'Kokekola', 'Keusämäki',
                 'Kitali', 'Ylöpula', 'Heissa', 'Pietarni', 'Balota', 'Töson', 'Szartak', 'Lajojosmizse', 'Oroszna',
                 'Riihivalta', 'Orimamäki', 'Valkeani', 'Huisuu', 'Nosiä', 'Ylövala', 'Niniemi', 'Haniemi', 'Raaseko',
                 'Raittinen', 'Kanttila', 'Ulranta', 'Kiskunta', 'Keszna', 'Tatak', 'Karnor', 'Szenbóvár', 'Hólhólmur',
                 'Mosfellssós', 'Reykvöllur', 'Hvolsfjörður', 'Keflajahlíð', 'Grundarsker', 'Blönnarnes',
                 'Eyrarjarhverfi', 'Þórsnesi', 'Dalnes', 'Garðaseyri', 'Dalkrókur', 'Comspol', 'Strănești',
                 'Rîșcamenca', 'Străză', 'Cupdul', 'Vopnaholt', 'Hvanseyri', 'Hnífshólar', 'Seyðissey', 'Þórsnes',
                 'Vestvöllur', 'Stukhólar', 'Garðaganes', 'Þorlákshólmur', 'Keflasós', 'Kópafjörður', 'Seltjarhöfn',
                 'Vatroca', 'Hînceriopol', 'Tereni', 'Iana', 'Rîșcați', 'Grolupe', 'Lienci', 'Vipils', 'Aluklosta',
                 'Salactene', 'Ziceni', 'Prielsi', 'Sigulda', 'Salacele', 'Jauncut', 'Vigazilani', 'Salaclozi',
                 'Piwice', 'Świmyśl', 'Łomkary', 'Kory', 'Śląnin', 'Jurlava', 'Bauslava', 'Sabidava', 'Strenza',
                 'Ligatnas', 'Aknibe', 'Alodava', 'Kargava', 'Valdone', 'Limnda', 'Varakgriva', 'Sabigums', 'Chezno',
                 'Chenowo', 'Piebunalski', 'Płowiec', 'Soworzno', 'Mažeikda', 'Priegara', 'Daugbrade', 'Druskiai',
                 'Marijventis', 'Grigtos', 'Dusetme', 'Drusštas', 'Rudišninka', 'Priecininkai', 'Utnai', 'Mažeiklute',
                 'Căliraolt', 'Galanaia', 'Dolhadiru', 'Ciatina', 'Ovilonta', 'Ramysiejai', 'Ignalbarkas', 'Gargbalis',
                 'Dusetkiai', 'Jieztavas', 'Kaiškuva', 'Plunjoji', 'Radkruojis', 'Jurkule', 'Šventai', 'Vergiai',
                 'Dukvas', 'Orășa', 'Însudud', 'Bohoi', 'Bebiu', 'Armănești', 'Grimhelle', 'Oshammer', 'Hokkbu',
                 'Molbak', 'Osstrøm', 'Varros', 'Verdalhelle', 'Ulsteinfjord', 'Arenstad', 'Elvik', 'Grimhalsen',
                 'Hønekim', 'Snivo', 'Zlačín', 'Dunajňava', 'Svärica', 'Stropky', 'Asrum', 'Søgjøen', 'Finnros',
                 'Tromvåg', 'Ålerum', 'Farsøor', 'Statjøen', 'Breksøra', 'Harvern', 'Brønnøystrøm', 'Kongsden',
                 'Verdaljøen', 'Dudintár', 'Ilajov', 'Návičovo', 'Baršiná', 'Marhovec', 'Torsholm', 'Oxelöhall',
                 'Landskil', 'Ulricellefteå', 'Bollbro', 'Gammaltorp', 'Bollbro', 'Österstad', 'Oxelötorp', 'Finburg',
                 'Uppbo', 'Borgsås', 'Uzhhove', 'Ochadilsk', 'Berchyn', 'Uzhkivka', 'Ananruch', 'Mjölsås', 'Östlänge',
                 'Huskhamn', 'Gamlesele', 'Djurskil', 'Fagerbacka', 'Sundbyvalla', 'Skogby', 'Oxelögrund', 'Bollhärad',
                 'Uddekoga', 'Eskilfors', 'Zbodiach', 'Polonihiv', 'Henirad', 'Chervonivka', 'Illinyk', 'Dalabey',
                 'Begegaç', 'Sivriyayla', 'Badekoyunlu', 'Pirakapi', 'Kocame', 'Kemeca', 'Sivrikisla', 'Khorashtar',
                 'Kashavar', 'Herist', 'Ahvaft', 'Ahvalard', 'Behbast', 'Abayaan', 'Kilaqqez', 'Nibjah', 'Quditha',
                 'Ctesirah', 'Balasit', 'Tall-Qubayr', 'Momadi', 'Zakhobil', 'Al-Hasyoun', 'Khushawai', 'Al-Kareya']
        conn = self.bot.pool
        provs = await conn.fetch('''SELECT * FROM provinces WHERE name = '';''')
        iterations = 0
        for p in provs:
            await conn.execute('''UPDATE provinces SET name = $1 WHERE id = $2;''', names[iterations], p['id'])
            iterations += 1
        await ctx.send(f"{iterations} provinces named.")

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
            await conn.execute('''DELETE FROM cnc_modifiers;''')

            ################ USER UPDATING ################

            for u in userids:
                user = self.bot.get_user(u)
                credits_added = 0
                # pull out the data and get a list of provinces and trade routes
                userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', u)
                # establish manpower, tax rate, and tax income
                initial_manpower = userinfo['manpower']
                tax_rate = userinfo['taxation'] / 100
                taxes = initial_manpower * tax_rate
                # set military upkeep and public services rates and remove their amount from taxes
                military_upkeep = userinfo['military_upkeep'] / 100
                public_services = userinfo['public_services'] / 100
                taxes *= 1 - (military_upkeep + public_services)
                # add taxes
                credits_added += taxes
                # establish initial trade access
                initial_trade_access = 0.5
                # establish total troops, civil war, and provinces variables
                total_troops = 0
                civil_war = False
                provinces = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1;''', u)
                provinces_owned = [p['id'] for p in provinces]
                occupied_count = await conn.fetchrow('''SELECT count(*) FROM provinces WHERE occupier_id = $1;''', u)
                # set taxes, military upkeep, and public service rates to whole-number values
                tax_rate *= 100
                military_upkeep *= 100
                public_services *= 100

                ################ TECH MODIFIERS UPDATING ################

                # update tech modifiers
                await conn.execute('''INSERT INTO cnc_modifiers(user_id) VALUES($1);''', u)
                tech = Technology(userinfo['username'], techs=userinfo['researched'], bot=self.bot)
                await tech.effects()
                # fetch all tech modifiers
                modifiers = await conn.fetchrow('''SELECT * FROM cnc_modifiers WHERE user_id = $1;''', u)

                ################ EVENT UPDATING ################

                # check for event
                event_info = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1 and event != '';''', u)
                # if there is no event, pick event and run
                if event_info is None:
                    random_event = await conn.fetchrow('''SELECT * FROM cnc_events WHERE type = 'national' 
                    ORDER BY random();''')
                    event = Events(bot=self.bot, nation=userinfo['username'], event=random_event['name'])
                    await event.event_effects()
                # otherwise, update effects
                else:
                    event = Events(bot=self.bot, nation=userinfo['username'], event=event_info['event'], current=True)
                    await event.event_effects()

                ################ LIMIT UPDATING ################

                # fort/city/port/trade route limit update
                if len(provinces_owned) <= 5:
                    structure_cost = 0
                    cities = await conn.fetchrow(
                        '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND city = True;''',
                        userinfo['user_id'])
                    ports = await conn.fetchrow(
                        '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND port = True;''',
                        userinfo['user_id'])
                    forts = await conn.fetchrow(
                        '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND fort = True;''',
                        userinfo['user_id'])
                    if cities['count'] > 1:
                        structure_cost += 1000 * (cities['count'] - 1)
                    if ports['count'] > 1:
                        structure_cost += 500 * (ports['count'] - 1)
                    if forts['count'] > 1:
                        structure_cost += 700 * (forts['count'] - 1)
                    await conn.execute(
                        '''UPDATE cncusers SET citylimit = 1, portlimit = 1, fortlimit = 1 WHERE user_id = $1;''',
                        userinfo['user_id'])
                else:
                    # calculate limits
                    structure_cost = 0
                    fortlimit = math.floor((len(provinces_owned) - 5) / 5) + 1
                    portlimit = math.floor((len(provinces_owned) - 5) / 3) + 1
                    citylimit = math.floor((len(provinces_owned) - 5) / 7) + 1
                    if userinfo['focus'] == 's':
                        fortlimit += 1
                    if userinfo['focus'] == 'e':
                        portlimit += 1
                    cities = await conn.fetchrow(
                        '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND city = True;''',
                        userinfo['user_id'])
                    ports = await conn.fetchrow(
                        '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND port = True;''',
                        userinfo['user_id'])
                    forts = await conn.fetchrow(
                        '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND fort = True;''',
                        userinfo['user_id'])
                    if cities['count'] > citylimit:
                        structure_cost += 1000 * (cities['count'] - citylimit)
                    if ports['count'] > portlimit:
                        structure_cost += 500 * (ports['count'] - portlimit)
                    if forts['count'] > fortlimit:
                        structure_cost += 700 * (forts['count'] - fortlimit)
                    await conn.execute(
                        '''UPDATE cncusers SET citylimit = $1, portlimit = $2, fortlimit = $3 WHERE user_id = $4;''',
                        citylimit, portlimit, fortlimit, userinfo['user_id'])
                # sets trade route limit
                trade_route_limit = 0
                # if the user is a great power, +1 trade route
                if userinfo['great_power']:
                    trade_route_limit += 1
                if userinfo['capital'] != 0:
                    trade_route_limit += 1
                # for every city +1 and for every two ports +1
                trade_route_limit += cities['count']
                trade_route_limit += math.floor(ports['count'] / 2)
                # if Banking and Investments is researched, add 1
                trade_route_limit += int(modifiers['trade_route'])
                # if the current trade route number is too high, reduce effective trade gain
                outgoing_count = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE type = 'trade' AND 
                              active = True AND sender_id = $1;''', userinfo['user_id'])
                outgoing_info = await conn.fetchrow('''SELECT * FROM interactions WHERE type = 'trade' AND 
                              active = True AND sender_id = $1;''', userinfo['user_id'])
                if outgoing_count['count'] is None:
                    outgoing_count = 0
                else:
                    outgoing_count = outgoing_count['count']
                incoming_count = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE type = 'trade' AND 
                                             active = True AND recipient_id = $1;''', userinfo['user_id'])
                if incoming_count['count'] is None:
                    incoming_count = 0
                else:
                    incoming_count = incoming_count['count']
                trade_debuff = 1
                if outgoing_count > trade_route_limit:
                    for i in range(trade_route_limit - outgoing_count):
                        trade_debuff -= .02
                # for every domestic trade route, +10% access. For every foreign trade route, +5% access
                if outgoing_info is not None:
                    outgoing_recipients = list()
                    for o in outgoing_info:
                        outgoing_recipients.append(o['recipient'])
                    outgoing_repeat = Counter(outgoing_recipients)
                    # for every repeat trade route, decrease by 2% down to 0%
                    for r in outgoing_repeat:
                        if r >= 6:
                            initial_trade_access = .3
                        else:
                            initial_trade_access += (10 - (r - 1) * r) / 100 * (
                                modifiers['trade_route_efficiency_mod'])
                # calculate initial trade access
                initial_trade_access += (.05 * incoming_count) * trade_debuff

                ################ NATIONAL UNREST UPDATING ################

                # check national Unrest for civil war and add national Unrest
                national_unrest = userinfo['national_unrest']
                # if the national unrest is above 80
                if len(provinces) > 9:
                    if national_unrest >= 80:
                        # roll a d100
                        unrest_roll = randint(0, 100)
                        # if the d100 is below or equal to the national unrest, trigger civil war
                        if unrest_roll <= national_unrest:
                            # fetch all provinces and get half
                            owned_provinces = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1 AND
                                          occupier_id = $1;''', user.id)
                            owned_provinces = [p['id'] for p in owned_provinces]
                            half_owned = math.floor(len(owned_provinces) / 2)
                            provinces_rebelling = sample(owned_provinces, half_owned)
                            # for all provinces rebelling, get their information
                            for pr in provinces_rebelling:
                                p_info = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', pr)
                                if p_info is None:
                                    continue
                                # add the remaining troops to the undeployed amount
                                undeployed = userinfo['undeployed']
                                troops_remaining = p_info['troops'] - (p_info['manpower'] * 2)
                                if troops_remaining <= 0:
                                    troops_remaining = 0
                                # update all information
                                await conn.execute('''UPDATE cncusers SET undeployed = $1 WHERE 
                                              user_id = $2;''', undeployed + troops_remaining, u)
                                await conn.execute('''UPDATE provinces SET occupier = '', occupier_id = 0, 
                                unrest = 0, troops = $1 WHERE id = $2;''', p_info['manpower'] * 2, pr)
                                await self.bot.loop.run_in_executor(None, self.occupy_color, pr, p_info['cord'][0:2],
                                                                    "#000000", userinfo['usercolor'])
                            provinces_rebelling.sort()
                            provinces_rebelling_string = ', '.join(str(e) for e in provinces_rebelling)
                            await user.send(f"Province(s) {provinces_rebelling_string} have rebelled in a civil war"
                                            f" due to high national unrest ({national_unrest})!")
                            civil_war = True
                # add national Unrest
                national_unrest = 0
                # do complicated maths to figure out the unrest rate
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
                # add national unrest suppression modifier
                public_service_unrest *= modifiers['national_unrest_suppression_efficiency_mod']
                # add unrest and cap or floor
                national_unrest += tax_unrest + public_service_unrest + military_upkeep_unrest
                if national_unrest > 100:
                    national_unrest = 100
                elif national_unrest < 0:
                    national_unrest = 0
                await conn.execute('''UPDATE cncusers SET national_unrest = $1 WHERE user_id = $2;''',
                                   national_unrest, u)

                ################ PROVINCE UPDATING ################

                provinces_rebelled = list()
                structures_destroyed = 0
                workshops_n_temples = 0
                # update all provinces
                for p in provinces_owned:
                    if p == 0:
                        continue
                    # fetch province info
                    p_info = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', p)
                    if p_info['uprising']:
                        # if the unrest is less than a random number between 1 and 100, end uprising
                        if p_info['unrest'] < randint(1, 100):
                            await conn.execute('''UPDATE provinces SET uprising = False WHERE id = $1;''', p)
                        # otherwise, continue uprising
                        else:
                            # calculate current unrest
                            unrest = 0
                            # reduce unrest for troops present
                            troops_unrest = p_info['troops'] / -100
                            if userinfo['great_power']:
                                troops_unrest *= 2
                            # add local unrest suppression efficiency mod
                            troops_unrest *= modifiers['local_unrest_suppression_efficiency_mod']
                            # do complicated maths
                            tax_unrest = math.ceil(10 * (1 + 1) ** ((tax_rate / 5) - 1))
                            military_upkeep_unrest = -round(
                                (1 * (1 + 1) ** (military_upkeep / 5.75 - 1)) + ((1 * (1 + 1) ** (
                                        military_upkeep / 10 - 1)) * 0.75))
                            if public_services < 15:
                                public_service_unrest = round(30 - public_services * 2)
                            else:
                                public_service_unrest = -round((3 * (1 + 0.75) ** ((public_services - 23) / 5) - 1))
                            # add unrest and cap or floor
                            unrest += tax_unrest + public_service_unrest + military_upkeep_unrest + troops_unrest
                            if unrest > 100:
                                unrest = 100
                            elif unrest < 0:
                                unrest = 0
                            await conn.execute('''UPDATE provinces SET unrest = $1 WHERE id = $2;''', unrest, p)
                            continue
                    total_troops += p_info['troops']

                    ################ PRODUCTION UPDATING ################

                    # define production value, producing amount, market value modifiers, and workshop production
                    production_value = 1
                    market_value_mod = 1
                    workshop_production = 0
                    # for every city, add .5 production
                    if p_info['city']:
                        production_value += 0.5
                    # for every port, add 25% market value to the local good, if it is not gold or silver
                    if p_info['port']:
                        if p_info['value'] not in ['Gold', 'Silver']:
                            market_value_mod += 0.25
                    # for every workshop, add 1 * the production modifier
                    if p_info['workshop']:
                        workshop_production += 1 * modifiers['workshop_production_mod']
                        workshops_n_temples += 1
                    # add all production to the base province production
                    producing = p_info['production'] * (production_value + modifiers['production_mod'])
                    # calculate local trade good value and total gain
                    trade_good = await conn.fetchrow('''SELECT * FROM trade_goods WHERE name = $1;''', p_info['value'])
                    credits_added += (((trade_good['market_value'] +
                                        modifiers[f'{self.space_replace(p_info["value"]).lower()}_mod']) *
                                       market_value_mod) * producing) * initial_trade_access

                    ################ LOCAL UNREST UPDATING ################

                    # check local Unrest for local uprising and add local Unrest
                    local_unrest = p_info['unrest']
                    # if the local Unrest is greater than 50
                    if len(provinces) > 4:
                        if local_unrest >= 50:
                            # roll a d100
                            unrest_roll = randint(0, 100)
                            # if the d100 is greater than the local Unrest, trigger an uprising
                            if unrest_roll <= local_unrest:
                                # if a city is present, 20% chance for destruction
                                if p_info['city']:
                                    if randint(1, 100) >= 80:
                                        structures_destroyed += 1
                                        await conn.execute('''UPDATE provinces SET city = False WHERE id = $1;''', p)
                                # if a fort is present, 10% chance for it to be destroyed
                                if p_info['fort']:
                                    if randint(1, 100) >= 90:
                                        structures_destroyed += 1
                                        await conn.execute('''UPDATE provinces SET fort = False WHERE id = $1;''', p)
                                # if a port is present 20% chance for it to be destroyed
                                if p_info['port']:
                                    if randint(1, 100) >= 80:
                                        structures_destroyed += 1
                                        await conn.execute('''UPDATE provinces SET port = False WHERE id = $1;''', p)
                                # calculate troops damage and update
                                troops_attacked = p_info['troops'] - \
                                                  (randint((p_info['manpower']) / 2, p_info['manpower']))
                                if troops_attacked < 0:
                                    troops_attacked = 0
                                await conn.execute('''UPDATE provinces SET uprising = True, troops = $2
                                              WHERE id = $1;''', p, troops_attacked)
                                provinces_rebelled.append(p)
                    # add Unrest
                    unrest = 0
                    # if there is a civil war ongoing, -20 unrest
                    if civil_war:
                        unrest -= 20
                    # do complicated maths
                    troops_unrest = p_info['troops'] / -100
                    tax_unrest = math.ceil(10 * (1 + 1) ** ((tax_rate / 5) - 1))
                    military_upkeep_unrest = -round((1 * (1 + 1) ** (military_upkeep / 5.75 - 1)) + ((1 * (1 + 1) ** (
                            military_upkeep / 10 - 1)) * 0.75))
                    if public_services < 15:
                        public_service_unrest = round(30 - public_services * 2)
                    else:
                        public_service_unrest = -round((3 * (1 + 0.75) ** ((public_services - 23) / 5) - 1))
                    # add unrest and cap or floor
                    unrest += tax_unrest + public_service_unrest + military_upkeep_unrest + troops_unrest
                    # if there is a temple, reduce to 85%
                    if p_info['temple']:
                        unrest *= 0.85
                        workshops_n_temples += 1
                    if unrest > 100:
                        unrest = 100
                    elif unrest < 0:
                        unrest = 0
                    # update unrest in province
                    await conn.execute('''UPDATE provinces SET unrest = $1 WHERE id = $2;''', unrest, p)
                    ################ EXIT PROVINCE UPDATING ################

                # if there are uprising provinces
                if len(provinces_rebelled) != 0:
                    provinces_rebelled_string = ', '.join(str(p) for p in provinces_rebelled)
                    await user.send(f"The population of province(s) {provinces_rebelled_string} "
                                    f"have risen up due to high unrest ({unrest})! {structures_destroyed} "
                                    f"structures have been destroyed by the rioters.")

                ################ OCCUPATION UPDATING ################

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
                        # do complicated maths
                        troops_unrest = p['troops'] / -100
                        tax_unrest = math.ceil(10 * (1 + 1) ** ((tax_rate / 5) - 1))
                        military_upkeep_unrest = -round(
                            (1 * (1 + 1) ** (military_upkeep / 5.75 - 1)) + ((1 * (1 + 1) ** (
                                    military_upkeep / 10 - 1)) * 0.75))
                        if public_services < 15:
                            public_service_unrest = round(30 - public_services * 2)
                        else:
                            public_service_unrest = -round((3 * (1 + 0.75) ** ((public_services - 23) / 5) - 1))
                        # add unrest and cap or floor
                        unrest += tax_unrest + public_service_unrest + military_upkeep_unrest + troops_unrest
                        if unrest > 100:
                            unrest = 100
                        elif unrest < 0:
                            unrest = 0
                        await conn.execute('''UPDATE provinces SET unrest = $1 WHERE id = $2;''', unrest, p)
                        # if the unrest is greater than 50, roll a d100-25 to see if they rebel
                        if unrest >= 50:
                            unrest_roll = randint(1, 100) - 25
                            if unrest_roll <= 75:
                                owner_info = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1,''',
                                                                 p['owner'])
                                await self.bot.loop.run_in_executor(None, self.map_color, p['id'], p['cord'],
                                                                    owner_info['usercolor'])
                                occupation_uprising.append(p['id'])
                # if the province rebels
                if occupation_uprising is True:
                    occupation_uprising_string = ', '.join(str(p) for p in occupation_uprising)
                    await user.send(f"The population of occupied province(s) {occupation_uprising_string} "
                                    f"have risen up due to high unrest ({unrest}) and have returned to their "
                                    f"core owner's control!")

                ################ RESOURCE AND MANPOWER UPDATING ################

                # subtract troop and structure maintenance costs
                credits_added -= total_troops * (0.01 * (modifiers['attack_level'] + modifiers['defense_level'])) * \
                                 modifiers['troop_upkeep_mod']
                credits_added -= structure_cost
                # calculate manpower increase and max manpower
                max_manpower_raw = await conn.fetchrow('''SELECT sum(manpower::int) FROM provinces WHERE
                              owner_id = $1 AND uprising = False;''', u)
                max_manpower = max_manpower_raw['sum']
                # if no provinces are owned, set to 3000
                if max_manpower is None:
                    max_manpower = 3000
                # calculate manpower gain (+1000 per city, +2500 for capital)
                added_manpower = (public_services / 100) * max_manpower * modifiers['manpower_mod']
                added_manpower += userinfo['citylimit'] * 1000
                if userinfo['capital'] != 0:
                    if userinfo['capital'] in provinces:
                        added_manpower += 2500
                # calculate all manpower and set ceiling
                manpower = added_manpower + userinfo['manpower'] + 3000
                if manpower > max_manpower:
                    manpower = max_manpower
                # calculates action points
                moves = 4
                # if less than 10 provinces, add no moves
                if len(provinces) <= 10:
                    moves += 0
                # if more than 10 provinces, add 1 move for every 10 provinces and add 10% for strategic focus
                elif len(provinces) > 10:
                    moves += math.floor((len(provinces) - 10) / 10)
                    if userinfo['focus'] == "s":
                        moves += math.floor(moves * .1)
                if userinfo['great_power']:
                    moves += 1
                # add all credits, manpower, moves to the user
                await conn.execute('''UPDATE cncusers SET resources = $1, manpower = $2, maxmanpower = $3, moves = $4,
                                   trade_route_limit = $5 WHERE user_id = $6;''',
                                   credits_added + userinfo['resources'], manpower, max_manpower, moves,
                                   trade_route_limit, u)

                ################ GREAT POWER UPDATING ################

                gp_points = 0
                # for every 100 credits earned, +1
                gp_points += credits_added * 0.01
                # for every army level, +1
                gp_points += modifiers['attack_level'] + modifiers['defense_level']
                # for every researched tech, +1
                gp_points += len(userinfo['researched'])
                # for every 1000 manpower, +1
                gp_points += manpower * 0.001
                # for every fort, city, port, workshop, and temple, +1
                gp_points += forts['count'] + cities['count'] + \
                             ports['count'] + workshops_n_temples
                # for every occupied 2 provinces, +1
                gp_points += occupied_count['count'] * 0.5
                alliances = await conn.fetchrow(
                    '''SELECT COUNT(*) FROM interactions WHERE (sender = $1 or recipient = $1) and type = 'alliance'
                    and active = True;''',
                    userinfo['username'])
                # for every 2 alliances, +1
                gp_points += alliances['count'] * 0.5
                # round to floor
                gp_points = math.floor(gp_points)
                # update great power score
                await conn.execute('''UPDATE cncusers SET great_power_score = $1 WHERE username = $2;''',
                                   gp_points, userinfo['username'])

                ################ EXIT USER UPDATING ################

            ################ GLOBAL UPDATING ################

            # set great powers
            await conn.execute('''UPDATE cncusers SET great_power = False;''')
            great_powers = await conn.fetch('''SELECT user_id, great_power_score FROM cncusers 
                          ORDER BY great_power_score DESC LIMIT 3;''')
            for gp in great_powers:
                if gp['great_power_score'] > 50:
                    userid = gp['user_id']
                    await conn.execute('''UPDATE cncusers SET great_power = True WHERE user_id = $1;''', userid)
            # update research turns and researched techs
            await conn.execute('''UPDATE cnc_researching SET turns = turns - 1;''')
            researched = await conn.fetch('''SELECT * FROM cnc_researching WHERE turns <= 0;''')
            for r in researched:
                await conn.execute('''UPDATE cncusers SET researched = researched || $1 WHERE user_id = $2;''',
                                   [str(r['tech'])], r['user_id'])
                user = self.bot.get_user(r['user_id'])
                userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', r['user_id'])
                await user.send(f"{userinfo['username']} has finished researching {r['tech']}.")
                await conn.execute('''DELETE FROM cnc_researching WHERE user_id = $1;''', r['user_id'])
                # updates modifiers
                tech = Technology(nation=userinfo['username'], techs=r['tech'], bot=self.bot)
                await tech.effects()
            # update turns
            turn = await conn.fetchrow('''SELECT data_value FROM cnc_data WHERE data_name = 'turn';''')
            await conn.execute('''UPDATE cnc_data SET data_value = data_value + 1 WHERE data_name = 'turn';''')
            # update user events
            await conn.execute('''UPDATE cncusers SET event_duration = event_duration - 1 WHERE event != '';''')
            await conn.execute('''UPDATE cncusers SET event = '', event_duration = 0 WHERE event_duration <= 0;''')
            # update global events and select if none is in effect
            await conn.execute('''UPDATE cnc_events SET turns = turns - 1 WHERE turns != 0;''')
            current_event = await conn.fetchrow('''SELECT * FROM cnc_events WHERE turns != 0;''')
            if current_event is None:
                random_global_event = await conn.fetchrow('''SELECT * FROM cnc_events 
                WHERE type = 'global' ORDER BY random();''')
                event = Events(bot=self.bot, event=random_global_event['name'])
                await event.global_effects()
                await conn.execute('''UPDATE cnc_events SET turns = $1 WHERE name = $2;''',
                                   random_global_event['duration'], random_global_event['name'])
            else:
                event = Events(bot=self.bot, event=current_event['name'], current=True)
                await event.global_effects()
            # send turn notification
            await cncchannel.send(f"New turn! It is now turn #{turn['data_value'] + 1}.")
            ################ EXIT GLOBAL UPDATING ################
        except Exception:
            self.bot.logger.warning(msg=traceback.format_exc())
            await crashchannel.send(content=f"```py\n{traceback.format_exc()}```")

    @commands.command()
    @commands.is_owner()
    async def cnc_force_turn(self, ctx):
        try:
            # channel to send to
            cncchannel = ctx.channel
            # connects to the database
            conn = self.bot.pool
            # fetches all the users and makes a list
            users = await conn.fetch('''SELECT user_id FROM cncusers;''')
            userids = [ids['user_id'] for ids in users]
            await conn.execute('''DELETE FROM cnc_modifiers;''')

            ################ USER UPDATING ################

            for u in userids:
                user = self.bot.get_user(u)
                credits_added = 0
                # pull out the data and get a list of provinces and trade routes
                userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', u)
                # establish manpower, tax rate, and tax income
                initial_manpower = userinfo['manpower']
                tax_rate = userinfo['taxation'] / 100
                taxes = initial_manpower * tax_rate
                # set military upkeep and public services rates and remove their amount from taxes
                military_upkeep = userinfo['military_upkeep'] / 100
                public_services = userinfo['public_services'] / 100
                taxes *= 1 - (military_upkeep + public_services)
                # add taxes
                credits_added += taxes
                # establish initial trade access
                initial_trade_access = 0.5
                # establish total troops, civil war, and provinces variables
                total_troops = 0
                civil_war = False
                provinces = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1;''', u)
                provinces_owned = [p['id'] for p in provinces]
                occupied_count = await conn.fetchrow('''SELECT count(*) FROM provinces WHERE occupier_id = $1;''', u)
                # set taxes, military upkeep, and public service rates to whole-number values
                tax_rate *= 100
                military_upkeep *= 100
                public_services *= 100

                ################ TECH MODIFIERS UPDATING ################

                # update tech modifiers
                await conn.execute('''INSERT INTO cnc_modifiers(user_id) VALUES($1);''', u)
                tech = Technology(userinfo['username'], techs=userinfo['researched'], bot=self.bot)
                await tech.effects()
                # fetch all tech modifiers
                modifiers = await conn.fetchrow('''SELECT * FROM cnc_modifiers WHERE user_id = $1;''', u)

                ################ EVENT UPDATING ################

                # check for event
                event_info = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1 and event != '';''', u)
                # if there is no event, pick event and run
                if event_info is None:
                    random_event = await conn.fetchrow('''SELECT * FROM cnc_events WHERE type = 'national' 
                    ORDER BY random();''')
                    event = Events(bot=self.bot, nation=userinfo['username'], event=random_event['name'])
                    await event.event_effects()
                # otherwise, update effects
                else:
                    event = Events(bot=self.bot, nation=userinfo['username'], event=event_info['event'], current=True)
                    await event.event_effects()

                ################ LIMIT UPDATING ################

                # fort/city/port/trade route limit update
                if len(provinces_owned) <= 5:
                    structure_cost = 0
                    cities = await conn.fetchrow(
                        '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND city = True;''',
                        userinfo['user_id'])
                    ports = await conn.fetchrow(
                        '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND port = True;''',
                        userinfo['user_id'])
                    forts = await conn.fetchrow(
                        '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND fort = True;''',
                        userinfo['user_id'])
                    if cities['count'] > 1:
                        structure_cost += 1000 * (cities['count'] - 1)
                    if ports['count'] > 1:
                        structure_cost += 500 * (ports['count'] - 1)
                    if forts['count'] > 1:
                        structure_cost += 700 * (forts['count'] - 1)
                    await conn.execute(
                        '''UPDATE cncusers SET citylimit = 1, portlimit = 1, fortlimit = 1 WHERE user_id = $1;''',
                        userinfo['user_id'])
                else:
                    # calculate limits
                    structure_cost = 0
                    fortlimit = math.floor((len(provinces_owned) - 5) / 5) + 1
                    portlimit = math.floor((len(provinces_owned) - 5) / 3) + 1
                    citylimit = math.floor((len(provinces_owned) - 5) / 7) + 1
                    if userinfo['focus'] == 's':
                        fortlimit += 1
                    if userinfo['focus'] == 'e':
                        portlimit += 1
                    cities = await conn.fetchrow(
                        '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND city = True;''',
                        userinfo['user_id'])
                    ports = await conn.fetchrow(
                        '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND port = True;''',
                        userinfo['user_id'])
                    forts = await conn.fetchrow(
                        '''SELECT count(*) FROM provinces WHERE owner_id = $1 AND fort = True;''',
                        userinfo['user_id'])
                    if cities['count'] > citylimit:
                        structure_cost += 1000 * (cities['count'] - citylimit)
                    if ports['count'] > portlimit:
                        structure_cost += 500 * (ports['count'] - portlimit)
                    if forts['count'] > fortlimit:
                        structure_cost += 700 * (forts['count'] - fortlimit)
                    await conn.execute(
                        '''UPDATE cncusers SET citylimit = $1, portlimit = $2, fortlimit = $3 WHERE user_id = $4;''',
                        citylimit, portlimit, fortlimit, userinfo['user_id'])
                # sets trade route limit
                trade_route_limit = 0
                # if the user is a great power, +1 trade route
                if userinfo['great_power']:
                    trade_route_limit += 1
                if userinfo['capital'] != 0:
                    trade_route_limit += 1
                # for every city +1 and for every two ports +1
                trade_route_limit += cities['count']
                trade_route_limit += math.floor(ports['count'] / 2)
                # if Banking and Investments is researched, add 1
                trade_route_limit += int(modifiers['trade_route'])
                # if the current trade route number is too high, reduce effective trade gain
                outgoing_count = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE type = 'trade' AND 
                              active = True AND sender_id = $1;''', userinfo['user_id'])
                outgoing_info = await conn.fetchrow('''SELECT * FROM interactions WHERE type = 'trade' AND 
                              active = True AND sender_id = $1;''', userinfo['user_id'])
                if outgoing_count['count'] is None:
                    outgoing_count = 0
                else:
                    outgoing_count = outgoing_count['count']
                incoming_count = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE type = 'trade' AND 
                                             active = True AND recipient_id = $1;''', userinfo['user_id'])
                if incoming_count['count'] is None:
                    incoming_count = 0
                else:
                    incoming_count = incoming_count['count']
                trade_debuff = 1
                if outgoing_count > trade_route_limit:
                    for i in range(trade_route_limit - outgoing_count):
                        trade_debuff -= .02
                # for every domestic trade route, +10% access. For every foreign trade route, +5% access
                if outgoing_info is not None:
                    outgoing_recipients = list()
                    for o in outgoing_info:
                        outgoing_recipients.append(o['recipient'])
                    outgoing_repeat = Counter(outgoing_recipients)
                    # for every repeat trade route, decrease by 2% down to 0%
                    for r in outgoing_repeat:
                        if r >= 6:
                            initial_trade_access = .3
                        else:
                            initial_trade_access += (10 - (r - 1) * r) / 100 * (
                                modifiers['trade_route_efficiency_mod'])
                # calculate initial trade access
                initial_trade_access += (.05 * incoming_count) * trade_debuff

                ################ NATIONAL UNREST UPDATING ################

                # check national Unrest for civil war and add national Unrest
                national_unrest = userinfo['national_unrest']
                # if the national unrest is above 80
                if len(provinces) > 9:
                    if national_unrest >= 80:
                        # roll a d100
                        unrest_roll = randint(0, 100)
                        # if the d100 is below or equal to the national unrest, trigger civil war
                        if unrest_roll <= national_unrest:
                            # fetch all provinces and get half
                            owned_provinces = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1 AND
                                          occupier_id = $1;''', user.id)
                            owned_provinces = [p['id'] for p in owned_provinces]
                            half_owned = math.floor(len(owned_provinces) / 2)
                            provinces_rebelling = sample(owned_provinces, half_owned)
                            # for all provinces rebelling, get their information
                            for pr in provinces_rebelling:
                                p_info = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', pr)
                                if p_info is None:
                                    continue
                                # add the remaining troops to the undeployed amount
                                undeployed = userinfo['undeployed']
                                troops_remaining = p_info['troops'] - (p_info['manpower'] * 2)
                                if troops_remaining <= 0:
                                    troops_remaining = 0
                                # update all information
                                await conn.execute('''UPDATE cncusers SET undeployed = $1 WHERE 
                                              user_id = $2;''', undeployed + troops_remaining, u)
                                await conn.execute('''UPDATE provinces SET occupier = '', occupier_id = 0, 
                                unrest = 0, troops = $1 WHERE id = $2;''', p_info['manpower'] * 2, pr)
                                await self.bot.loop.run_in_executor(None, self.occupy_color, pr, p_info['cord'][0:2],
                                                                    "#000000", userinfo['usercolor'])
                            provinces_rebelling.sort()
                            provinces_rebelling_string = ', '.join(str(e) for e in provinces_rebelling)
                            await user.send(f"Province(s) {provinces_rebelling_string} have rebelled in a civil war"
                                            f" due to high national unrest ({national_unrest})!")
                            civil_war = True
                # add national Unrest
                national_unrest = 0
                # do complicated maths to figure out the unrest rate
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
                # add national unrest suppression modifier
                public_service_unrest *= modifiers['national_unrest_suppression_efficiency_mod']
                # add unrest and cap or floor
                national_unrest += tax_unrest + public_service_unrest + military_upkeep_unrest
                if national_unrest > 100:
                    national_unrest = 100
                elif national_unrest < 0:
                    national_unrest = 0
                await conn.execute('''UPDATE cncusers SET national_unrest = $1 WHERE user_id = $2;''',
                                   national_unrest, u)

                ################ PROVINCE UPDATING ################

                provinces_rebelled = list()
                structures_destroyed = 0
                workshops_n_temples = 0
                # update all provinces
                for p in provinces_owned:
                    if p == 0:
                        continue
                    # fetch province info
                    p_info = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', p)
                    if p_info['uprising']:
                        # if the unrest is less than a random number between 1 and 100, end uprising
                        if p_info['unrest'] < randint(1, 100):
                            await conn.execute('''UPDATE provinces SET uprising = False WHERE id = $1;''', p)
                        # otherwise, continue uprising
                        else:
                            # calculate current unrest
                            unrest = 0
                            # reduce unrest for troops present
                            troops_unrest = p_info['troops'] / -100
                            if userinfo['great_power']:
                                troops_unrest *= 2
                            # add local unrest suppression efficiency mod
                            troops_unrest *= modifiers['local_unrest_suppression_efficiency_mod']
                            # do complicated maths
                            tax_unrest = math.ceil(10 * (1 + 1) ** ((tax_rate / 5) - 1))
                            military_upkeep_unrest = -round(
                                (1 * (1 + 1) ** (military_upkeep / 5.75 - 1)) + ((1 * (1 + 1) ** (
                                        military_upkeep / 10 - 1)) * 0.75))
                            if public_services < 15:
                                public_service_unrest = round(30 - public_services * 2)
                            else:
                                public_service_unrest = -round((3 * (1 + 0.75) ** ((public_services - 23) / 5) - 1))
                            # add unrest and cap or floor
                            unrest += tax_unrest + public_service_unrest + military_upkeep_unrest + troops_unrest
                            if unrest > 100:
                                unrest = 100
                            elif unrest < 0:
                                unrest = 0
                            await conn.execute('''UPDATE provinces SET unrest = $1 WHERE id = $2;''', unrest, p)
                            continue
                    total_troops += p_info['troops']

                    ################ PRODUCTION UPDATING ################

                    # define production value, producing amount, market value modifiers, and workshop production
                    production_value = 1
                    market_value_mod = 1
                    workshop_production = 0
                    # for every city, add .5 production
                    if p_info['city']:
                        production_value += 0.5
                    # for every port, add 25% market value to the local good, if it is not gold or silver
                    if p_info['port']:
                        if p_info['value'] not in ['Gold', 'Silver']:
                            market_value_mod += 0.25
                    # for every workshop, add 1 * the production modifier
                    if p_info['workshop']:
                        workshop_production += 1 * modifiers['workshop_production_mod']
                        workshops_n_temples += 1
                    # add all production to the base province production
                    producing = p_info['production'] * (production_value + modifiers['production_mod'])
                    # calculate local trade good value and total gain
                    trade_good = await conn.fetchrow('''SELECT * FROM trade_goods WHERE name = $1;''', p_info['value'])
                    credits_added += (((trade_good['market_value'] +
                                        modifiers[f'{self.space_replace(p_info["value"]).lower()}_mod']) *
                                       market_value_mod) * producing) * initial_trade_access

                    ################ LOCAL UNREST UPDATING ################

                    # check local Unrest for local uprising and add local Unrest
                    local_unrest = p_info['unrest']
                    # if the local Unrest is greater than 50
                    if len(provinces) > 4:
                        if local_unrest >= 50:
                            # roll a d100
                            unrest_roll = randint(0, 100)
                            # if the d100 is greater than the local Unrest, trigger an uprising
                            if unrest_roll <= local_unrest:
                                # if a city is present, 20% chance for destruction
                                if p_info['city']:
                                    if randint(1, 100) >= 80:
                                        structures_destroyed += 1
                                        await conn.execute('''UPDATE provinces SET city = False WHERE id = $1;''', p)
                                # if a fort is present, 10% chance for it to be destroyed
                                if p_info['fort']:
                                    if randint(1, 100) >= 90:
                                        structures_destroyed += 1
                                        await conn.execute('''UPDATE provinces SET fort = False WHERE id = $1;''', p)
                                # if a port is present 20% chance for it to be destroyed
                                if p_info['port']:
                                    if randint(1, 100) >= 80:
                                        structures_destroyed += 1
                                        await conn.execute('''UPDATE provinces SET port = False WHERE id = $1;''', p)
                                # calculate troops damage and update
                                troops_attacked = p_info['troops'] - \
                                                  (randint((p_info['manpower']) / 2, p_info['manpower']))
                                if troops_attacked < 0:
                                    troops_attacked = 0
                                await conn.execute('''UPDATE provinces SET uprising = True, troops = $2
                                              WHERE id = $1;''', p, troops_attacked)
                                provinces_rebelled.append(p)
                    # add Unrest
                    unrest = 0
                    # if there is a civil war ongoing, -20 unrest
                    if civil_war:
                        unrest -= 20
                    # do complicated maths
                    troops_unrest = p_info['troops'] / -100
                    tax_unrest = math.ceil(10 * (1 + 1) ** ((tax_rate / 5) - 1))
                    military_upkeep_unrest = -round((1 * (1 + 1) ** (military_upkeep / 5.75 - 1)) + ((1 * (1 + 1) ** (
                            military_upkeep / 10 - 1)) * 0.75))
                    if public_services < 15:
                        public_service_unrest = round(30 - public_services * 2)
                    else:
                        public_service_unrest = -round((3 * (1 + 0.75) ** ((public_services - 23) / 5) - 1))
                    # add unrest and cap or floor
                    unrest += tax_unrest + public_service_unrest + military_upkeep_unrest + troops_unrest
                    # if there is a temple, reduce to 85%
                    if p_info['temple']:
                        unrest *= 0.85
                        workshops_n_temples += 1
                    if unrest > 100:
                        unrest = 100
                    elif unrest < 0:
                        unrest = 0
                    # update unrest in province
                    await conn.execute('''UPDATE provinces SET unrest = $1 WHERE id = $2;''', unrest, p)
                    ################ EXIT PROVINCE UPDATING ################

                # if there are uprising provinces
                if len(provinces_rebelled) != 0:
                    provinces_rebelled_string = ', '.join(str(p) for p in provinces_rebelled)
                    await user.send(f"The population of province(s) {provinces_rebelled_string} "
                                    f"have risen up due to high unrest ({unrest})! {structures_destroyed} "
                                    f"structures have been destroyed by the rioters.")

                ################ OCCUPATION UPDATING ################

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
                        # do complicated maths
                        troops_unrest = p['troops'] / -100
                        tax_unrest = math.ceil(10 * (1 + 1) ** ((tax_rate / 5) - 1))
                        military_upkeep_unrest = -round(
                            (1 * (1 + 1) ** (military_upkeep / 5.75 - 1)) + ((1 * (1 + 1) ** (
                                    military_upkeep / 10 - 1)) * 0.75))
                        if public_services < 15:
                            public_service_unrest = round(30 - public_services * 2)
                        else:
                            public_service_unrest = -round((3 * (1 + 0.75) ** ((public_services - 23) / 5) - 1))
                        # add unrest and cap or floor
                        unrest += tax_unrest + public_service_unrest + military_upkeep_unrest + troops_unrest
                        if unrest > 100:
                            unrest = 100
                        elif unrest < 0:
                            unrest = 0
                        await conn.execute('''UPDATE provinces SET unrest = $1 WHERE id = $2;''', unrest, p)
                        # if the unrest is greater than 50, roll a d100-25 to see if they rebel
                        if unrest >= 50:
                            unrest_roll = randint(1, 100) - 25
                            if unrest_roll <= 75:
                                owner_info = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1,''',
                                                                 p['owner'])
                                await self.bot.loop.run_in_executor(None, self.map_color, p['id'], p['cord'],
                                                                    owner_info['usercolor'])
                                occupation_uprising.append(p['id'])
                # if the province rebels
                if occupation_uprising is True:
                    occupation_uprising_string = ', '.join(str(p) for p in occupation_uprising)
                    await user.send(f"The population of occupied province(s) {occupation_uprising_string} "
                                    f"have risen up due to high unrest ({unrest}) and have returned to their "
                                    f"core owner's control!")

                ################ RESOURCE AND MANPOWER UPDATING ################

                # subtract troop and structure maintenance costs
                credits_added -= total_troops * (0.01 * (modifiers['attack_level'] + modifiers['defense_level'])) * \
                                 modifiers['troop_upkeep_mod']
                credits_added -= structure_cost
                # calculate manpower increase and max manpower
                max_manpower_raw = await conn.fetchrow('''SELECT sum(manpower::int) FROM provinces WHERE
                              owner_id = $1 AND uprising = False;''', u)
                max_manpower = max_manpower_raw['sum']
                # if no provinces are owned, set to 3000
                if max_manpower is None:
                    max_manpower = 3000
                # calculate manpower gain (+1000 per city, +2500 for capital)
                added_manpower = (public_services / 100) * max_manpower * modifiers['manpower_mod']
                added_manpower += userinfo['citylimit'] * 1000
                if userinfo['capital'] != 0:
                    if userinfo['capital'] in provinces:
                        added_manpower += 2500
                # calculate all manpower and set ceiling
                manpower = added_manpower + userinfo['manpower'] + 3000
                if manpower > max_manpower:
                    manpower = max_manpower
                # calculates action points
                moves = 4
                # if less than 10 provinces, add no moves
                if len(provinces) <= 10:
                    moves += 0
                # if more than 10 provinces, add 1 move for every 10 provinces and add 10% for strategic focus
                elif len(provinces) > 10:
                    moves += math.floor((len(provinces) - 10) / 10)
                    if userinfo['focus'] == "s":
                        moves += math.floor(moves * .1)
                if userinfo['great_power']:
                    moves += 1
                # add all credits, manpower, moves to the user
                await conn.execute('''UPDATE cncusers SET resources = $1, manpower = $2, maxmanpower = $3, moves = $4,
                                   trade_route_limit = $5 WHERE user_id = $6;''',
                                   credits_added + userinfo['resources'], manpower, max_manpower, moves,
                                   trade_route_limit, u)

                ################ GREAT POWER UPDATING ################

                gp_points = 0
                # for every 100 credits earned, +1
                gp_points += credits_added * 0.01
                # for every army level, +1
                gp_points += modifiers['attack_level'] + modifiers['defense_level']
                # for every researched tech, +1
                gp_points += len(userinfo['researched'])
                # for every 1000 manpower, +1
                gp_points += manpower * 0.001
                # for every fort, city, port, workshop, and temple, +1
                gp_points += forts['count'] + cities['count'] + \
                             ports['count'] + workshops_n_temples
                # for every occupied 2 provinces, +1
                gp_points += occupied_count['count'] * 0.5
                alliances = await conn.fetchrow(
                    '''SELECT COUNT(*) FROM interactions WHERE (sender = $1 or recipient = $1) and type = 'alliance'
                    and active = True;''',
                    userinfo['username'])
                # for every 2 alliances, +1
                gp_points += alliances['count'] * 0.5
                # round to floor
                gp_points = math.floor(gp_points)
                # update great power score
                await conn.execute('''UPDATE cncusers SET great_power_score = $1 WHERE username = $2;''',
                                   gp_points, userinfo['username'])

                ################ EXIT USER UPDATING ################

            ################ GLOBAL UPDATING ################

            # set great powers
            await conn.execute('''UPDATE cncusers SET great_power = False;''')
            great_powers = await conn.fetch('''SELECT user_id, great_power_score FROM cncusers 
                          ORDER BY great_power_score DESC LIMIT 3;''')
            for gp in great_powers:
                if gp['great_power_score'] > 50:
                    userid = gp['user_id']
                    await conn.execute('''UPDATE cncusers SET great_power = True WHERE user_id = $1;''', userid)
            # update research turns and researched techs
            await conn.execute('''UPDATE cnc_researching SET turns = turns - 1;''')
            researched = await conn.fetch('''SELECT * FROM cnc_researching WHERE turns <= 0;''')
            for r in researched:
                await conn.execute('''UPDATE cncusers SET researched = researched || $1 WHERE user_id = $2;''',
                                   [str(r['tech'])], r['user_id'])
                user = self.bot.get_user(r['user_id'])
                userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', r['user_id'])
                await user.send(f"{userinfo['username']} has finished researching {r['tech']}.")
                await conn.execute('''DELETE FROM cnc_researching WHERE user_id = $1;''', r['user_id'])
                # updates modifiers
                tech = Technology(nation=userinfo['username'], techs=r['tech'], bot=self.bot)
                await tech.effects()
            # update turns
            turn = await conn.fetchrow('''SELECT data_value FROM cnc_data WHERE data_name = 'turn';''')
            await conn.execute('''UPDATE cnc_data SET data_value = data_value + 1 WHERE data_name = 'turn';''')
            # update user events
            await conn.execute('''UPDATE cncusers SET event_duration = event_duration - 1 WHERE event != '';''')
            await conn.execute('''UPDATE cncusers SET event = '', event_duration = 0 WHERE event_duration <= 0;''')
            # update global events and select if none is in effect
            await conn.execute('''UPDATE cnc_events SET turns = turns - 1 WHERE turns != 0;''')
            current_event = await conn.fetchrow('''SELECT * FROM cnc_events WHERE turns != 0;''')
            if current_event is None:
                random_global_event = await conn.fetchrow('''SELECT * FROM cnc_events 
                WHERE type = 'global' ORDER BY random();''')
                event = Events(bot=self.bot, event=random_global_event['name'])
                await event.global_effects()
                await conn.execute('''UPDATE cnc_events SET turns = $1 WHERE name = $2;''',
                                   random_global_event['duration'], random_global_event['name'])
            else:
                event = Events(bot=self.bot, event=current_event['name'], current=True)
                await event.global_effects()
            # send turn notification
            await cncchannel.send(f"New turn! It is now turn #{turn['data_value'] + 1}.")
            ################ EXIT GLOBAL UPDATING ################
        except Exception:
            self.bot.logger.warning(msg=traceback.format_exc())
            await ctx.send(content=f"```py\n{traceback.format_exc()}```")
        ################ EXIT GLOBAL UPDATING ################

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
                await shardchannel.send(f"Turn loop waiting until {update.strftime('%a, %d %b %Y at %H:%M:%S %Z%z')}.")
                await discord.utils.sleep_until(update)
            # if the hour is less than 0600 but greater than 0600
            elif now.time() < datetime.time(hour=6):
                update = now.replace(hour=6, minute=0, second=0)
                await shardchannel.send(f"Turn loop waiting until {update.strftime('%a, %d %b %Y at %H:%M:%S %Z%z')}.")
                await discord.utils.sleep_until(update)
            # if the hour is greater than 0600 but less than noon
            elif now.time() < datetime.time(hour=12):
                update = now.replace(hour=12, minute=0, second=0)
                await shardchannel.send(f"Turn loop waiting until {update.strftime('%a, %d %b %Y at %H:%M:%S %Z%z')}.")
                await discord.utils.sleep_until(update)
            # if the hour is greater than noon but less than 1800
            elif now.time() < datetime.time(hour=18, minute=0):
                update = now.replace(hour=18, minute=0)
                await shardchannel.send(f"Turn loop waiting until {update.strftime('%a, %d %b %Y at %H:%M:%S %Z%z')}.")
                await discord.utils.sleep_until(update)
            # if the hour is greater than 1800 but less than midnight
            elif now.time() > datetime.time(hour=18, minute=0):
                update = now.replace(hour=0, minute=0, second=0)
                update += datetime.timedelta(days=1)
                await shardchannel.send(f"Turn loop waiting until {update.strftime('%a, %d %b %Y at %H:%M:%S %Z%z')}.")
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
