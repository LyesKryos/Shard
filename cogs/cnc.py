from discord import app_commands
from ShardBot import Shard
import discord
from discord.ext import commands, tasks
import asyncio
from PIL import Image, ImageColor, ImageDraw
from base64 import b64encode
import requests
from discord.ui import View, Select
import math


def plus_minus(number: int) -> str:
    """Adds a plus and minus to a number, turning it into a string."""
    if not isinstance(number, int):
        raise TypeError
    if number >= 0:
        return str(f"+{number}")
    elif number < 0:
        return str(f"-{number}")


class MapButtons(View):

    def __init__(self, message: discord.InteractionMessage, author):
        # set the timeout to two minutes
        super().__init__(timeout=120)
        # define the original map message
        self.message = message
        self.author = author
        self.map_directory = r"/root/Shard/CNC/Map Files/Maps/"

    async def on_timeout(self) -> None:
        # for all buttons, disable
        for button in self.children:
            button.disabled = True
        # update the view so that the buttons are disabled
        await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction):
        # ensures that the person using the interaction is the original author
        return interaction.user.id == self.author.id

    def add_ids(self):
        # open map, open ids image, paste, and save
        bmap = Image.open(fr"{self.map_directory}wargame_provinces.png").convert("RGBA")
        ids = Image.open(fr"{self.map_directory}wargame numbers.png").convert("RGBA")
        bmap.paste(ids, box=(0, 0), mask=ids)
        bmap.save(fr"{self.map_directory}wargame_nations_map.png")

    @discord.ui.button(label="Main", emoji="\U0001f5fa", style=discord.ButtonStyle.blurple)
    async def main_map(self, interaction: discord.Interaction, main: discord.Button):
        # defer the interaction because otherwise stuff crashes
        await interaction.response.defer()
        # edit the original message with the numbers map
        await self.message.edit(content="https://i.ibb.co/6RtH47v/Terrain-with-Numbers-Map.png")

    @discord.ui.button(label="Terrain", emoji="\U000026f0", style=discord.ButtonStyle.blurple)
    async def terrain_map(self, interaction: discord.Interaction, terrain: discord.Button):
        # defer the interaction because otherwise stuff crashes
        await interaction.response.defer()
        await self.message.edit(content="https://i.ibb.co/DwvJ2zc/Terrain-Map.png")

    @discord.ui.button(label="Cartography", emoji="\U0001f4cc", style=discord.ButtonStyle.blurple)
    async def carto_map(self, interaction: discord.Interaction, carto: discord.Button):
        # defer the interaction because otherwise stuff crashes
        await interaction.response.defer()
        await self.message.edit(content="https://i.ibb.co/XDmDKn3/CNC-name-map.png")

    @discord.ui.button(label="Nations", emoji="\U0001f3f3", style=discord.ButtonStyle.blurple)
    async def nation_map(self, interaction: discord.Interaction, nation_map: discord.Button):
        # defer response
        await interaction.response.defer()
        # disable all buttons so people don't keep trying to hit it because IT TAKES A SECOND
        for button in self.children:
            button.disabled = True
        await self.message.edit(content="Loading...", view=self)
        # get the running loop, crucial to the map command running without the world ending
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.add_ids)
        # open the nations map from the directory in "reading-binary" mode
        with open(fr"{self.map_directory}wargame_nations_map.png", "rb") as preimg:
            # read the image using 64-bit encoding
            img = b64encode(preimg.read())
            # set the parameters for imgbb's API call
            params = {"key": "a64d9505a13854ff660980db67ee3596",
                      "name": "Nations Map",
                      "image": img,
                      "expiration": 86400}
            # upload the map to imgbb
            upload = await loop.run_in_executor(None, requests.post, "https://api.imgbb.com/1/upload",
                                                params)
            # get the response as a json string
            response = upload.json()
            # re-enable buttons
            for button in self.children:
                button.disabled = False
            # parse out the map url and then edit the message accordingly
            await self.message.edit(content=response["data"]["url"], view=self)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, close: discord.Button):
        # for all buttons, disable
        for button in self.children:
            button.disabled = True
        # update the view so all the buttons are disabled
        await interaction.response.edit_message(view=self)


