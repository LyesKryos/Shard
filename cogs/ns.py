# dispatch cog v 1.4
import datetime
from io import BytesIO
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
                name = nation_info_soup.name.text
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
            img = Image.open(BytesIO(get_flag))
            rgb_color = self.get_dominant_color(img)
            flag_color = discord.Colour.from_rgb(rgb_color[0], rgb_color[1], rgb_color[2])
            creation_time = datetime.datetime.fromtimestamp(int(founded_epoch), tz=self.eastern)
            # create embed
            nation_embed = discord.Embed(title=f"{fullname}", colour=flag_color,
                                         url=f"https://www.nationstates.net/nation={name}")
            nation_embed.set_thumbnail(url=flag_link)
            nation_embed.add_field(name="Motto", value=f"{motto}")
            nation_embed.add_field(name="Classification", value=f"{category}")
            nation_embed.add_field(name="\u200b", value="\u200b")
            nation_embed.add_field(name="World Assembly", value=f"{wa} ({len(endos)} endorsements)")
            nation_embed.add_field(name="Influence", value=f"{influence} ({influence_score:,} points)")
            nation_embed.add_field(name="\u200b", value="\u200b")
            nation_embed.add_field(name="Region", value=f"[{region}]"
                                                        f"(https://www.nationstates.net/region="
                                                        f"{self.sanitize_links_underscore(region)})")
            nation_embed.add_field(name="Founded",
                                   value=f"{creation_time.strftime('%d %b %Y')} "
                                         f"({founded})")
            if int(population) >= 1000:
                population = f"{float(population) / 1000} billion {demonym}"
            else:
                population = f"{float(population)} million {demonym}"
            nation_embed.add_field(name="Population", value=population)
            await ctx.send(embed=nation_embed)
            return asyncio.sleep(1.8)

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


async def setup(bot):
    cog = NationStates(bot)
    await bot.add_cog(cog)
