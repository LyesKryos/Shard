# dispatch cog v 1.4
import datetime
import shelve
import typing
from io import BytesIO
from cairosvg import svg2png
import PIL
import aiohttp
import discord
from discord import app_commands
import xml.etree.ElementTree as ET
from ShardBot import Shard
import asyncio
from discord.ext import commands, tasks
from bs4 import BeautifulSoup
import re
from pytz import timezone
from PIL import Image
from ratelimiter import Ratelimiter
from customchecks import TooManyRequests


def parse_rmb_message(message: str) -> dict:
    # establish the dict of the data
    message_data = {"message": "", "quoted_nation": None, "quote_id": None, "quoted_message": None}
    # define the quote pattern
    quote_pattern = f"\\](.*){re.escape("[/quote]")}"
    # search for if there is a quote
    quote_match = re.search(quote_pattern, message, flags=re.DOTALL)
    # if there is a quote detected, parse out the information
    if quote_match:
        # define the quote content
        message_data["quoted_nation"] = quote_match.group(1)
        # parse the nation quoted and define it
        quoted_nation_pattern = f"{re.escape("[quote=")}(.*){re.escape(";")}"
        quoted_nation_match = re.search(quoted_nation_pattern, message)
        message_data["quoted_nation"] = quoted_nation_match.group(1)
        # parse the quote id and parse it
        quote_id_pattern = f"{quoted_nation_match.group(1)};(.*?){re.escape("]")}"
        quote_id_match = re.search(quote_id_pattern, message)
        message_data["quote_id"] = f"> {quote_id_match.group(1).replace("\n", "\n> ")}"
        # parse the quote content
        quote_content_pattern = re.escape("[quote=") + r'(.*)' + re.escape("[/quote]")
        # define the host message content of the quote
        host_message = re.sub(pattern=quote_content_pattern, string=message, repl="", flags=re.DOTALL)[1:]
        message_data["message"] = host_message
    # if there is not a quote, make the message data just the message itself
    else:
        message_data['message'] = message
    # send the message data back
    return message_data


