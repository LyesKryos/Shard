# Shard WA Program v1.0a
import asyncio
import csv
import gzip
import logging
import re
import traceback
import xml.etree.ElementTree as ET
import requests
from discord.ext import commands
from time import perf_counter, strftime
from ShardBot import Shard
from customchecks import TooManyRequests
from ratelimiter import Ratelimiter


class WA(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot
        self.rate_limit = Ratelimiter()
        self.directory_variable = r'~/Documents/Shard/dumps/'
        self.channel = bot.get_channel(835579413625569322)
        self.rate_limit = Ratelimiter()

    def sanitize_raw(userinput: str) -> str:
        # replaces user input with proper, url-friendly code
        to_regex = userinput.replace("_", " ")
        return re.sub(r"[^a-zA-Z0-9_-]", ' ', to_regex)

    def sanitize(userinput: str) -> str:
        # replaces user input with proper, url-friendly code
        to_regex = userinput.replace(" ", "_")
        return re.sub(r"[^a-zA-Z0-9_-]", ' ', to_regex)

    async def region_dump(self, ctx):
        # start the time to count
        time_start = perf_counter()
        # establish the headers
        headers = {"User-Agent": "Bassiliya"}
        # fetch the region dump file from NS
        rdump = requests.get("https://www.nationstates.net/pages/regions.xml.gz", headers=headers, allow_redirects=True)
        # ratelimiter
        while True:
            # see if there are enough available calls. if so, break the loop
            try:
                await self.rate_limit.call()
                break
            # if there are not enough available calls, continue the loop
            except TooManyRequests as error:
                await asyncio.sleep(int(str(error)))
                continue
        # decompress gzip file
        decompressed = gzip.decompress(rdump.content)
        # open a new tile and replace the last line with the current date and time
        with open(fr"{self.directory_variable}regions.xml", "wb") as rx:
            rx.write(decompressed)
        with open(fr"{self.directory_variable}regions.xml", "a") as rx:
            rx.write(f"<!-- Update Time: {strftime('%Y-%m-%d %H:%M:%S')}-->")
        # connect to database
        conn = self.bot.pool
        # open the file with ET.iterparse, events being 'start' and 'end'
        iteration = ET.iterparse(
            rf"C{self.directory_variable}regions.xml",
            events=('start', 'end'))
        # count regions
        regions = 1
        # declare the list for each region
        items = list()
        # declare the whole list
        items_list = list()
        # for each event and tag in the iteration, parse out the data,
        # add it to the list, and then add the list to master
        for event, region in iteration:
            if event == 'end':
                if region.tag != "REGION":
                    if region.tag == "NAME":
                        items.append(region.text.strip())
                    if region.tag == "DELEGATE":
                        if region.text.strip() == "0":
                            delegate = "None"
                        else:
                            delegate = region.text.strip()
                        items.append(delegate)
                    if region.tag == "DELEGATEVOTES":
                        items.append(int(region.text.strip()))
                    if region.tag == "DELEGATEAUTH":
                        items.append(region.text)
                    if region.tag == "NUMNATIONS":
                        items.append(int(region.text.strip()))
                    if region.tag == "FOUNDER":
                        if region.text is None:
                            items.append("Founderless")
                        else:
                            items.append(region.text.strip())
                    if region.tag == "FOUNDERAUTH":
                        if region.text is not None:
                            if region.text == "XABCEP":
                                items.append("All")
                            else:
                                items.append(region.text.strip())
                        else:
                            items.append("Non-exec")
                    if region.tag == "POWER":
                        items.append(region.text.strip())
                    if region.tag == "NATIONS":
                        if region.text is not None:
                            items.append(set(region.text.split(":")))
                        else:
                            items.append({"None"})
                    if region.tag == "LASTUPDATE":
                        if region.text is None:
                            items.append(0)
                        else:
                            items.append(int(region.text.strip()))
                        # increase count
                        regions += 1
                        # append region data to master list and clear region data
                        items_list.append(items)
                        items = list()
                continue
        # open a csv file and write the master list to it
        with open(f'{self.directory_variable}region_dump.csv', 'w', newline='', encoding="UTF-8") as region_dump_csv:
            writer = csv.writer(region_dump_csv)
            writer.writerows(items_list)
        # clear the previous region_dump
        await conn.execute('''DELETE FROM region_dump;''')
        # open the csv file and mass-copy to that file
        await conn.execute(r'''copy region_dump FROM $1'region_dump.csv'
        WITH csv;''', self.directory_variable)
        # stop stopwatch
        time_end = perf_counter()
        return await self.channel.send(f"Parsed {regions} regions in {time_end - time_start}.")

    async def nation_dump(self, ctx):
        # start the time to count
        start_time = perf_counter()
        # establish the headers
        headers = {"User-Agent": "Bassiliya"}
        # fetch the region dump file from NS
        ndump = requests.get("https://www.nationstates.net/pages/nations.xml.gz", headers=headers, allow_redirects=True)
        # ratelimiter
        while True:
            # see if there are enough available calls. if so, break the loop
            try:
                await self.rate_limit.call()
                break
            # if there are not enough available calls, continue the loop
            except TooManyRequests as error:
                await asyncio.sleep(int(str(error)))
                continue
        # decompress gzip file
        decompressed = gzip.decompress(ndump.content)
        # open a new tile and replace the last line with the current date and time
        with open(fr"{self.directory_variable}nations.xml", "wb") as rx:
            rx.write(decompressed)
        with open(fr"{self.directory_variable}nations.xml", "a") as rx:
            rx.write(f"<!-- Update Time: {strftime('%Y-%m-%d %H:%M:%S')}-->")
        # connect to database
        conn = self.bot.pool
        # open the file with ET.iterparse, events being 'start' and 'end'
        iteration = ET.iterparse(
            fr"{self.directory_variable}nations.xml",
            events=('start', 'end'))
        # count nations
        nations = 1
        # declare the list for each region
        nation_items = list()
        # declare the whole list
        nation_items_list = list()
        # for each event and tag in the iteration, parse out the data, add it to the list, and then add the list to master
        for event, nation in iteration:
            if event == 'end':
                if nation.tag != "REGION":
                    if nation.tag == "NAME":
                        nation_items.append(nation.text.strip())
                    if nation.tag == "TYPE":
                        nation_items.append(nation.text.strip())
                    if nation.tag == "UNSTATUS":
                        status = nation.text.strip()
                        if status.lower() == "non-member":
                            nation_items.append(False)
                        else:
                            nation_items.append(True)
                    if nation.tag == "ENDORSEMENTS":
                        if nation.text is None:
                            nation_items.append({"None"})
                        else:
                            nation_items.append(set(nation.text.strip().split(",")))
                    if nation.tag == "REGION":
                        nation_items.append(nation.text.strip())
                    if nation.tag == "FLAG":
                        nation_items.append(nation.text.strip())
                    if nation.tag == "FIRSTLOGIN":
                        nation_items.append(nation.text.strip())
                    # DBID indicates the end of the nation's data
                    if nation.tag == "DBID":
                        # increase count
                        nations += 1
                        # append region data to master list and clear region data
                        nation_items_list.append(nation_items)
                        nation_items = list()
                continue
        # open a csv file and write the master list to it
        with open(f'{self.directory_variable}nation_dump.csv', 'w', newline='', encoding="UTF-8") as nation_dump_csv:
            writer = csv.writer(nation_dump_csv)
            writer.writerows(nation_items_list)
        # clear the previous region_dump
        await conn.execute('''DELETE FROM nation_dump;''')
        # open the csv file and mass-copy to that file
        await conn.execute(r'''copy nation_dump FROM 
        $1'nation_dump.csv' WITH csv;''', self.directory_variable)
        # stop stopwatch
        time_end = perf_counter()
        return await self.channel.send(f"Parsed {nations} nations in {time_end - start_time}.")

    @commands.command()
    async def run_dumps(self, ctx):
        async with ctx.typing():
            await self.nation_dump(ctx)
            await self.region_dump(ctx)

async def setup(bot: Shard):
    # define the cog and add the cog
    cog = WA(bot)
    await bot.add_cog(cog)
