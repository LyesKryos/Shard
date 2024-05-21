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