class CNC(commands.Cog):

    def __init__(self, bot: Shard):
        self.map_directory = r"/root/Shard/CNC/Map Files/Maps/"
        self.province_directory = r"/root/Shard/CNC/Map Files/Province Layers/"
        self.interaction_directory = r"/root/Shard/CNC/Interaction Files/"
        self.tech_directory = r"/root/Shard/CNC/Tech Tree/"
        self.bot = bot
        self.banned_colors = ["#000000", "#ffffff", "#808080", "#0071BC", "#0084E2", "#2BA5E2", "#999999"]
        self.version = "version 4.0 New Horizons"
        self.version_notes = ""

    async def map_color(self, province: int, hexcode, release: bool = False):
        # establish connection
        conn = self.bot.pool
        # pull province information
        province_info = await conn.fetchrow('''SELECT * FROM cnc_provinces WHERE id = $1;''', province)
        province_cord = province_info['cord']
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

    async def occupy_color(self, province: int, occupy_color, owner_color):
        # establish connection
        conn = self.bot.pool
        # pull province information
        province_info = await conn.fetchrow('''SELECT * FROM cnc_provinces WHERE id = $1;''', province)
        province_cord = province_info['cord']
        # obtain the coordinate information
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

    async def locate_color(self, province: int, prov_cords):
        # define loop
        loop = self.bot.loop
        # fetch map and province
        map_image = Image.open(fr"{self.map_directory}wargame_blank_save.png").convert("RGBA")
        prov = Image.open(fr"{self.province_directory}{province}.png").convert("RGBA")
        # get color
        color = ImageColor.getrgb("#FF00DC")
        # obtain size and coordinate information
        width = prov.size[0]
        height = prov.size[1]
        cord = (prov_cords[0], prov_cords[1])
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
        map_image.paste(prov, box=cord, mask=prov)
        map_image.save(fr"{self.map_directory}highlight_map.png")

        with open(fr"{self.map_directory}highlight_map.png", "rb") as preimg:
            img = b64encode(preimg.read())
        params = {"key": "a64d9505a13854ff660980db67ee3596",
                  "image": img}
        await asyncio.sleep(1)
        upload = await loop.run_in_executor(None, requests.post, "https://api.imgbb.com/1/upload",
                                            params)
        response = upload.json()
        return response['data']['url']

    async def user_db_info(self, user_id: int):
        """Pulls user info from the database using Discord user ID."""
        # establish connection
        conn = self.bot.pool
        # pull the user data
        user_info = await conn.fetchrow('''SELECT * FROM cnc_users WHERE user_id = $1;''', user_id)
        return user_info

    async def nation_db_info(self, nation_name: str):
        """Pulls user info from the database using the nation name."""
        # estbalish connection
        conn = self.bot.pool
        # pull user information based on nation name
        user_info = await conn.fetchrow('''SELECT * FROM cnc_users WHERE LOWER(name) = $1;''', nation_name.lower())
        return user_info

    async def nation_provinces_db_sort(self, user_id: int):
        """Pulls info from the database about ALL of a user's provinces using Discord user ID.
        Returns a sorted list of provinces and the count of provinces."""
        # establish connection
        conn = self.bot.pool
        # pull territory information
        provinces = await conn.fetch('''SELECT id FROM cnc_provinces WHERE owner_id = $1;''', user_id)
        # for every entry, pull out the ID
        provinces = [t['id'] for t in provinces]
        # count the number of entries
        province_count = len(provinces)
        # sort the provinces
        provinces.sort()
        # divide the list and deliniate with commas
        province_list = ', '.join(str(p) for p in provinces)
        return province_list, province_count

    async def nation_provinces_db_info(self, user_id: int):
        """Returns a database call of all provinces owned by the user indicated."""
        # establish connection
        conn = self.bot.pool
        # pull all the provinces info
        provinces = await conn.fetch('''SELECT * FROM cnc_provinces WHERE owner_id = $1;''', user_id)
        return provinces

    async def province_db_info(self, province_id: int = None, province_name: str = None):
        """Pulls info from the database about a particular province using province ID."""
        # establish connection
        conn = self.bot.pool
        # pull province information
        if province_id is not None:
            province = await conn.fetchrow('''SELECT * FROM cnc_provinces WHERE id = $1;''', province_id)
        elif province_name is not None:
            province = await conn.fetchrow('''SELECT * FROM cnc_provinces WHERE name = $1;''', province_name)
        else:
            raise TypeError
        return province

    async def terrain_name(self, terrain_id: int) -> str:
        # define connection
        conn = self.bot.pool
        terrain_name = await conn.fetchrow('''SELECT name FROM cnc_terrains WHERE id = $1;''', terrain_id)
        return str(terrain_name['name'])

    # the CnC command group
    cnc = app_commands.Group(name="cnc", description="...")

    # === User Commands and View Commands === #

    @cnc.command(name="register", description="Registers a new player nation.")
    @app_commands.guild_only()
    @app_commands.describe(nation_name="The name of your new nation.",
                           color="The hex code of your new nation. Include the '#'.")
    async def register(self, interaction: discord.Interaction, nation_name: str, color: str):
        # defer the interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # define user
        user = interaction.user
        # check if the user already exists
        check_call = await self.user_db_info(user.id)
        if check_call is not None:
            return await interaction.followup.send(
                f"You are already a registered player of the Command and Conquest system. "
                f"Your nation name is {check_call['name']}.", ephemeral=True)
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
                # if the color isn't a real hex code, return that they need to get the right hex code
                return await interaction.followup.send(
                    "That doesn't appear to be a valid hex color code. Include the `#` symbol.")
            # insert the new player into the user database
            await conn.execute('''INSERT INTO cnc_users(user_id, name, color) VALUES ($1,$2,$3);''', user.id,
                               nation_name.title(), color)
            # select the starting province
            # the starting province cannot be on one of the few islands do prevent impossible starts
            # the starting province cannot be owned by any player
            # (and since unowned provinces cannot be occupied, that too)
            starting_province = await conn.fetchrow('''SELECT * FROM cnc_provinces 
            WHERE owner_id = 0 and id NOT IN (130, 441, 442, 621, 622, 623, 65, 486, 215, 923, 926, 924, 
            925, 771, 772,770, 769, 768, 909, 761, 762, 763, 764, 765, 766, 767, 1207,
            1208, 1209, 1210, 1211, 1212, 1213, 1214, 744) ORDER BY random();''')
            # update the provinces database to set the player as the new owner and occupier
            await conn.execute('''UPDATE cnc_provinces SET owner_id = $1, occupier_id = $1 WHERE id = $2;''',
                               user.id, starting_province['id'])
            # color the map using the province coordinates and the ID
            await self.map_color(starting_province['id'], color)
            # create an army of 3,000 troops in the starting province
            await conn.execute('''INSERT INTO cnc_armies(owner_id, troops, location, army_name) 
            VALUES ($1, $2, $3, $4);''', user.id, 3000, starting_province['id'], f"Army of {starting_province['name']}")
            # send welcome message
            await interaction.followup.send(f"Welcome to the Command and Conquest System, {user.mention}!\n\n"
                                            f"Your nation, {nation_name.title()}, has risen from the mists of history "
                                            f"to make a name for itself in the annals of time. Will your people prove "
                                            f"they are masters of warfare? Will your merchants dominate the global "
                                            f"market, earning untold wealth? Will your scientists unlock the mysteries "
                                            f"of the world? Will your people flourish under your hand or cower under "
                                            f"your iron fist? Only the future can tell.\n\n"
                                            f"To get started, be sure to check out the "
                                            f"[**Command and Conquest Manual**]"
                                            f"(<https://1drv.ms/w/s!AtjcebV95AZNgWR1RbfSyx_0ln31?e=tD0eHa>). This "
                                            f"document has all the information you need to get started, a new players' "
                                            f"guide, and an overview of all commands.\n\n"
                                            f"**\"I came, I saw, I conquered.\" -Julius Caesar**")
            return

    @cnc.command(name="map", description="Opens the map for viewing.")
    @app_commands.guild_only()
    async def map(self, interaction: discord.Interaction):
        # defer the interaction
        await interaction.response.defer(thinking=True)
        # send the map
        map = await interaction.followup.send("https://i.ibb.co/6RtH47v/Terrain-with-Numbers-Map.png")
        map_buttons = MapButtons(map, author=interaction.user)
        await map.edit(view=map_buttons)

    @cnc.command(name="locate_province", description="Highlights a province on the map.")
    @app_commands.describe(province="The ID of the province to locate.")
    @app_commands.guild_only()
    async def locate_province(self, interaction: discord.Interaction, province: int):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # gather province info
        prov_info = await self.province_db_info(province)
        # if the province doesn't exist
        if prov_info is None:
            # return error message
            return await interaction.followup.send("No such province.")
        cords = prov_info['cord']
        url = await self.locate_color(province, cords)
        return await interaction.followup.send(url)

    @cnc.command(name="nation", description="Displays nation information for specified nation or player.")
    @app_commands.guild_only()
    @app_commands.describe(nation="The name of the nation you wish to query.", user="The user you wish to query.")
    async def nation(self, interaction: discord.Interaction, user: discord.Member = None, nation: str = None):
        # if neither argument is submitted, return error message
        if (nation is None) and (user is None):
            return await interaction.response.send_message("This command requires at least one input.", ephemeral=True)
        # if both are submitted, return error message
        if (nation is not None) and (user is not None):
            return await interaction.response.send_message("This command can take only one argument.", ephemeral=True)
        # defer the interaction
        await interaction.response.defer(thinking=True)
        # if the nation is called
        if nation is not None:
            # pull info from nation name
            user_info = await self.nation_db_info(nation.title())
            if user_info is None:
                return await interaction.followup.send(f"`{nation.title()}` not found.", ephemeral=True)
        elif user is not None:
            user_info = await self.user_db_info(user.id)
            if user_info is None:
                return await interaction.followup.send(f"That user is not a registered player of the CNC system.",
                                                       ephemeral=True)
        else:
            return
        # define connection
        conn = self.bot.pool
        # pull province data
        province_list, province_count = await self.nation_provinces_db_sort(user_info['user_id'])
        # pull the name of the capital
        capital = await conn.fetchrow('''SELECT * FROM cnc_provinces WHERE id = $1;''', user_info['capital'])
        if capital is None:
            capital = "None"
        else:
            capital = capital['name']
        # pull relations information
        alliances = await conn.fetch('''SELECT * FROM cnc_diplomacy WHERE $1 = ANY(members) AND type = 'alliance';''',
                                     user_info['name'])
        wars = await conn.fetch('''SELECT * FROM cnc_diplomacy WHERE $1 = ANY(members) AND type = 'wars';''',
                                user_info['name'])
        trade_pacts = await conn.fetch('''SELECT * FROM cnc_diplomacy WHERE $1 = ANY(members) AND type = 'trade';''',
                                       user_info['name'])
        military_access = await conn.fetch('''SELECT * FROM cnc_diplomacy 
        WHERE $1 = ANY(members) AND type = 'access';''', user_info['name'])

        def parse_relations(relations):
            if not relations:
                output = "None"
                return output
            else:
                output = ""
                for relation in relations:
                    buffer_output = ", ".join([r for r in relation['members'] if r != user_info['name']])
                    output += buffer_output
                return output

        allies = parse_relations(alliances)
        wars = parse_relations(wars)
        trade_pacts = parse_relations(trade_pacts)
        military_access = parse_relations(military_access)
        # build embed, populate title with pretitle and nation name, set color to user color,
        # and set description to Discord user.
        user_embed = discord.Embed(title=f"The {user_info['pretitle']} of {user_info['name']}",
                                   color=discord.Color(int(user_info["color"].lstrip('#'), 16), ),
                                   description=f"Registered nation of "
                                               f"{(self.bot.get_user(user_info['user_id'])).mention}.")
        # populate government type and subtype
        user_embed.add_field(name="Government", value=f"{user_info['govt_subtype']} {user_info['govt_type']}")
        # populate territory and count
        user_embed.add_field(name=f"Territory (Total: {province_count})", value=f"{province_list}")
        # populate capital
        user_embed.add_field(name="Capital", value=f"{capital}")
        # populate all three types of authority
        user_embed.add_field(name="Political Authority", value=f"{user_info['pol_auth']}")
        user_embed.add_field(name="Military Authority", value=f"{user_info['mil_auth']}")
        user_embed.add_field(name="Economic Authority", value=f"{user_info['econ_auth']}")
        # populate stability
        user_embed.add_field(name="Stability", value=f"{user_info['stability']}")
        # populate all four types of relations
        user_embed.add_field(name="Allies", value=f"{allies}")
        user_embed.add_field(name="Wars", value=f"{wars}")
        user_embed.add_field(name="Trade Pacts", value=f"{trade_pacts}")
        user_embed.add_field(name="Military Access", value=f"{military_access}")
        # send the embed
        return await interaction.followup.send(embed=user_embed)

    @cnc.command(name="dossier", description="Displays detailed information about your nation.")
    @app_commands.describe(direct_message="Optional: select True to send a private DM.")
    async def dossier(self, interaction: discord.Interaction, direct_message: bool = None):
        # defer interaction
        await interaction.response.defer(thinking=True, ephemeral=True)
        # establish connection
        conn = self.bot.pool
        # fetch user information
        user_id = interaction.user.id
        user_info = await self.user_db_info(user_id)
        # if the user does not exist
        if user_info is None:
            # return error message
            return await interaction.followup.send("You are not a registered member of the CNC system.")
        # pull province data
        province_list = await self.nation_provinces_db_info(user_id)
        province_list = [p['id'] for p in province_list]
        province_count = len(province_list)
        province_list = ", ".join(str(p) for p in province_list)
        # pull troop and army data
        troops = await conn.fetchrow('''SELECT SUM(troops) FROM cnc_armies WHERE owner_id = $1;''', user_id)
        armies = await conn.fetchrow('''SELECT COUNT(*) FROM cnc_armies WHERE owner_id = $1;''', user_id)
        generals = await conn.fetchrow('''SELECT COUNT(*) FROM cnc_generals WHERE owner_id = $1;''', user_id)
        total_manpower = await conn.fetchrow('''SELECT SUM(citizens) FROM cnc_provinces WHERE owner_id = $1;''',
                                             user_id)
        # build embed, populate title with pretitle and nation name, set color to user color,
        # and set description to Discord user.
        user_embed = discord.Embed(title=f"The {user_info['pretitle']} of {user_info['name']}",
                                   color=discord.Color(int(user_info["color"].lstrip('#'), 16), ),
                                   description=f"Registered nation of "
                                               f"{(self.bot.get_user(user_info['user_id'])).mention}.")
        # populate government type and subtype
        user_embed.add_field(name="Government", value=f"{user_info['govt_subtype']} {user_info['govt_type']}")
        # populate territory and count on its own line
        user_embed.add_field(name=f"Territory (Total: {province_count})", value=f"{province_list}", inline=False)
        # populate authority and gains
        user_embed.add_field(name="Political Authority (Change Last Turn)",
                             value=f"{user_info['pol_auth']} ({plus_minus(user_info['last_pol_auth_gain'])})")
        user_embed.add_field(name="Military Authority (Change Last Turn)",
                             value=f"{user_info['mil_auth']} ({plus_minus(user_info['last_mil_auth_gain'])})")
        user_embed.add_field(name="Economic Authority (Change Last Turn)",
                             value=f"{user_info['econ_auth']} ({plus_minus(user_info['last_econ_auth_gain'])})")
        # populate troops and armies
        user_embed.add_field(name="Troops", value=f"{troops['sum']:,}")
        user_embed.add_field(name="Armies", value=f"{armies['count']}")
        user_embed.add_field(name="Generals", value=f"{generals['count']}")
        # populate manpower
        user_embed.add_field(name="Manpower \n(Manpower Access)", value=f"{user_info['manpower']:,} "
                                                                        f"({user_info['manpower_access']}%)")
        user_embed.add_field(name="Manpower Regen",
                             value=f"{math.floor(total_manpower['sum'] * (user_info['manpower_regen'] / 100))} "
                                   f"({user_info['manpower_regen']}%)")
        user_embed.add_field(name="Total Manpower", value=f"{total_manpower['sum']:,}")
        # populate tax and spending stats
        user_embed.add_field(name="Taxation Level", value=f"{user_info['tax_level']}%")
        user_embed.add_field(name="Public Spending Cost",
                             value=f"{user_info['public_spend']} Economic Authority per turn")
        user_embed.add_field(name="Military Upkeep Cost",
                             value=f"{user_info['mil_upkeep']} Economic Authority per turn")
        # populate unrest, stability, overextension
        user_embed.add_field(name="National Unrest", value=f"{user_info['unrest']}")
        user_embed.add_field(name="Stability", value=f"{user_info['stability']}")
        user_embed.add_field(name="Overextension Limit", value=f"{user_info['overextend_limit']}")
        # populate overlord, if applicable
        if user_info['overlord']:
            user_embed.add_field(name="Overlord", value=f"{user_info['overlord']}")
        # send to direct message if required
        if direct_message is True:
            await interaction.followup.send("Sent you a DM!")
            return await interaction.user.send(embed=user_embed)
        else:
            return await interaction.followup.send(embed=user_embed)

    @cnc.command(name="strategic_view", description="Displays information about every province owned.")
    @app_commands.describe(direct_message="Optional: select True to send a private DM.")
    async def strategic_view(self, interaction: discord.Interaction, direct_message: bool = None):
        # defer interaction
        await interaction.response.defer(thinking=True, ephemeral=True)
        # pull user information
        user_id = interaction.user.id
        user_info = await self.user_db_info(user_id)
        # check if the user exists
        if user_info is None:
            return await interaction.followup.send("You are not a registered member of the CNC system.")
        # pull province information
        provinces = await self.nation_provinces_db_info(user_id)
        # creating the embed that the provinces will go into
        sv_embed = discord.Embed(title=f"Strategic View for {user_info['name']}",
                                 color=discord.Color(int(user_info["color"].lstrip('#'), 16)))
        # defining DM/ephemeral message
        if direct_message is True:
            message_source = interaction.user
        else:
            message_source = interaction.followup
        # defining the count and clear parameters
        count = 0
        if count >= 24:
            await message_source.send(embed=sv_embed)
            sv_embed.clear_fields()
            count = 0
        for p in provinces:
            sv_embed.add_field(name=f"{p['name']} ({p['id']})",
                               value=f"Terrain: {await self.terrain_name(p['terrain'])}\n"
                                     f"Citizens: {p['citizens']:,}\n"
                                     f"Trade Good: {p['trade_good']}\n"
                                     f"Production: {p['production']:,.3}\n"
                                     f"Structures: {p['structures']}\n"
                                     f"Fort Level: {p['fort_level']}")
            count += 1
        if count != 0:
            return await message_source.send(embed=sv_embed)
        else:
            return

    @cnc.command(name="province", description="Displays basic information about a province.")
    @app_commands.describe(province_id="The ID of the province.", province_name="The name of the province.")
    async def province(self, interaction: discord.Interaction, province_id: int = None, province_name: str = None):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # gather province information
        if (province_id is None) and (province_name is None):
            return await interaction.followup.send("This command requires at least one argument.")
        elif province_id is not None:
            prov_info = await self.province_db_info(province_id=province_id)
        elif province_name is not None:
            prov_info = await self.province_db_info(province_name=province_name)
        else:
            raise TypeError
        # if the province doesn't exist
        if prov_info is None:
            return await interaction.followup.send("That province does not appear to exist.")
        # owner and occupier info
        if prov_info['owner_id'] != 0:
            owner = await self.user_db_info(prov_info['owner_id'])
            owner = owner['name']
        else:
            owner = "Natives"
        if prov_info['occupier_id'] != 0:
            occupier = await self.user_db_info(prov_info['occupier_id'])
            occupier = occupier['name']
        else:
            occupier = "Natives"
        if prov_info['river'] is True:
            river = ", River"
        else:
            river = ""
        # troops and armies
        troop_count = await conn.fetchrow('''SELECT SUM(troops) FROM cnc_armies WHERE location = $1;''',
                                          prov_info['id'])
        # parse out troop count
        if troop_count['sum'] is None:
            troop_count = 0
        else:
            troop_count = f"{troop_count['sum']:,}"
        army_list = await conn.fetch('''SELECT * FROM cnc_armies WHERE location = $1''', prov_info['id'])
        # parse out army list
        if army_list is None:
            army_list = "None"
        else:
            army_list = ", ".join(a['name'] for a in army_list)
        # build embed for province and populate name and ID
        prov_embed = discord.Embed(title=f"Province of {prov_info['name']}", description=f"Province #{prov_info['id']}",
                                   color=discord.Color.red())
        # populate bordering
        prov_embed.add_field(name="Bordering Provinces",
                             value=f"{', '.join([str(b) for b in prov_info['bordering']])}",
                             inline=False)
        prov_embed.add_field(name="Core Owner", value=owner)
        prov_embed.add_field(name="Occupier", value=occupier)
        prov_embed.add_field(name="Troops and Armies", value=f"{troop_count} troops "
                                                             f"in {army_list} armies.")
        prov_embed.add_field(name="Terrain", value=f"{await self.terrain_name(prov_info['terrain'])}"+river)
        prov_embed.add_field(name="Trade Good", value=f"{prov_info['trade_good']}")
        prov_embed.add_field(name="Citizens", value=f"{prov_info['citizens']:,}")
        prov_embed.add_field(name="Production", value=f"{prov_info['production']:,.3}")
        return await interaction.followup.send(embed=prov_embed)

    # === Tech Commands === #

    @cnc.command(name="tech", description="Displays information about a specified technology.")
    @app_commands.guild_only()
    @app_commands.describe(tech="The tech to search.")
    async def tech(self, interaction: discord.Interaction, tech: str):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # pull the tech data
        tech = await conn.fetchrow('''SELECT * FROM cnc_tech WHERE lower(name) = $1;''', tech.lower())
        # if the tech doesn't exist
        if tech is None:
            # return the error message
            return await interaction.followup.send("No such technology found.")
        # create tech embed
        tech_embed = discord.Embed(title=f"{tech['name']}", description=f"{tech['description']}")
        tech_embed.set_thumbnail(url=f"{tech['image']}")
        tech_embed.add_field(name="Effect", value=f"{tech['effect']}")
        tech_embed.add_field(name="Prerequisites", value=f"{', '.join([str(p) for p in tech['prereqs']])}")
        tech_embed.add_field(name="Exclusive with", value=f"{tech['exclusive']}")
        return await interaction.followup.send(embed=tech_embed)

    @cnc.command(name="view_tech_tree", description="Displays researched techs.")
    @app_commands.guild_only()
    async def view_tech_tree(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # pull user's tech
        techs = await conn.fetchrow('''SELECT tech FROM cnc_users WHERE user_id = $1;''', interaction.user.id)
        # parse tech
        techs = techs['tech']
        # map techs
        tech_map = Image.open(fr"{self.tech_directory}CNC Tech Tree.png").convert('RGBA')
        gear_icon = Image.open(fr"{self.tech_directory}CNC Gear Tech Icon.png").convert('RGBA')
        # pull tech info
        for tech in techs:
            tech_info = await conn.fetchrow('''SELECT * FROM cnc_tech WHERE name = $1;''', tech)
            gear_cords = tech_info['gear_cords']
            await interaction.followup.send(gear_cords)
            tech_map.paste(gear_icon, (int(gear_cords[0]/3.778), int(gear_cords[1]/3.778)) , mask=gear_icon)
        # save image
        tech_map.save(fr"{self.tech_directory}CNC Tech Map Rendered.png", optimize=True, quality=53)
        # upload image
        await interaction.followup.send(file=discord.File(fr"{self.tech_directory}CNC Tech Map Rendered.png"))

    @cnc.command(name="research", description="Begins researching a specified tech.")
    @app_commands.guild_only()
    @app_commands.describe(tech="The tech to research.")
    async def research(self, interaction: discord.Interaction, tech: str):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # pull user info
        user_id = interaction.user.id
        user_info = await self.user_db_info(user_id=user_id)
        # if the user does not exist
        if user_info is None:
            # return a message
            return await interaction.followup.send("You are not a registered member of the CNC system.")
        # check if that tech is an existing tech
        tech_info = await conn.fetchrow('''SELECT * FROM cnc_tech WHERE lower(name) = $1;''', tech.lower())
        # if it is not an existing tech
        if tech_info is None:
            # return denial
            return await interaction.followup.send("That is not a recognized tech.")
        # pull techs
        techs = user_info['tech']
        # check if the requested tech is already researched
        if tech.lower() in [t.lower() for t in techs]:
            # return denial
            return await interaction.followup.send("That tech has already been researched.")
        # check if a tech is already being researched
        researching_tech = await conn.fetchrow('''SELECT * FROM cnc_researching WHERE user_id = $1;''', user_id)
        if researching_tech is not None:
            # return denial
            return await interaction.followup.send("A tech is already being researched.")
        # if the tech is not yet unlocked and another tech is not already being researched, add the tech to the research queue
        # determine research time
        # set base research time as four turns
        research_time = 4
        # pull development score
        total_dev = await conn.fetchrow('''SELECT sum(development) FROM cnc_provinces WHERE owner_id = $1;''', user_id)
        total_dev = total_dev['sum']
        # pull research time
        research_buff = user_info['research_time']
        # calculate total research time
        research_time += (total_dev//10) + research_buff
        # add to researching database
        await conn.execute('''INSERT INTO cnc_researching VALUES($1,$2,$3);''',
                           user_id, tech_info['name'], research_time)
        # send confirmation message and research time
        return await interaction.followup.send(f"{tech_info['name']} will be researched in {research_time} turns.\n"
                                        f"||Research Time = {total_dev//10} (development) +"
                                        f" {research_buff} (national research time) + 4 (base research time)||")

    @cnc.command(name="researching", description="Displays which tech is being researched.")
    @app_commands.guild_only()
    async def researching(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # check if the user exists
        user_id = interaction.user.id
        user_info = await self.user_db_info(user_id)
        # if the user doesn't exist
        if user_info is None:
            # return denial
            return await interaction.followup.send("You are not a registered member of the CNC system.")
        # pull researching information
        researching = await conn.fetchrow('''SELECT * FROM cnc_researching WHERE user_id = $1;''', user_id)
        # if there is no tech being researched currently
        if researching is None:
            # return message
            return await interaction.followup.send("No tech is being researched currently.")
        # if there is a tech being researched, send the info
        if researching is not None:
            # return info
            return await interaction.followup.send(f"Scientists are currently researching the {researching['tech']} "
                                                   f"tech. Research will be complete in {researching['turns']} turns.")

    @cnc.command(name="cancel_research", description="Cancels the tech currently being researchined.")
    @app_commands.guild_only()
    async def cancel_research(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # check if the user exist
        user_id = interaction.user.id
        user_info = await self.user_db_info(user_id)
        # if the user doesn't exist
        if user_info is None:
            # return denial
            return await interaction.followup.send("You are not a registered member of the CNC system.")
        # pull researching information
        researching = await conn.fetchrow('''SELECT * FROM cnc_researching WHERE user_id = $1;''', user_id)
        # if there is no tech being researched currently
        if researching is None:
            # return message
            return await interaction.followup.send("No tech is being researched currently.")
        # cancel the research currently underway
        if researching is not None:
            # send cancel to db
            await conn.execute('''DELETE FROM cnc_researching WHERE user_id = $1;''', user_id)
            return await interaction.followup.send(f"Scientists are no longer researching {researching['tech']}.")







    @commands.command()
    @commands.is_owner()
    async def cnc_reset_map(self, ctx):
        map_image = Image.open(fr"{self.map_directory}wargame_blank_save.png").convert("RGBA")
        map_image.save(fr"{self.map_directory}wargame_provinces.png")
        await ctx.send("Map reset.")

    @commands.command()
    @commands.is_owner()
    async def permanent_delete_user(self, ctx, user_id: int):
        # sent a confirmation message
        delete_confirm = await ctx.send(f"Are you certain you would like to delete {self.bot.get_user(user_id).name} "
                                        f"from the Command and Conquest System?")

        # wait for a confirmation message
        def confirmation_check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji)

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30, check=confirmation_check)
            if str(reaction.emoji) != "\U00002705":
                return await ctx.send("Must confirm deletion with: \U00002705")
        except asyncio.TimeoutError:
            return await delete_confirm.edit(content=f"Permanent deletion of {self.bot.get_user(user_id).name} "
                                                     f"from the Command and Conquest System aborted.")
        conn = self.bot.pool
        user = await conn.fetchrow('''SELECT * FROM cnc_users WHERE user_id = $1;''', user_id)
        if user is None:
            return await ctx.send("No such user in the CNC system.")
        await conn.execute('''DELETE FROM cnc_users WHERE user_id = $1;''', user_id)
        await conn.execute('''DELETE FROM cnc_armies WHERE owner_id = $1;''', user_id)
        await conn.execute('''UPDATE cnc_provinces SET owner_id = 0, occupier_id = 0 
        WHERE owner_id = $1 AND occupier_id = $1;''', user_id)
        await conn.execute('''DELETE FROM cnc_researching WHERE user_id = $1;''', user_id)
        await delete_confirm.delete()
        return await ctx.send(f"Permanent deletion of {self.bot.get_user(user_id).name} "
                              "from the Command and Conquest System completed.")


async def setup(bot: Shard):
    # define the cog and add the cog
    cog = CNC(bot)
    await bot.add_cog(cog)
