# Shard Verification 0.1b
from ShardBot import Shard
import asyncio
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import re
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone

class Verification:

    def __init__(self, bot: Shard):
        self.bot = bot


    @commands.command(brief="Verifies a nation.")
    async def verify(self, ctx):
        # establishes connection
        conn = self.bot.pool
        # establishes author
        author = ctx.author
        # sends DM to initiate verification
        await author.send(f"**Welcome to the Thegye server, {author}!** \n\n"
                          f"This is your quick invitation to verify your NationStates nation. If your nation is "
                          f"currently residing in Thegye, you will be assigned the Thegye role. If your nation is"
                          f" not currently residing in Thegye, you will be assigned the Traveler role. "
                          f"If you do not verify any nation, you will be assigned the Unverified role and be unable"
                          f"to access the majority of the server.\n\n"
                          f"To begin the verification process, please enter your nation's **name**, "
                          f"without the pretitle. For example, if your nation appears as `The Holy Empire of Bassiliya`,"
                          f" please only type "
                          f""
                          f"")