class NationStates(commands.Cog):

    def __init__(self, bot: Shard):
        self.bot = bot
        self.eastern = timezone('US/Eastern')
        self.rate_limit = Ratelimiter()
        self.rmb_proxy.start()

    def cog_unload(self):
        self.rmb_proxy.cancel()

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

    async def get_nation(self, nation: str, data_only: bool = False):
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
                    return False
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
                svg_bytes = svg2png(url=flag_link)
                img = Image.frombytes(data=svg_bytes, mode="RGB", size=(30, 30))
                flag_link = flag_link.replace(".svg", ".png")
            rgb_color = self.get_dominant_color(img)
            flag_color = discord.Colour.from_rgb(rgb_color[0], rgb_color[1], rgb_color[2])
            creation_time = datetime.datetime.fromtimestamp(int(founded_epoch), tz=self.eastern)
            endos = len(endos.split(','))
            if wa == "Non-member":
                endos = 0
            if data_only:
                raw_data = {"name": name, "fullname": fullname, "motto": motto, "flag_link": flag_link, "flag_color": flag_color,
                            "category": category, "region": region, "endos": endos, "population": population,
                            "residency": residency, "demonym": demonym}
                return raw_data
            else:
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
                return nation_embed

    async def get_region(self, interaction: discord.Interaction, region):
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
                    return await interaction.followup.send("That region does not seem to exist.")
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
            await interaction.followup.send(embed=region_embed)

    @tasks.loop(minutes=1)
    async def rmb_proxy(self):
        crash_channel = self.bot.get_channel(835579413625569322)
        with shelve.open("rmb_post_id") as rmb_post_id:
            last_post_id = rmb_post_id['last_post_id']
        if last_post_id is None:
            last_post_id = 0
        post_buffer = {}
        try:
            # define session
            async with aiohttp.ClientSession() as rmb_session:
                # define user agent
                headers = {"User-Agent": "Bassiliya @Lies Kryos#1734 on Discord"}
                # define parameters
                params = {"region": "project_chaos",
                          "q": "messages"}
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
                # if the last post ID isn't defined, get the most recent post ID and use that as the post ID
                if last_post_id == 0:
                    # add limit 1 to the parameter
                    params.update({"limit": "1"})
                    # call the messages
                    async with rmb_session.get("https://www.nationstates.net/cgi-bin/api.cgi",
                                               headers=headers, params=params) as most_recent_message:
                        # parse data
                        message_raw = await most_recent_message.text()
                        try:
                            messages_root = ET.fromstring(message_raw)
                        except ET.ParseError as e:
                            self.bot.logger.error(f"Error parsing XML: {e}")
                            await crash_channel.send("RMB posting error. Check the logs.")
                        # pull all message information
                        post = messages_root.find(".//POST")
                        # pull post id and add it to the list of posts
                        last_post_id = post.get("id")
                        post_buffer.update({last_post_id: [post.find(".//NATION").text, post.find('.//MESSAGE').text]})
                        # set the last post id as the saved post id
                        with shelve.open("rmb_post_id") as rmb_post_id:
                            rmb_post_id['last_post_id'] = last_post_id
                else:
                    # pull all posts after the last post id
                    params.update({"fromid": str(last_post_id+1)})
                    # call the messages
                    async with rmb_session.get("https://www.nationstates.net/cgi-bin/api.cgi",
                                               headers=headers, params=params) as all_recent_messages:
                        # parse data
                        messages_raw = await all_recent_messages.text()
                        try:
                            messages_root = ET.fromstring(messages_raw)
                        except ET.ParseError as e:
                            self.bot.logger.error(f"Error parsing XML: {e}")
                            await crash_channel.send("RMB posting error. Check the logs.")
                        # pull all message information
                        posts = messages_root.findall(".//POST")
                        # add the information from each post to the post_buffer
                        for post in posts:
                            post_id = post.get("id")
                            nation = post.find(".//NATION").text
                            message = post.find(".//MESSAGE").text
                            # update dict
                            post_buffer.update({post_id: [nation, message]})
                # create and send embed for each post
                for post in post_buffer:
                    # get the key
                    post_id = [*post][0]
                    # get the nation and message, which are first and second in the list, respectively
                    nation = post_buffer[post_id][0]
                    message = post_buffer[post_id][1]
                    # pull nation info
                    nation_info = await self.get_nation(nation=nation, data_only=True)
                    # parse the message info
                    message_info = parse_rmb_message(message)
                    # create the embed object
                    post_embed = discord.Embed(title="posted")
                    post_embed.set_author(name=f"{nation}", url=f"https://www.nationstates.net/nation/{nation}",
                                          icon_url=f"{nation_info['flag_link']}")
                    # if the message has a quote, include the quote
                    if message_info['quoted_nation'] is not None:
                        post_embed.add_field(name="\u200B",
                                             value=f"[{message_info['quoted_nation']} wrote...] "
                                                   f"(https://www.nationstates.net/page=rmb/postid="
                                                   f"{message_info['quote_id']})\n"
                                                   f"{message_info['quoted_message']}\n\n"
                                                   f"{message_info['message']}")
                    else:
                        post_embed.add_field(name="\u200B", value=f"{message}")
                    post_embed.set_footer(text="Posted on the Thegye Regional Message Board",
                                            icon_url="https://i.ibb.co/YTVtf5q6/j-Fd-Wa-Fb-400x400.jpg")
                    await crash_channel.send(embed=post_embed)
        except Exception as error:
            self.bot.logger.error(f"Error: {error}")
            await crash_channel.send("RMB error. Check the logs.")


    ns = app_commands.Group(name="ns", description="...")

    @ns.command(name="nation", description="Displays information about a nation")
    @app_commands.describe(nation_name="The name of the nation you would like to search for.")
    async def nation(self, interaction: discord.Interaction, nation_name: typing.Optional[str]):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establishes connection
        conn = self.bot.pool
        # defines nation
        if nation_name is None:
            # fetches nation info
            main_nation = await conn.fetchrow('''SELECT * FROM verified_nations WHERE user_id = $1;''',
                                              interaction.user.id)
            # if there is no verified nation
            if main_nation['main_nation'] is None:
                return await interaction.followup.send("You have no main nation set.")
            # otherwise
            else:
                embed = await self.get_nation(main_nation['main_nation'])
                if embed is False:
                    return await interaction.followup.send(f"That nation does not seem to exist. "
                                                    f"You can check for CTEd nations in the Boneyard: "
                                                    f"https://www.nationstates.net/page=boneyard")
                return await interaction.followup.send(embed=embed)
        else:
            embed = await self.get_nation(nation_name)
            if embed is False:
                return await interaction.followup.send(f"That nation does not seem to exist. "
                                                       f"You can check for CTEd nations in the Boneyard: "
                                                       f"https://www.nationstates.net/page=boneyard")
            return await interaction.followup.send(embed=embed)

    @ns.command(description="Displays information about a region")
    @app_commands.describe(region_name="The name of the region you would like to search for")
    async def region(self, interaction: discord.Interaction, region_name: str):
        # defer interaction
        await interaction.response.defer(thinking=True)
        await self.get_region(interaction=interaction, region=region_name)

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
