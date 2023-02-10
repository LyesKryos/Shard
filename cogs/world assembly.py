# Shard Verification 0.1b

import xml.etree.ElementTree as ET

from discord.ext import commands

from ShardBot import Shard
from ratelimiter import Ratelimiter


class WA(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot
        self.rate_limit = Ratelimiter()
        self.directory_variable = r"C:\Users\jaedo\OneDrive\Documents\GitHub\Shard\Dumps"

    async def region_dump(self):
        try:
            tree = ET.parse(f"{self.directory_variable}regions.xml")
            root = tree.getroot()
        except Exception as error:
            print(error)
            return
        conn = self.bot.pool
        for elm in root:
            if elm.tag == "REGION":
                for region in elm:
                    if region.tag == "NAME":
                        name = region.text
                    if region.tag == "DELEGATE":
                        delegate = region.text
                    if region.tag == "DELEGATEVOTES":
                        delendo = int(region.text)
                    if region.tag == "DELEGATEAUTH":
                        delauth = region.text
                    if region.tag == "NUMNATIONS":
                        numnations = int(region.text)
                    if region.tag == "FOUNDER":
                        founder = region.text
                    if region.tag == "FOUNDERAUTH":
                        if region.text is not None:
                            if region.text[0] == "X":
                                foundauth = "All"
                            else:
                                foundauth = region.text
                    if region.tag == "POWER":
                        power = region.text
                    if region.tag == "LASTUPDATE":
                        if region.text is None:
                            unix = 0
                        else:
                            unix = int(region.text)
                    if region.tag == "NATIONS":
                        if region.text is not None:
                            nations = list(region.text.split(":"))
                        else:
                            nations = ["None"]
                await conn.execute('''INSERT INTO region_dump VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10);''',
                                   name, delegate, delendo, delauth, numnations, founder, foundauth,
                                   power, unix, nations )


    async def nation_dump(self):
        pass


async def setup(bot: Shard):
    # define the cog and add the cog
    cog = WA(bot)
    await bot.add_cog(cog)
