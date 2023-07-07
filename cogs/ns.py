# dispatch cog v 1.4
import datetime
from io import BytesIO
from cairosvg import svg2png
import PIL
import aiohttp
import discord
from ShardBot import Shard
import asyncio
from discord.ext import commands
from bs4 import BeautifulSoup
import re
from pytz import timezone
from PIL import Image
from ratelimiter import Ratelimiter
from customchecks import TooManyRequests


class NationStates(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot
        self.eastern = timezone('US/Eastern')
        self.rate_limit = Ratelimiter()

    def get_dominant_color(self, pil_img, palette_size=16):
        # Resize image to speed up processing
        img = pil_img.copy()
        img.thumbnail((100, 100))
        # Reduce colors (uses k-means internally)
        paletted = img.convert('P', palette=Image.ADAPTIVE, colors=palette_size)
        # Find the color that occurs most often
        palette = paletted.getpalette()
        color_counts = sorted(paletted.getcolors(), reverse=True)
        palette_index = color_counts[0][1]
        dominant_color = palette[palette_index * 3:palette_index * 3 + 3]
        return tuple(dominant_color)

    def sanitize_links_underscore(self, userinput: str) -> str:
        # replaces user input with proper, url-friendly code
        to_regex = userinput.replace(" ", "_")
        return re.sub(r"[^a-zA-Z0-9_-]", ' ', to_regex)

    async def get_nation(self, ctx, nation):
        async with aiohttp.ClientSession() as nation_session:
            headers = {'User-Agent': 'Bassiliya'}
            params = {'nation': nation}
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
            # get data
            async with nation_session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                          headers=headers, params=params) as nation_info:
                # if the nation does not exist
                if nation_info.status == 404:
                    return await ctx.send(f"That nation does not seem to exist. "
                                          f"You can check for CTEd nations in the Boneyard: "
                                          f"https://www.nationstates.net/page=boneyard")
                # parse data
                nation_info_raw = await nation_info.text()
                nation_info_soup = BeautifulSoup(nation_info_raw, 'lxml')
                fullname = nation_info_soup.fullname.text
                name = nation_info_soup.find('name').text
                motto = nation_info_soup.motto.text
                category = nation_info_soup.category.text
                wa = nation_info_soup.unstatus.text
                endos = nation_info_soup.endorsements.text
                region = nation_info_soup.region.text
                founded = nation_info_soup.founded.text
                founded_epoch = nation_info_soup.firstlogin.text
                population = nation_info_soup.population.text
                influence = nation_info_soup.influence.text
                demonym = nation_info_soup.demonym2plural.text
                flag_link = nation_info_soup.flag.text
            # parameters for census scores
            number_params = {'nation': nation,
                             'q': 'census',
                             'mode': 'score',
                             'scale': '80+65'}
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
            # get data
            async with nation_session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                          headers=headers, params=number_params) as number_info:
                # parse data
                nation_soup = await number_info.text()
                nation_soup = BeautifulSoup(nation_soup, 'lxml')
                # get scores
                influence_score, residency = [round(float(score.text))
                                              for score in nation_soup.census.find_all("score")]
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
            # get data
            async with nation_session.get(f"{flag_link}",
                                          headers=headers) as flag:
                # parse data
                get_flag = await flag.read()
            try:
                img = Image.open(BytesIO(get_flag))
            except PIL.UnidentifiedImageError:
                bytes = svg2png(url=flag_link)
                await ctx.send(bytes)
                # img = Image.frombytes(data=bytes)
            rgb_color = self.get_dominant_color(img)
            flag_color = discord.Colour.from_rgb(rgb_color[0], rgb_color[1], rgb_color[2])
            creation_time = datetime.datetime.fromtimestamp(int(founded_epoch), tz=self.eastern)
            endos = len(endos.split(','))
            if wa == "Non-member":
                endos = 0
            # create embed
            nation_embed = discord.Embed(description=f"*{motto}*", color=flag_color)
            nation_embed.set_thumbnail(url=flag_link)
            nation_embed.set_author(name=f"{fullname}", url=f"https://www.nationstates.net/nation="
                                                            f"{self.sanitize_links_underscore(name)}")
            nation_embed.add_field(name="Classification", value=f"{category}")
            nation_embed.add_field(name="\u200b", value="\u200b")
            nation_embed.add_field(name="World Assembly", value=f"{wa}\n({endos} endorsements)")
            nation_embed.add_field(name="Influence", value=f"{influence}\n({influence_score:,} points)")
            nation_embed.add_field(name="\u200b", value="\u200b")
            nation_embed.add_field(name="Region", value=f"[{region}]"
                                                        f"(https://www.nationstates.net/region="
                                                        f"{self.sanitize_links_underscore(region)})\n"
                                                        f"({residency} days ago)")
            nation_embed.add_field(name="Founded",
                                   value=f"{creation_time.strftime('%d %b %Y')}\n"
                                         f"({founded})")
            nation_embed.add_field(name="\u200b", value="\u200b")
            if int(population) >= 1000:
                population = f"{float(population) / 1000} billion {demonym}"
            else:
                population = f"{float(population)} million {demonym}"
            nation_embed.add_field(name="Population", value=population)
            await ctx.send(embed=nation_embed)

    async def get_region(self, ctx, region):
        async with aiohttp.ClientSession() as nation_session:
            headers = {'User-Agent': 'Bassiliya'}
            params = {'region': region,
                      'q': 'name+numnations+founder+foundedtime+power+flag+delegate+delegatevotes+lastupdate'}
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
            # get data
            async with nation_session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                          headers=headers, params=params) as region_data:
                # if the nation does not exist
                if region_data.status == 404:
                    return await ctx.send("That region does not seem to exist.")
                # parse data
                region_data_raw = await region_data.text()
                region_info = BeautifulSoup(region_data_raw, 'lxml')
                region_name = region_info.find('name').text
                residents = region_info.numnations.text
                delegate = region_info.delegate.text
                del_endos = region_info.delegatevotes.text
                founder = region_info.founder.text
                founded = region_info.foundedtime.text
                influence_level = region_info.power.text
                flag_link = region_info.flag.text
                update = region_info.lastupdate.text
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
            # get data
            async with nation_session.get(f"{flag_link}",
                                          headers=headers) as flag:
                # parse data
                get_flag = await flag.read()
            img = Image.open(BytesIO(get_flag))
            rgb_color = self.get_dominant_color(img)
            flag_color = discord.Colour.from_rgb(rgb_color[0], rgb_color[1], rgb_color[2])
            creation_time = datetime.datetime.fromtimestamp(int(founded), tz=self.eastern)
            # create embed
            region_embed = discord.Embed(color=flag_color)
            region_embed.set_thumbnail(url=flag_link)
            region_embed.set_author(name=f"{region_name}", url=f"https://www.nationstates.net/region="
                                                               f"{self.sanitize_links_underscore(region_name)}")
            region_embed.add_field(name="Founder", value=f"[{founder.title()}](https://www.nationstates.net/nation="
                                                         f"{self.sanitize_links_underscore(founder)})")
            region_embed.add_field(name="\u200b", value="\u200b")
            region_embed.add_field(name="Founded",
                                   value=f"{creation_time.strftime('%d %b %Y')}\n"
                                         f"(<t:{founded}:R>)")
            region_embed.add_field(name="Nations", value=f"{residents} nations", inline=False)
            region_embed.add_field(name="WA Delegate", value=f"[{delegate.title()}]"
                                                             f"(https://www.nationstates.net/nation="
                                                             f"{self.sanitize_links_underscore(delegate)})"
                                                             f"\n({del_endos} votes)")
            region_embed.add_field(name="\u200b", value="\u200b")
            region_embed.add_field(name="Influence", value=f"{influence_level}")
            region_embed.add_field(name="Last Update", value=f"<t:{update}:T>", inline=False)
            await ctx.send(embed=region_embed)

    @commands.command(brief="Displays information about a nation", aliases=['n'])
    async def nation(self, ctx, *, args=None):
        # establishes connection
        conn = self.bot.pool
        # defines nation
        if args is None:
            # fetches nation info
            main_nation = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''', ctx.author.id)
            # if there is no verified nation
            if main_nation['main_nation'] is None:
                raise commands.UserInputError
            # otherwise
            else:
                await self.get_nation(ctx, main_nation['main_nation'])
        else:
            await self.get_nation(ctx, args)

    @commands.command(brief="Displays information about a region", aliases=['r'])
    async def region(self, ctx, *, args):
        await self.get_region(ctx, args)

    @commands.command(brief="Displays the NS telegram queue", aliases=['tgq'])
    async def telegram_queue(self, ctx):
        async with aiohttp.ClientSession() as tgq_session:
            headers = {'User-Agent': 'Bassiliya'}
            params = {'q': 'tgqueue'}
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
            async with tgq_session.get('https://www.nationstates.net/cgi-bin/api.cgi?',
                                       headers=headers, params=params) as tgq:
                if tgq.status != 200:
                    await ctx.send("NationStates error. Please wait and try again later.")
                    return
                else:
                    tgq_raw = await tgq.text()
                    tgq = BeautifulSoup(tgq_raw, 'lxml')
                    manual = tgq.manual.text
                    stamps = tgq.mass.text
                    api = tgq.api.text
                    return await ctx.send("__Telegram Queue__\n"
                                          f"Manual: {int(manual):,}\n"
                                          f"Stamps: {int(stamps):,}\n"
                                          f"API: {int(api):,}")


async def setup(bot):
    cog = NationStates(bot)
    await bot.add_cog(cog)
