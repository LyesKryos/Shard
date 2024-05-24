import random
from typing import Literal
from discord import app_commands
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
from discord.ui import View, Select

class OptionButton(View):

    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Back", emoji="\U000023ea", style=discord.ButtonStyle.blurple)
    async def back_button(self, interaction: discord.Interaction, left_button: discord.Button):
        await interaction.response.send_message("2")
        return 1

    @discord.ui.button(label="Forward", emoji="\U000023e9", style=discord.ButtonStyle.blurple)
    async def forward_button(self, interaction: discord.Interaction, left_button: discord.Button):
        await interaction.response.send_message("1")
        return 2



class CNC(commands.Cog):

    def __init__(self, bot: Shard):
        self.map_directory = r"/root/Documents/Shard/CNC/Map Files/Maps/"
        self.province_directory = r"/root/Documents/Shard/CNC/Map Files/Province Layers/"
        self.interaction_directory = r"/root/Documents/Shard/CNC/Interaction Files/"
        self.bot = bot
        self.turn_task = None
        self.banned_colors = ["#000000", "#ffffff", "#808080", "#0071BC", "#0084E2", "#2BA5E2"]
        self.version = "version 3.0 Golden Crowns"

    def cog_unload(self):
        # stop the running turnloop
        self.turn_loop.cancel()
        # cancel the running turn task
        self.turn_task.cancel()

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
                        if data != (255, 255, 255, 0):
                            prov.putpixel((x, y), color)
        # if this is a release, change every color to neutral grey
        if release is True:
            color = ImageColor.getrgb("#808080")
            for x in range(0, prov.size[0]):
                for y in range(0, prov.size[1]):
                    data = prov.getpixel((x, y))
                    if data != color:
                        if data != (0, 0, 0, 0):
                            if data != (255, 255, 255, 0):
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
                if pixel == (0, 0, 0, 0) or pixel == (255, 255, 255, 0):
                    not_colored.append((x, y))
                else:
                    prov.putpixel((x, y), owner)
        # draw lines every 20 pixels with the occupier color
        for x in range(0, 1000 * 2, space):
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

    # the CnC command group
    cnc = app_commands.Group(name="cnc", description="...")

    @cnc.command(name="register", description="Registers a new player nation.")
    @app_commands.guild_only()
    @app_commands.describe(nation_name="The name of your new nation.",
                           color="The hex code of your new nation. Include the '#'.")
    async def register(self, interaction: discord.Interaction, nation_name: str, color: str):
        # defer the interaction
        await interaction.response.defer(thinking=True, ephemeral=True)
        # establish connection
        conn = self.bot.pool
        # define user
        user = interaction.user
        # check if the user already exists
        check_call = await conn.fetchrow('''SELECT * FROM cnc_users WHERE user_id = $1;''', user.id)
        if check_call is not None:
            return await interaction.followup.response(
                f"You are already a registered player of the Command and Conquest system. "
                f"Your nation name is {check_call['name']}", ephemeral=True)
        # otherwise, continue with player registration
        else:
            # check if the color is taken, banned, or even a color
            check_color_taken = await conn.fetchrow('''SELECT * FROM cnc_users WHERE color = $1;''', color)
            if check_color_taken is not None:
                return await interaction.followup.send("That color is already taken. "
                                                       "Please register with a different color.")
            if color in self.banned_colors:
                return await interaction.followup.send("That color is a restricted color. "
                                                       "Please register with a different color.")
            # try and get the color from the hex code
            try:
                ImageColor.getrgb(color)
            except ValueError:
                return await interaction.followup.send(
                    "That doesn't appear to be a valid hex color code. Include the `#` symbol.")
            await conn.execute('''INSERT INTO cnc_users(user_id, name, color) VALUES ($1,$2,$3);''', user.id,
                               nation_name, color)


    @cnc.command(name="map", description="Opens the map for viewing.")
    @app_commands.guild_only()
    async def map(self, interaction: discord.Interaction):
        # defer the interaction
        await interaction.response.defer(thinking=True)
        # send the map
        map = await interaction.followup.send("https://i.ibb.co/6RtH47v/Terrain-with-Numbers-Map.png")
        button = OptionButton()
        msg = await interaction.followup.send("text", view=button)
        if button == 1:
            return await msg.edit(content="forward")
        elif button == 2:
            return await msg.edit(content="back")




async def setup(bot: Shard):
    # define the cog and add the cog
    cog = CNC(bot)
    await bot.add_cog(cog)

