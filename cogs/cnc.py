from __future__ import annotations
from random import randrange, randint
import asyncpg
from discord import app_commands, Interaction
from discord._types import ClientT
from ShardBot import Shard
import discord
from discord.ext import commands, tasks
import asyncio
from PIL import Image, ImageColor, ImageDraw
from base64 import b64encode
import requests
from discord.ui import View
import math


async def safe_dm(bot: discord.Client, user_id: int, *, content: str | None = None,
                  embed: discord.Embed | None = None, view: discord.ui.View | None = None,
                  fallback_channel_id: int = 927288304301387816) -> bool:
    """Attempt to DM a user. On failure, warn them in a public fallback channel.
    Returns True if DM sent, False otherwise.
    """
    try:
        user = bot.get_user(user_id) or await bot.fetch_user(user_id)
    except Exception:
        user = None
    if user is None:
        # cannot resolve user; warn in fallback
        channel = bot.get_channel(fallback_channel_id)
        if channel:
            await channel.send(
                f"<@{user_id}>, I was unable to send you a DM (couldn't resolve your user). Please enable DMs and try again.")
        return False
    try:
        if embed is not None and content is not None:
            await user.send(content=content, embed=embed, view=view)
        elif embed is not None:
            await user.send(embed=embed, view=view)
        else:
            await user.send(content or "", view=view)
        return True
    except (discord.Forbidden, discord.HTTPException):
        channel = bot.get_channel(fallback_channel_id)
        if channel:
            await channel.send(
                f"<@{user_id}>, I was unable to send an important Command & Conquest notification to you! Be sure you permit DMs from me.")
        return False


def plus_minus(number: int) -> str:
    """Adds a plus and minus to a number, turning it into a string."""
    if number >= 0:
        return str(f"+{number}")
    elif number < 0:
        return str(f"-{number}")


def ordinal_suffix(number: int) -> str:
    """
    Adds an ordinal suffix to an integer, turning it into a string.
    """
    # set the number differentiation
    if 10 <= number % 100 <= 20:
        suffix = "nth"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


async def create_prov_embed(prov_info: asyncpg.Record, conn: asyncpg.Pool) -> discord.Embed:
    # owner and occupier info
    if prov_info['owner_id'] != 0:
        owner = await user_db_info(prov_info['owner_id'], conn)
        owner = owner['name']
    else:
        owner = "Natives"
    if prov_info['occupier_id'] != 0:
        occupier = await user_db_info(prov_info['occupier_id'], conn)
        occupier = occupier['name']
    else:
        occupier = "Natives"
    if prov_info['river'] is True:
        river = ", River"
    else:
        river = ""
    # troops and armies
    troop_count = await conn.fetchval('''SELECT SUM(troops)
                                         FROM cnc_armies
                                         WHERE location = $1;''',
                                      prov_info['id'])
    # parse out troop count
    if troop_count is None:
        troop_count = 0
    else:
        troop_count = f"{troop_count:,}"
    # parse structures
    if prov_info['structures'] is None:
        structures = "None"
    elif not prov_info['structures']:
        structures = "None"
    else:
        structures = ",".join(p for p in prov_info['structures'])
    army_count = await conn.fetchval('''SELECT COUNT(*)
                                        FROM cnc_armies
                                        WHERE location = $1''', prov_info['id'])
    # build embed for province and populate name and ID
    prov_embed = discord.Embed(title=f"Province of {prov_info['name']}",
                               description=f"Province #{prov_info['id']}",
                               color=discord.Color.red())
    # populate bordering
    prov_embed.add_field(name="Bordering Provinces",
                         value=f"{', '.join([str(b) for b in prov_info['bordering']])}",
                         inline=False)
    prov_embed.add_field(name="Core Owner", value=owner)
    prov_embed.add_field(name="Occupier", value=occupier)
    prov_embed.add_field(name="Troops and Armies", value=f"{troop_count} troops "
                                                         f"in {army_count} armies.")
    prov_embed.add_field(name="Terrain", value=f"{await terrain_name(prov_info['terrain'], conn)}" + river)
    prov_embed.add_field(name="Trade Good", value=f"{prov_info['trade_good']}")
    prov_embed.add_field(name="Citizens", value=f"{prov_info['citizens']:,}")
    prov_embed.add_field(name="Production\n(last turn)", value=f"{prov_info['production']:,.3}")
    prov_embed.add_field(name="Development", value=f"{prov_info['development']}")
    prov_embed.add_field(name="Structures", value=f"{structures}")
    return prov_embed


async def user_db_info(user_id: int | str, conn: asyncpg.Pool) -> asyncpg.Record:
    """Pulls user info from the database using Discord user ID."""
    # if the type is int, its a user id
    if type(user_id) == int:
        user_info = await conn.fetchrow('''SELECT *
                                           FROM cnc_users
                                           WHERE user_id = $1;''', user_id)
    # if the type is str, its a user nation name
    else:
        user_info = await conn.fetchrow('''SELECT *
                                           FROM cnc_users
                                           WHERE lower(name) = $1;''', user_id.lower())
    return user_info


async def terrain_name(terrain_id: int, conn: asyncpg.Pool) -> str:
    # make terrain db call
    terrain_name = await conn.fetchval('''SELECT name
                                          FROM cnc_terrains
                                          WHERE id = $1;''', terrain_id)
    # return name string
    return str(terrain_name)


async def map_color(province: int, hexcode: str, conn: asyncpg.Pool):
    map_directory = r"/root/Shard/CNC/Map Files/Maps/"
    province_directory = r"/root/Shard/CNC/Map Files/Province Layers/"
    # pull province information
    province_info = await conn.fetchrow('''SELECT *
                                           FROM cnc_provinces
                                           WHERE id = $1;''', province)
    province_cord = province_info['cord']
    # obtain the coordinate information
    province_cord = ((int(province_cord[0])), (int(province_cord[1])))
    # get color
    try:
        color = ImageColor.getrgb(hexcode)
    except ValueError:
        return ValueError("Hex code issue")
    # open the map and the province images
    map = Image.open(fr"{map_directory}wargame_provinces.png").convert("RGBA")
    prov = Image.open(fr"{province_directory}{province}.png").convert("RGBA")
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
    map.save(fr"{map_directory}wargame_provinces.png")


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


class Accept(View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=120)
        self.value = None
        self.interaction = interaction

    async def on_timeout(self):
        self.value = False
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.interaction.user.id

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    @discord.ui.button(label='Accept', style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Decline', style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()


# === Province Views ===

class ConstructDropdown(discord.ui.Select):

    def __init__(self, province_db: asyncpg.Record, user_info: asyncpg.Record, pool: asyncpg.Pool):
        self.prov_info = province_db
        self.pool = pool
        self.user_info = user_info

        # define options
        options = [
            discord.SelectOption(label='Farm'),
            discord.SelectOption(label='Trading Post'),
            discord.SelectOption(label='Lumber Mill'),
            discord.SelectOption(label='Mine'),
            discord.SelectOption(label='Fishery'),
            discord.SelectOption(label='City'),
            discord.SelectOption(label='Fort'),
            discord.SelectOption(label='Road'),
            discord.SelectOption(label='Manufactory'),
            discord.SelectOption(label='Port'),
            discord.SelectOption(label='Bridge'),
            discord.SelectOption(label='University'),
            discord.SelectOption(label='Temple')]
        # define the super
        super().__init__(placeholder="Choose a structure to build...", min_values=1, max_values=1, options=options)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.user_info['user_id']

    # set callback
    async def callback(self, interaction: discord.Interaction):
        structure = self.values[0]
        prov_info = self.prov_info
        user_info = self.user_info
        conn = self.pool
        # check if structure is already built
        if prov_info['structures'] is not None:
            if structure in prov_info['structures']:
                return await interaction.response.send_message(content=f"A {structure} already exists in "
                                                                       f"{prov_info['name']} (ID: {prov_info['id']}).")
        # check if the province has enough space
        development = prov_info['development']
        if prov_info['structures'] is not None:
            structures_num = len(prov_info['structures'])
        else:
            structures_num = 0
        # if the Engineering tech has been researched, increase building slots by 1
        if "Engineering" in user_info['tech']:
            structures_num -= 1
        # to build, the development of the province must be x>1 where x is defined as (development/10) - number of structures
        # accepting that each province can host a minimum of 1 structure
        if structures_num > 0:
            if (development / 10) - structures_num + 1 < 1:
                return await interaction.response.send_message(content=f"{prov_info['name']} is not developed "
                                                                       f"enough to support another structure.\n"
                                                                       f"The province will need an additional "
                                                                       f"{math.ceil(development - ((structures_num - 1) * 10))} to "
                                                                       f"build another structure.")
        # search for required tech
        req_tech = await conn.fetchrow('''SELECT *
                                          FROM cnc_tech
                                          WHERE effect = $1;''',
                                       f"Unlocks {structure} structure.")
        # if the user does not have the required tech
        if req_tech['name'] not in user_info['tech']:
            return await interaction.response.send_message(content=f"The **{req_tech['name']}** tech must be "
                                                                   f"researched before constructing a {structure}.")
        # check if the user has enough authority of that type to expend
        structure_info = await conn.fetchrow('''SELECT *
                                                FROM cnc_structures
                                                WHERE name = $1;''', structure)
        structure_cost = structure_info['cost']
        # GOVERNMENT AND TECH MODIFICATIONS
        # if the structure is a Fort
        if structure == "Fort":
            # if Siegeworks is researched, add 2 to the cost
            if "Siegeworks" in user_info['tech']:
                structure_cost += 2
            # if the government is absolute monarchy, reduce cost by 1
            if user_info['govt_subtype'] == "Absolute":
                structure_cost -= 1
        # if Machines is researched, subtract 1 from the cost, minimum 1
        if "Machines" in user_info['tech']:
            structure_cost -= 1
        # if the structure is a temple and the government subtype is Theocratic, reduce by 2
        if (structure == "Temples") and (user_info['govt_subtype'] == "Theocratic"):
            structure_cost -= 2
        # if the structure is a city and the government subtype is Patrician, reduce by 1
        if (structure == "City") and (user_info['govt_subtype'] == "Patrician"):
            structure_cost -= 2
        # if the structure is a port and the government subtype is Merchant, reduce by 1
        if (structure == "Port") and (user_info['govt_subtype'] == "Merchant"):
            structure_cost -= 1
        # if the structure is a port or a bridge and the government subtype is Populist, reduce by 50%
        if (structure == "Port" or structure == "Bridge") and (user_info['govt_subtype'] == "Populist"):
            structure_cost *= .5
        # structures must cost at least one power
        if structure_cost < 0:
            structure_cost = 1
        # if the user is Tusail, only use political authority
        if user_info['govt_type'] == "Tusail":
            if user_info['pol_auth'] < structure_cost:
                return await interaction.response.send_message(content="You do not have enough "
                                                                       "Political Authority to build that structure. You are lacking "
                                                                       f"{structure_cost - user_info['pol_auth']} authority.")
        # check if the user has enough military authority
        elif structure_info['authority'] == "Military":
            if user_info['mil_auth'] < structure_cost:
                return await interaction.response.send_message(content="You do not have enough "
                                                                       "Military Authority to build that structure. You are lacking "
                                                                       f"{structure_cost - user_info['mil_auth']} authority.")
        # check if the user has enough economic authority
        elif structure_info['authority'] == "Economic":
            if user_info['econ_auth'] < structure_cost:
                return await interaction.response.send_message(content="You do not have enough "
                                                                       "Economic Authority to build that structure. You are lacking "
                                                                       f"{structure_cost - user_info['econ_auth']} authority.")
        # check terrain requirements
        if structure_info['terrain'] is not None:
            if prov_info['terrain'] != structure_info['terrain']:
                return await interaction.response.send_message(content=f"You cannot build a {structure} in "
                                                                       f"{prov_info['name']}'s improper terrain.")
        # check unique requirements
        if structure == "Port":
            if prov_info['coast'] is False:
                return await interaction.response.send_message(content=f"You cannot build a {structure} in "
                                                                       f"{prov_info['name']}'s improper terrain.")
        if structure == "Bridge":
            if prov_info['river'] is False:
                return await interaction.response.send_message(content=f"You cannot build a {structure} in "
                                                                       f"{prov_info['name']}'s improper terrain.")
        if structure == "University":
            if "City" not in prov_info['structures']:
                return await interaction.response.send_message(content=f"You must construct a City in "
                                                                       f"{prov_info['name']} before constructing a "
                                                                       f"University.")
        # if the government type is Free City, only one city per nation allowed
        if (structure == "City") and (user_info['govt_subtype'] == "Free City"):
            provs_with_cities = await conn.fetchrow('''SELECT *
                                                       FROM cnc_provinces
                                                       WHERE owner_id = $1
                                                         AND 'City' = ANY (structures)''', interaction.user.id)
            if provs_with_cities is not None:
                return await interaction.response.send_message(content=f"Free Cities can construct only one City. "
                                                                       f"{user_info['name']} maintains City {provs_with_cities['name']}"
                                                                       f" (ID: {provs_with_cities['id']}).")
        # if all checks are met, construct and bill cost
        try:
            await conn.execute('''UPDATE cnc_provinces
                                  SET structures = structures || $1
                                  WHERE id = $2;''',
                               [structure], prov_info['id'])
            if structure_info['authority'] == "Military":
                await conn.execute('''UPDATE cnc_users
                                      SET mil_auth = mil_auth - $1
                                      WHERE user_id = $2;''',
                                   structure_info['cost'], interaction.user.id)
            elif structure_info['authority'] == "Economic":
                await conn.execute('''UPDATE cnc_users
                                      SET econ_auth = econ_auth - $1
                                      WHERE user_id = $2;''',
                                   structure_info['cost'], interaction.user.id)
            if structure == "Fort":
                await conn.execute('''UPDATE cnc_provinces
                                      SET fort_level = $1
                                      WHERE id = $2;''',
                                   user_info['fort_level'], prov_info['id'])
        except Exception as error:
            raise error
        return await interaction.response.send_message(content=f"{structure} successfully constructed in "
                                                               f"{prov_info['name']}.")


class ConstructView(View):
    def __init__(self, author, province_db: asyncpg.Record, user_info: asyncpg.Record, pool: asyncpg.Pool):
        super().__init__(timeout=120)
        self.author = author
        self.province_db = province_db
        self.user_info = user_info
        self.pool = pool
        # Adds the dropdown to our view object.
        self.add_item(ConstructDropdown(province_db, user_info, pool))
        # define OG view
        self.prov_owned_view = OwnedProvinceModifiation(author, province_db,
                                                        user_info, pool)

    async def on_timeout(self) -> None:
        # disable all the children
        for child in self.children:
            child.disabled = True
        # update the view
        await self.interaction.edit_original_response(view=self)

    async def interaction_check(self, interaction: discord.Interaction):
        # ensures that the person using the interaction is the original author
        return interaction.user.id == self.author.id

    @discord.ui.button(label="Back", emoji="\U000023ea", style=discord.ButtonStyle.blurple)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=OwnedProvinceModifiation(self.author, self.province_db,
                                                                              self.user_info, self.pool))

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)


class DeconstructDropdown(discord.ui.Select):

    def __init__(self, province_db: asyncpg.Record, user_info: asyncpg.Record, pool: asyncpg.Pool):
        self.prov_info = province_db
        self.pool = pool
        self.user_info = user_info

        # define options based on the existing structures
        options = []
        for structure in province_db['structures']:
            options.append(discord.SelectOption(label=structure))

        # define the super
        super().__init__(placeholder="Choose a structure to deconstruct...", min_values=1, max_values=1,
                         options=options)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.user_info['user_id']

    # define callback
    async def callback(self, interaction: discord.Interaction):
        # define constants
        structure = self.values[0]
        prov_info = self.prov_info
        province_id = prov_info['id']
        conn = self.pool
        # otherwise cary on
        # remove the structure from the province
        await conn.execute('''UPDATE cnc_provinces
                              SET structures = array_remove(structures, $1)
                              WHERE id = $2;''',
                           structure, province_id)
        return await interaction.response.send_message(f"The {structure} has been deconstructed in "
                                                       f"{prov_info['name']} (ID: {province_id}).")


class DeconstructView(View):
    def __init__(self, author, province_db: asyncpg.Record, user_info: asyncpg.Record, pool: asyncpg.Pool):
        super().__init__(timeout=120)
        self.author = author
        self.province_db = province_db
        self.user_info = user_info
        self.pool = pool
        # Adds the dropdown to our view object.
        self.add_item(DeconstructDropdown(province_db, user_info, pool))
        # define OG view
        self.prov_owned_view = OwnedProvinceModifiation(author, province_db,
                                                        user_info, pool)

    async def on_timeout(self) -> None:
        # disable all the children
        for child in self.children:
            child.disabled = True
        # update the view
        return await self.interaction.edit_original_response(view=self)

    async def interaction_check(self, interaction: discord.Interaction):
        # ensures that the person using the interaction is the original author
        return interaction.user.id == self.author.id

    @discord.ui.button(label="Back", emoji="\U000023ea", style=discord.ButtonStyle.blurple)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=OwnedProvinceModifiation(self.author, self.province_db,
                                                                              self.user_info, self.pool))

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)


class DevelopmentBoostView(View):
    def __init__(self, author, province_db: asyncpg.Record, user_info: asyncpg.Record, pool: asyncpg.Pool):
        super().__init__(timeout=120)
        self.author = author
        self.province_db = province_db
        self.user_info = user_info
        self.pool = pool
        self.authority_type = None
        # define OG view
        self.prov_owned_view = OwnedProvinceModifiation(author, province_db,
                                                        user_info, pool)

    async def interaction_check(self, interaction: discord.Interaction):
        # ensures that the person using the interaction is the original author
        return interaction.user.id == self.author.id

    async def on_timeout(self) -> None:
        # disable all the children
        for child in self.children:
            child.disabled = True
        # update the view
        return await self.interaction.edit_original_response(view=self, content=None)

    @discord.ui.button(label="Economic", style=discord.ButtonStyle.blurple)
    async def economic(self, interaction: discord.Interaction, button: discord.ui.Button):
        # define province variables
        prov_info = self.province_db
        user_info = self.user_info
        conn = self.pool
        province_id = prov_info['id']
        structures = [] if prov_info['structures'] is None else list(prov_info['structures'])
        # calculate dev boosting cost. base cost = current development * .75
        boost_cost = prov_info['development'] * .75
        # add modifiers from govt type
        govt_info = await conn.fetchrow('''SELECT *
                                           FROM cnc_govts
                                           WHERE govt_type = $1
                                             AND govt_subtype = $2;''',
                                        user_info['govt_type'], user_info['govt_subtype'])
        govt_mod = govt_info['dev_cost']
        boost_cost *= govt_mod
        # add modifiers from structures
        if "Lumber Mill" in structures:
            boost_cost *= .85
        # round boost cost up
        boost_cost = math.ceil(boost_cost)
        # check if user has sufficient authority
        if user_info['econ_auth'] < boost_cost:
            return await interaction.response.send_message(
                f"You do not have sufficient Economic authority to boost in this "
                f"province. You are missing {boost_cost - user_info['econ_auth']} "
                f"Economic authority.")
        # execute orders
        await conn.execute('''UPDATE cnc_users
                              SET econ_auth = econ_auth - $1
                              WHERE user_id = $2;''',
                           int(boost_cost), interaction.user.id)
        await conn.execute('''UPDATE cnc_provinces
                              SET development = development + 1
                              WHERE id = $1;''',
                           province_id)
        # define and reset to owned province
        await interaction.response.edit_message(content=None,
                                                view=self.prov_owned_view,
                                                embed=await create_prov_embed(prov_info, conn))
        return await interaction.followup.send(f"Successfully boosted Development at a cost of "
                                               f"{boost_cost} Economic authority! "
                                               f"The total development of {prov_info['name']} (ID: {province_id}) "
                                               f"is now **{prov_info['development'] + 1}**.")

    @discord.ui.button(label="Political", style=discord.ButtonStyle.blurple)
    async def political(self, interaction: discord.Interaction, button: discord.ui.Button):
        # define province variables
        prov_info = self.province_db
        user_info = self.user_info
        conn = self.pool
        province_id = prov_info['id']
        structures = [] if prov_info['structures'] is None else list(prov_info['structures'])
        # calculate dev boosting cost. base cost = current development * .75
        boost_cost = prov_info['development'] * .75
        # add modifiers from govt type
        govt_info = await conn.fetchrow('''SELECT *
                                           FROM cnc_govts
                                           WHERE govt_type = $1
                                             AND govt_subtype = $2;''',
                                        user_info['govt_type'], user_info['govt_subtype'])
        govt_mod = govt_info['dev_cost']
        boost_cost *= govt_mod
        # add modifiers from structures
        if "Lumber Mill" in structures:
            boost_cost *= .85
        # round boost cost up
        boost_cost = math.ceil(boost_cost)
        # check if user has sufficient authority
        if user_info['pol_auth'] < boost_cost:
            return await interaction.response.send_message(
                f"You do not have sufficient Political authority to boost in this "
                f"province. You are missing {boost_cost - user_info['econ_auth']} "
                f"Political authority.")
        # execute orders
        await conn.execute('''UPDATE cnc_users
                              SET pol_auth = pol_auth - $1
                              WHERE user_id = $2;''',
                           int(boost_cost), interaction.user.id)
        await conn.execute('''UPDATE cnc_provinces
                              SET development = development + 1
                              WHERE id = $1;''',
                           province_id)
        # define and reset to owned province
        await interaction.response.edit_message(content=None,
                                                view=self.prov_owned_view,
                                                embed=await create_prov_embed(prov_info, conn))
        return await interaction.followup.send(f"Successfully boosted Development at a cost of "
                                               f"{boost_cost} Political authority! "
                                               f"The total development of {prov_info['name']} (ID: {province_id}) "
                                               f"is now **{prov_info['development'] + 1}**.")

    @discord.ui.button(label="Military", style=discord.ButtonStyle.blurple)
    async def military(self, interaction: discord.Interaction, button: discord.ui.Button):
        # define province variables
        prov_info = self.province_db
        user_info = self.user_info
        conn = self.pool
        province_id = prov_info['id']
        structures = [] if prov_info['structures'] is None else list(prov_info['structures'])
        # calculate dev boosting cost. base cost = current development * .75
        boost_cost = prov_info['development'] * .75
        # add modifiers from govt type
        govt_info = await conn.fetchrow('''SELECT *
                                           FROM cnc_govts
                                           WHERE govt_type = $1
                                             AND govt_subtype = $2;''',
                                        user_info['govt_type'], user_info['govt_subtype'])
        govt_mod = govt_info['dev_cost']
        boost_cost *= govt_mod
        # add modifiers from structures
        if "Lumber Mill" in structures:
            boost_cost *= .85
        # round boost cost up
        boost_cost = math.ceil(boost_cost)
        # check if user has sufficient authority
        if user_info['mil_auth'] < boost_cost:
            return await interaction.response.send_message(
                f"You do not have sufficient Military authority to boost in this "
                f"province. You are missing {boost_cost - user_info['econ_auth']} "
                f"Military authority.")
        # execute orders
        await conn.execute('''UPDATE cnc_users
                              SET mil_auth = mil_auth - $1
                              WHERE user_id = $2;''',
                           int(boost_cost), interaction.user.id)
        await conn.execute('''UPDATE cnc_provinces
                              SET development = development + 1
                              WHERE id = $1;''',
                           province_id)
        # define and reset to owned province
        await interaction.response.edit_message(content=None,
                                                view=self.prov_owned_view,
                                                embed=await create_prov_embed(prov_info, conn))
        return await interaction.followup.send(f"Successfully boosted Development at a cost of "
                                               f"{boost_cost} Military authority! "
                                               f"The total development of {prov_info['name']} (ID: {province_id}) "
                                               f"is now **{prov_info['development'] + 1}**.")

    @discord.ui.button(label="Back", emoji="\U000023ea", style=discord.ButtonStyle.blurple)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=None,
                                                view=OwnedProvinceModifiation(self.author, self.province_db,
                                                                              self.user_info, self.pool))

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)


class DevelopmentAppropriateView(View):
    def __init__(self, author, province_db: asyncpg.Record, user_info: asyncpg.Record, pool: asyncpg.Pool):
        super().__init__(timeout=120)
        self.author = author
        self.province_db = province_db
        self.user_info = user_info
        self.pool = pool
        self.authority_type = None
        # define OG view
        self.prov_owned_view = OwnedProvinceModifiation(author, province_db,
                                                        user_info, pool)

    async def interaction_check(self, interaction: discord.Interaction):
        # ensures that the person using the interaction is the original author
        return interaction.user.id == self.author.id

    async def on_timeout(self) -> None:
        # disable all the children
        for child in self.children:
            child.disabled = True
        # update the view
        return await self.interaction.edit_original_response(view=self, content=None)

    @discord.ui.button(label="Economic", style=discord.ButtonStyle.blurple)
    async def economic(self, interaction: discord.Interaction, button: discord.ui.Button):
        # define stuff
        prov_info = self.province_db
        user_info = self.user_info
        conn = self.pool
        province_id = prov_info['id']
        development = prov_info['development']
        auth_return = int(development // 3.5)
        # execute
        await conn.execute('''UPDATE cnc_provinces
                              SET development = development - 1
                              WHERE id = $1;''',
                           province_id)
        await conn.execute('''UPDATE cnc_users
                              SET econ_auth = econ_auth + $1
                              WHERE user_id = $2;''',
                           auth_return, user_info['user_id'])
        # define and reset to owned province
        await interaction.response.edit_message(content=None,
                                                view=self.prov_owned_view,
                                                embed=await create_prov_embed(prov_info, conn))
        await interaction.followup.send(f"{auth_return} Economic authority appropriated from the "
                                        f"development of {prov_info['name']} (ID: {province_id}).")
        self.stop()

    @discord.ui.button(label="Political", style=discord.ButtonStyle.blurple)
    async def political(self, interaction: discord.Interaction, button: discord.ui.Button):
        # define stuff
        prov_info = self.province_db
        user_info = self.user_info
        conn = self.pool
        province_id = prov_info['id']
        development = prov_info['development']
        auth_return = int(development // 3.5)
        # execute
        await conn.execute('''UPDATE cnc_provinces
                              SET development = development - 1
                              WHERE id = $1;''',
                           province_id)
        await conn.execute('''UPDATE cnc_users
                              SET pol_auth = pol_auth + $1
                              WHERE user_id = $2;''',
                           auth_return, user_info['user_id'])
        # define and reset to owned province
        await interaction.response.edit_message(content=None,
                                                view=self.prov_owned_view,
                                                embed=await create_prov_embed(prov_info, conn))
        return await interaction.followup.send(f"{auth_return} Political authority appropriated from the "
                                               f"development of {prov_info['name']} (ID: {province_id}).")

    @discord.ui.button(label="Military", style=discord.ButtonStyle.blurple)
    async def military(self, interaction: discord.Interaction, button: discord.ui.Button):
        # define stuff
        prov_info = self.province_db
        user_info = self.user_info
        conn = self.pool
        province_id = prov_info['id']
        development = prov_info['development']
        auth_return = int(development // 3.5)
        # execute
        await conn.execute('''UPDATE cnc_provinces
                              SET development = development - 1
                              WHERE id = $1;''',
                           province_id)
        await conn.execute('''UPDATE cnc_users
                              SET mil_auth = mil_auth + $1
                              WHERE user_id = $2;''',
                           auth_return, user_info['user_id'])
        # define and reset to owned province
        await interaction.response.edit_message(content=None,
                                                view=self.prov_owned_view,
                                                embed=await create_prov_embed(prov_info, conn))
        return await interaction.followup.send(f"{auth_return} Military authority appropriated from the "
                                               f"development of {prov_info['name']} (ID: {province_id}).")

    @discord.ui.button(label="Back", emoji="\U000023ea", style=discord.ButtonStyle.blurple)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=None,
                                                view=OwnedProvinceModifiation(self.author, self.province_db,
                                                                              self.user_info, self.pool))

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)


class AbandonConfirm(View):
    def __init__(self, author, province_db: asyncpg.Record, user_info: asyncpg.Record, pool: asyncpg.Pool):
        super().__init__(timeout=120)
        self.prov_info = province_db
        self.user_info = user_info
        self.pool = pool
        self.author = author

    @discord.ui.button(label="Abandon Province", style=discord.ButtonStyle.danger)
    async def abandon_province_confirmed(self, interaction: discord.Interaction, button: discord.ui.Button):
        # define everything
        conn = self.pool
        province_id = self.prov_info['id']
        # abandon province
        await conn.execute('''UPDATE cnc_users
                              SET unrest = unrest + 1
                              WHERE user_id = $1;''',
                           interaction.user.id)
        await conn.execute('''UPDATE cnc_provinces
                              SET owner_id    = 0,
                                  occupier_id = 0,
                                  development = floor((random() * 9) + 1),
                                  citizens    = floor((random() * 10000) + 1000),
                                  structures  = '{}',
                                  fort_level  = 0
                              WHERE id = $1;''', province_id)
        # color the province
        await map_color(province_id, "#808080", self.pool)
        await interaction.response.edit_message(content=f"{self.prov_info['name']} (ID: {province_id}) "
                                                        f"has been successfully abandoned.", view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def abandon_province_cancelled(self, interaction: discord.Interaction, button: discord.ui.Button):
        # go back
        await interaction.response.edit_message(content=None, embed=await create_prov_embed(self.prov_info, self.pool),
                                                view=OwnedProvinceModifiation(self.author, self.prov_info,
                                                                              self.user_info, self.pool))


class OwnedProvinceModifiation(View):

    def __init__(self, author, province_db: asyncpg.Record, user_info: asyncpg.Record, pool: asyncpg.Pool):
        super().__init__(timeout=120)
        self.prov_info = province_db
        self.user_info = user_info
        self.pool = pool
        self.author = author

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        return await self.interaction.edit_original_response(view=self)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.author.id

    @discord.ui.button(label="Construct", emoji="\U00002692", style=discord.ButtonStyle.blurple, row=1)
    async def construct(self, interaction: discord.Interaction, button: discord.Button):
        # define the dropdown view
        construct_view = ConstructView(self.author, self.prov_info, self.user_info, self.pool)
        # set view to the construction dropdown
        construct_view.interaction = interaction
        await interaction.response.edit_message(view=construct_view)

    @discord.ui.button(label="Deconstruct", emoji="\U0001f3da", style=discord.ButtonStyle.blurple, row=1)
    async def deconstruct(self, interaction: discord.Interaction, button: discord.Button):
        # if the province has no structures, disable the button and update the view
        if not self.prov_info['structures']:
            button.disabled = True
            await interaction.response.edit_message(view=self)
            return await interaction.followup.send("There are no structures to deconstruct in this province.")
        # otherwise, carry on
        # define the dropdown view
        deconstruct_view = DeconstructView(self.author, self.prov_info, self.user_info, self.pool)
        deconstruct_view.interaction = interaction
        await interaction.response.edit_message(view=deconstruct_view)

    @discord.ui.button(label="Boost Development", emoji="\U0001f4c8", style=discord.ButtonStyle.blurple, row=2)
    async def boost_dev(self, interaction: discord.Interaction, button: discord.Button):
        # define everything
        conn = self.pool
        user_info = self.user_info
        prov_info = self.prov_info
        # define boost view
        dev_boost_view = DevelopmentBoostView(interaction.user, prov_info, user_info, conn)
        # send boost option view
        dev_boost_view.interaction = interaction
        await interaction.response.edit_message(content="**Select the type of authority to "
                                                        "spend using the buttons below.**",
                                                view=dev_boost_view)

    @discord.ui.button(label="Appropriate Development", emoji="\U0001f4c9", style=discord.ButtonStyle.blurple, row=2)
    async def appropriate_dev(self, interaction: discord.Interaction, button: discord.Button):
        # define everything
        conn = self.pool
        user_info = self.user_info
        prov_info = self.prov_info
        # check if development is sufficient
        if prov_info['development'] <= 5:
            return await interaction.response.send_message("This province does not have "
                                                           "sufficient development to be appropriated.")
        # ensure that buildings are still supported. each structure (minus 1) needs 10 development
        structures = len([] if prov_info['structures'] is None else list(prov_info['structures'])) - 1
        # if there are any structures (more than 2)
        if structures > 1:
            # if the amount of development, after appropriation, is insufficient to support the structures, deny
            if ((prov_info['development'] - 1) / 10) / structures <= 1:
                return await interaction.response.send_message("Existing Structures in this province "
                                                               "prevent development appropriation.")
        # otherwise, appropriate
        dev_appropriate_view = DevelopmentAppropriateView(interaction.user, prov_info, user_info, conn)
        dev_appropriate_view.interaction = interaction
        await interaction.response.edit_message(view=dev_appropriate_view, content="**Select the type of authority to "
                                                                                   "gain using the buttons below.**")

    @discord.ui.button(label="Abandon Province", emoji="\U0001f6ab", style=discord.ButtonStyle.danger, row=3)
    async def abandon_province(self, interaction: discord.Interaction, button: discord.Button):
        # define everything
        conn = self.pool
        user_info = self.user_info
        prov_info = self.prov_info
        # check if the user is at war. abandoning is not legal when at war
        war_check = await conn.fetchrow('''SELECT *
                                           FROM cnc_wars
                                           WHERE $1 = ANY (array_cat(attackers, defenders));''', user_info['name'])
        if war_check is not None:
            return await interaction.response.send_message("You cannot abandon provinces while at war.")
        # check to make sure that the user will have > 1 province after
        prov_owned_count = await conn.fetchval('''SELECT count(id)
                                                  FROM cnc_provinces
                                                  WHERE owner_id = $1;''',
                                               interaction.user.id)
        if prov_owned_count - 1 < 1:
            return await interaction.response.send_message("You cannot abandon your last province.")
        # otherwise, carry on
        abandon_province_view = AbandonConfirm(interaction.user, prov_info, user_info, conn)
        abandon_province_view.interaction = interaction
        await interaction.response.edit_message(view=abandon_province_view, embed=None, content="**Confirm below.**")


class UnownedProvince(View):

    def __init__(self, author: discord.User, province_db: asyncpg.Record, user_info: asyncpg.Record,
                 pool: asyncpg.Pool):
        super().__init__(timeout=120)
        self.prov_info = province_db
        self.user_info = user_info
        self.pool = pool
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.author.id

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        return await self.interaction.edit_original_response(view=self)

    @discord.ui.button(label="Colonize", style=discord.ButtonStyle.blurple, emoji="\U0001f3d5")
    async def colonize(self, interaction: discord.Interaction, button: discord.Button):
        # define everything
        conn = self.pool
        user_info = self.user_info
        prov_info = self.prov_info
        province_id = prov_info['id']
        user_id = user_info['user_id']
        # define OG view
        prov_owned_view = OwnedProvinceModifiation(self.author, prov_info,
                                                   user_info, conn)
        # ensure the user has researched the "Colonialism" tech
        if "Colonialism" not in user_info['tech']:
            return await interaction.followup.send("Colonization requires the Colonialism tech to be researched.")
        # check if the province is owned
        if prov_info['owner_id'] != 0:
            return await interaction.response.send_message("You cannot colonize a province owned by any other nation.")
        # check if the user has more than 15 provinces
        prov_owned_count = await conn.fetchval('''SELECT count(id)
                                                  FROM cnc_provinces
                                                  WHERE owner_id = $1;''',
                                               user_id)
        if prov_owned_count < 15:
            return await interaction.response.send_message("You cannot colonize until you own at least 15 provinces.")
        # check if the province is on the coast or bordering a province owned by the nation
        bordering_check = await conn.fetch('''SELECT *
                                              FROM cnc_provinces
                                              WHERE $1 = ANY (bordering)
                                                and owner_id = $2;''', province_id, user_id)
        if (not bordering_check) and (prov_info['coast'] is False):
            return await interaction.response.send_message("You cannot cannot colonize a province that you do not "
                                                           "border or that is not a costal province.")
        # calculate cost
        cost = 1
        # cost of colonization = (5 + provinces count) - 25, minimum 1, maximum 10
        cost += (5 + prov_owned_count) - 25
        # if the user has the "Manifest Destiny" tech, reduce cost by 2
        if "Manifest Destiny" in user_info['tech']:
            cost -= 2
        # enforce minimum
        if cost < 1:
            cost = 1
        # enforce maximum
        if cost > 10:
            cost = 10
        # if the nation is overextended, increase cost by 50%
        if prov_owned_count > user_info['overextend_limit']:
            cost *= 1.5
        # if the nation is a puppet, increase cost by 15%
        if user_info['overlord'] is not None:
            cost *= 1.15
        # check for enough authority
        if (user_info['econ_auth'] < cost) and (user_info['mil_auth'] < cost) and (user_info['pol_auth'] < cost):
            return await interaction.followup.send("You do not have enough authority to colonize that province. "
                                                   f"The cost of colonizing a province is currently {cost} authority.")
        # define dev
        dev = 3
        # if the user has Predatory Ethnology, add 2 to dev
        if 'Predatory Ethnology' in user_info['tech']:
            dev += 2
        # if all the checks pass, execute the operations
        await conn.execute('''UPDATE cnc_users
                              SET econ_auth = econ_auth - $1,
                                  mil_auth  = mil_auth - $1,
                                  pol_auth  = pol_auth - $1
                              WHERE user_id = $2;''', cost, interaction.user.id)
        await conn.execute('''UPDATE cnc_provinces
                              SET owner_id    = $1,
                                  occupier_id = $1,
                                  development = $3
                              WHERE id = $2;''', interaction.user.id, province_id, dev)
        await map_color(province_id, user_info['color'], conn)
        await interaction.response.edit_message(content=None,
                                                view=prov_owned_view,
                                                embed=await create_prov_embed(prov_info, conn))
        return await interaction.followup.send(f"{prov_info['name']} (ID: {province_id}) "
                                               f"has been successfully colonized.")


# === Dossier View ===

class DossierView(View):

    def __init__(self, interaction, embed: discord.Embed, user_info, conn: asyncpg.Pool):
        super().__init__(timeout=120)
        self.doss_embed = embed
        self.user_info = user_info
        self.conn = conn
        self.interaction = interaction

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        return await self.interaction.edit_original_response(view=self)

    @discord.ui.button(label="Summary", style=discord.ButtonStyle.blurple)
    async def summary(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # clear embed
        self.doss_embed.clear_fields()
        # pull province data
        province_list = await self.conn.fetch('''SELECT *
                                                 FROM cnc_provinces
                                                 WHERE owner_id = $1;''',
                                              self.user_info['user_id'])
        province_list = [p['id'] for p in province_list]
        province_count = len(province_list)
        province_list = ", ".join(str(p) for p in province_list)
        # populate summary
        self.doss_embed.add_field(name="Government",
                                  value=f"{self.user_info['govt_subtype']} {self.user_info['govt_type']}")
        # populate territory and count on its own line
        self.doss_embed.add_field(name=f"Territory (Total: {province_count})", value=f"{province_list}", inline=False)
        # send update
        await interaction.edit_original_response(embed=self.doss_embed)

    @discord.ui.button(label="Authority", style=discord.ButtonStyle.blurple)
    async def authority(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # clear embed
        self.doss_embed.clear_fields()
        # populate authority and gains
        self.doss_embed.add_field(name="=====================AUTHORITY=====================",
                                  value="Information known about your nation's authority.", inline=False)
        self.doss_embed.add_field(name="Political Authority (Change Last Turn)",
                                  value=f"{self.user_info['pol_auth']} ({plus_minus(self.user_info['last_pol_auth_gain'])})")
        self.doss_embed.add_field(name="Military Authority (Change Last Turn)",
                                  value=f"{self.user_info['mil_auth']} ({plus_minus(self.user_info['last_mil_auth_gain'])})")
        self.doss_embed.add_field(name="Economic Authority (Change Last Turn)",
                                  value=f"{self.user_info['econ_auth']} ({plus_minus(self.user_info['last_econ_auth_gain'])})")
        await interaction.edit_original_response(embed=self.doss_embed)

    @discord.ui.button(label="Military", style=discord.ButtonStyle.blurple)
    async def military(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # clear emebed
        self.doss_embed.clear_fields()
        # establish conn
        conn = self.conn
        # establish user_id
        user_id = interaction.user.id
        # pull troop and army data
        troops = await conn.fetchval('''SELECT SUM(troops)
                                        FROM cnc_armies
                                        WHERE owner_id = $1;''', user_id)
        armies = await conn.fetchval('''SELECT COUNT(*)
                                        FROM cnc_armies
                                        WHERE owner_id = $1;''', user_id)
        generals = await conn.fetchval('''SELECT COUNT(*)
                                          FROM cnc_generals
                                          WHERE owner_id = $1;''', user_id)
        total_manpower = await conn.fetchval('''SELECT SUM(citizens)
                                                FROM cnc_provinces
                                                WHERE owner_id = $1;''',
                                             user_id)
        # populate troops and armies
        self.doss_embed.add_field(name="=======================MILITARY======================",
                                  value="Information about your nation's military.", inline=False)
        self.doss_embed.add_field(name="Troops", value=f"{troops:,}")
        self.doss_embed.add_field(name="Armies", value=f"{armies}")
        self.doss_embed.add_field(name="Generals", value=f"{generals}")
        # populate manpower
        self.doss_embed.add_field(name="Manpower \n(Manpower Access)", value=f"{self.user_info['manpower']:,} "
                                                                             f"({self.user_info['manpower_access']}%)")
        self.doss_embed.add_field(name="Manpower Regen",
                                  value=f"{math.floor(total_manpower['sum'] * (self.user_info['manpower_regen'] / 100)):,} "
                                        f"({self.user_info['manpower_regen']}%)")
        self.doss_embed.add_field(name="Total Manpower", value=f"{total_manpower:,}")
        # update
        await interaction.edit_original_response(embed=self.doss_embed)

    @discord.ui.button(label="Economy", style=discord.ButtonStyle.blurple)
    async def economy(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # clear emebed
        self.doss_embed.clear_fields()
        # populate tax and spending stats
        self.doss_embed.add_field(name="======================ECONOMY======================",
                                  value="Information about your nation's economy.", inline=False)
        self.doss_embed.add_field(name="Taxation Level", value=f"{self.user_info['tax_level'] * 100}%")
        self.doss_embed.add_field(name="Public Spending Cost",
                                  value=f"{self.user_info['public_spend']} Economic Authority per turn")
        self.doss_embed.add_field(name="Military Upkeep Cost",
                                  value=f"{self.user_info['mil_upkeep']} Economic Authority per turn")
        # update
        await interaction.edit_original_response(embed=self.doss_embed)

    @discord.ui.button(label="Government", style=discord.ButtonStyle.blurple)
    async def government(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # clear emebed
        self.doss_embed.clear_fields()
        # count the number of provinces the user has
        province_count = await self.conn.fetchval('''SELECT count(id)
                                                     FROM cnc_provinces
                                                     WHERE owner_id = $1;''',
                                                  self.user_info['user_id'])
        # populate unrest, stability, overextension
        self.doss_embed.add_field(name="=====================GOVERNMENT===================",
                                  value="Information about your nation's government.", inline=False)
        self.doss_embed.add_field(name="National Unrest", value=f"{self.user_info['unrest']}")
        self.doss_embed.add_field(name="Stability", value=f"{self.user_info['stability']}")
        self.doss_embed.add_field(name="Overextension Limit",
                                  value=f"{province_count}/{self.user_info['overextend_limit']}")
        # populate overlord, if applicable
        if self.user_info['overlord']:
            self.doss_embed.add_field(name="Overlord", value=f"{self.user_info['overlord']}")
        # update
        await interaction.edit_original_response(embed=self.doss_embed)

    @discord.ui.button(label="Relations", style=discord.ButtonStyle.blurple)
    async def relations(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # clear emebed
        self.doss_embed.clear_fields()
        # establish conn
        conn = self.conn
        # pull information for the international relations and diplomacy
        # pull relations information
        alliances = await conn.fetch('''SELECT *
                                        FROM cnc_alliances
                                        WHERE $1 = ANY (members);''',
                                     self.user_info['name'])
        wars = await conn.fetch('''SELECT *
                                   FROM cnc_wars
                                   WHERE $1 = ANY (array_cat(attackers, defenders));''',
                                self.user_info['name'])
        trade_pacts = await conn.fetch('''SELECT *
                                          FROM cnc_trade_pacts
                                          WHERE $1 = ANY (members);''',
                                       self.user_info['name'])
        military_access = await conn.fetch('''SELECT *
                                              FROM cnc_military_access
                                              WHERE $1 = ANY (members);''',
                                           self.user_info['name'])

        def parse_relations(relations: list, name: str, wars: bool = False) -> str:
            """
            Parses out the names of nations within the input relations.
            ``wars``, if true, parses out attackers and defenders rather than "members".
            """
            if not relations:
                output = "None"
                return output
            elif wars:
                # define combined names
                combined_names = list()
                # for each relation, join to a comma-separated list if the relation "member" isn't the user's nation
                for relation in relations:
                    # define all names
                    defenders_names = [r for r in relation['defenders'] if r != name]
                    attackers_names = [r for r in relation['attackers'] if r != name]
                    combined_names += defenders_names + attackers_names
                output = ", ".join(combined_names)
                return output
            else:
                output = ""
                # for each relation, join to a comma-separated list if the relation "member" isn't the user's nation
                for relation in relations:
                    buffer_output = ", ".join([r for r in relation['members'] if r != name])
                    output += buffer_output
                return output

        allies = parse_relations(alliances, self.user_info['name'])
        wars = parse_relations(wars, self.user_info['name'], True)
        trade_pacts = parse_relations(trade_pacts, self.user_info['name'])
        military_access = parse_relations(military_access, self.user_info['name'])
        # populate relations
        self.doss_embed.add_field(name="=====================RELATIONS=====================",
                                  value="Information about your nation's diplomatic relationships.", inline=False)
        self.doss_embed.add_field(name="Allies", value=f"{allies}")
        self.doss_embed.add_field(name="Wars", value=f"{wars}")
        self.doss_embed.add_field(name="Trade Pacts", value=f"{trade_pacts}")
        self.doss_embed.add_field(name="Military Access", value=f"{military_access}")
        # update
        await interaction.edit_original_response(embed=self.doss_embed)


# === Government Modification Views

class GovernmentModView(View):

    def __init__(self, author: discord.User, interaction, conn: asyncpg.Pool,
                 govt_info: asyncpg.Record, govt_embed: discord.Embed):
        super().__init__(timeout=120)
        self.govt_info = govt_info
        self.conn = conn
        self.interaction = interaction
        self.author = author
        self.govt_info = govt_info
        self.govt_embed = govt_embed

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.author.id

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        return await self.interaction.edit_original_response(view=self)

    @discord.ui.button(label="Taxation", style=discord.ButtonStyle.blurple, emoji="\U0001f4b0")
    async def taxation(self, interaction: discord.Interaction, button: discord.Button):
        # defer
        await interaction.response.defer()
        # establish secondary view
        tax_menu = TaxManageView(self.author, self.interaction, self.conn, self.govt_info, self.govt_embed)
        # send secondary view
        await interaction.edit_original_response(view=tax_menu)

    @discord.ui.button(label="Public Spending", style=discord.ButtonStyle.blurple, emoji="\U0001f6e0")
    async def pub_spend(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # establish secondary view
        ps_menu = PublicSpendingView(self.author, self.interaction, self.conn, self.govt_info, self.govt_embed)
        # send secondary view
        await interaction.edit_original_response(view=ps_menu)

    @discord.ui.button(label="Military Upkeep", style=discord.ButtonStyle.blurple, emoji="\U0001f6e1")
    async def mil_upkeep(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # establish secondary view
        mu_menu = MilUpkeepView(self.author, self.interaction, self.conn, self.govt_info, self.govt_embed)
        # send secondary view
        await interaction.edit_original_response(view=mu_menu)

    @discord.ui.button(label="Boost Stability", style=discord.ButtonStyle.blurple, emoji="\U00002696")
    async def boost_stability(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # establish connection
        conn = self.conn
        # pull userinfo
        user_info = await user_db_info(interaction.user.id, conn)
        # pull user boost limit
        stab_boost_limit = user_info['stability_limit']
        # pull current stability
        stability = user_info['stability']
        # check if user has used their stability limit
        if stab_boost_limit <= 0:
            return await interaction.followup.send("You cannot expend more than 10 Political authority on "
                                                   "Stability boosting each turn.")
        # check if the boost amount will overdraw boosting
        if stab_boost_limit - 1 < 0:
            return await interaction.followup.send(
                f"You cannot boost that amount. The maximum boost amount this turn is"
                f" currently {stab_boost_limit} Political authority.")
        # check to ensure that boosting will not boost beyond 80
        if stability >= 80:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send("You cannot boost stability beyond 80.")
        # check if the user has a sufficient amount of political authority
        if user_info['pol_auth'] < 1:
            return await interaction.followup.send("You do not have sufficient Political "
                                                   "authority to boost that amount.")
        # otherwise carry on
        # reduce stab limit
        await conn.execute('''UPDATE cnc_users
                              SET stability_limit = stability_limit - 1
                              WHERE user_id = $1;''',
                           interaction.user.id)
        # pay pol auth
        await conn.execute('''UPDATE cnc_users
                              SET pol_auth = pol_auth - 1
                              WHERE user_id = $1;''',
                           interaction.user.id)
        await conn.execute('''UPDATE cnc_users
                              SET stability = stability + $1
                              WHERE user_id = $2;''',
                           math.floor((-stability ** .05) + 10), interaction.user.id)
        self.govt_embed.set_field_at(2, name="Stability", value=stability + math.floor((-stability ** .05) + 10))
        await interaction.edit_original_response(embed=self.govt_embed)
        return await interaction.followup.send(f"The stability of {user_info['name']} has been boosted.")

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.Button):
        # defer response
        await interaction.response.defer()
        # disable all buttons and update view
        for child in self.children:
            child.disabled = True
        await interaction.edit_original_response(view=self)


class TaxManageView(View):

    def __init__(self, author: discord.User, interaction, conn: asyncpg.Pool,
                 govt_info: asyncpg.Record, govt_embed: discord.Embed):
        super().__init__(timeout=120)
        self.user_info = None
        self.govt_info = govt_info
        self.conn = conn
        self.interaction = interaction
        self.author = author
        self.govt_embed = govt_embed

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.author.id

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        return await self.interaction.edit_original_response(view=self)

    @discord.ui.button(label="Decrease Tax", style=discord.ButtonStyle.blurple, emoji="\U0001f4c9")
    async def decrease(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # establish connection
        conn = self.conn
        # pull user info
        self.user_info = await user_db_info(self.author.id, conn)
        # if the user would decrease their tax below 0, stop them
        if self.user_info['tax_level'] - .01 <= 0:
            await interaction.followup.send("You cannot decrease your taxation below 0%.")
            button.disabled = True
            await interaction.edit_original_response(view=self)
        # otherwise, carry on
        else:
            # update tax level
            await conn.execute('''UPDATE cnc_users
                                  SET tax_level = tax_level - .01
                                  WHERE user_id = $1;''',
                               self.author.id)
            # send confirmation
            await interaction.followup.send(f"Your tax rate is now {self.user_info['tax_level'] - .01:.0%}!")
            # update embed
            self.govt_embed.set_field_at(-4, name="Current Tax Level", value=f"{self.user_info['tax_level'] - .01:.0%}")
            # enable increase button
            self.increase.disabled = False
            # update embed
            await interaction.edit_original_response(embed=self.govt_embed, view=self)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
    async def back(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # return to menu
        gov_menu = GovernmentModView(self.author, self.interaction, self.conn, self.govt_info, self.govt_embed)
        await interaction.edit_original_response(view=gov_menu)

    @discord.ui.button(label="Increase Tax", style=discord.ButtonStyle.blurple, emoji="\U0001f4c8")
    async def increase(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # establish connection
        conn = self.conn
        # pull user info
        self.user_info = await user_db_info(self.author.id, conn)
        # if the user would decrease their tax below 0, stop them
        if self.user_info['tax_level'] + .01 >= 20:
            await interaction.followup.send(f"You cannot increase your taxation above "
                                            f"{self.govt_info['tax_level'] + self.user_info['tax_level']:.0%}.")
            button.disabled = True
            await interaction.edit_original_response(view=self)
        # otherwise, carry on
        else:
            # update tax level
            await conn.execute('''UPDATE cnc_users
                                  SET tax_level = tax_level + .01
                                  WHERE user_id = $1;''',
                               self.author.id)
            # send confirmation
            await interaction.followup.send(f"Your tax rate is now {self.user_info['tax_level'] + .01:.0%}!")
            # update embed
            self.govt_embed.set_field_at(-4, name="Current Tax Level", value=f"{self.user_info['tax_level'] + .01:.0%}")
            # enable decrease button
            self.decrease.disabled = False
            # update embed
            await interaction.edit_original_response(embed=self.govt_embed, view=self)


class PublicSpendingView(View):

    def __init__(self, author: discord.User, interaction, conn: asyncpg.Pool,
                 govt_info: asyncpg.Record, govt_embed: discord.Embed):
        super().__init__(timeout=120)
        self.user_info = None
        self.govt_info = govt_info
        self.conn = conn
        self.interaction = interaction
        self.author = author
        self.govt_embed = govt_embed

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.author.id

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        return await self.interaction.edit_original_response(view=self)

    @discord.ui.button(label="Decrease Public Spending", style=discord.ButtonStyle.blurple, emoji="\U0001f4c9")
    async def decrease(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # establish connection
        conn = self.conn
        # pull user info
        self.user_info = await user_db_info(self.author.id, conn)
        # if the user is going to decrease below 0 spending, stop them
        if self.user_info['public_spend'] - 1 < 0:
            button.disabled = True
            await interaction.followup.send(f"You cannot decrease your public spending "
                                            f"below 0 Economic Authority.")
            await interaction.edit_original_response(view=self)
        else:
            # update public spending level
            await conn.execute('''UPDATE cnc_users
                                  SET public_spend = public_spend - 1
                                  WHERE user_id = $1;''',
                               self.author.id)
            # update embed
            self.govt_embed.set_field_at(-2, name="Public Spending",
                                         value=f"{self.user_info['public_spend'] - 1} Economic Authority")
            # enable increase button
            self.increase.disabled = False
            # update embed
            await interaction.edit_original_response(view=self, embed=self.govt_embed)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
    async def back(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # return to menu
        gov_menu = GovernmentModView(self.author, self.interaction, self.conn, self.govt_info, self.govt_embed)
        await interaction.edit_original_response(view=gov_menu)

    @discord.ui.button(label="Increase Public Spending", style=discord.ButtonStyle.blurple, emoji="\U0001f4c8")
    async def increase(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # establish connection
        conn = self.conn
        # pull user info
        self.user_info = await user_db_info(self.author.id, conn)
        # if the user is going to decrease below 0 spending, stop them
        if self.user_info['public_spend'] + 1 > 10:
            button.disabled = True
            await interaction.followup.send(f"You cannot increase your public spending "
                                            f"above 10 Economic Authority.")
            await interaction.edit_original_response(view=self)
        else:
            # update public spending level
            await conn.execute('''UPDATE cnc_users
                                  SET public_spend = public_spend + 1
                                  WHERE user_id = $1;''',
                               self.author.id)
            # update embed
            self.govt_embed.set_field_at(-2, name="Public Spending",
                                         value=f"{self.user_info['public_spend'] + 1} Economic Authority")
            # enable decrease button
            self.decrease.disabled = False
            # update embed
            await interaction.edit_original_response(embed=self.govt_embed, view=self)


class MilUpkeepView(View):

    def __init__(self, author: discord.User, interaction, conn: asyncpg.Pool,
                 govt_info: asyncpg.Record, govt_embed: discord.Embed):
        super().__init__(timeout=120)
        self.user_info = None
        self.govt_info = govt_info
        self.conn = conn
        self.interaction = interaction
        self.author = author
        self.govt_embed = govt_embed

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.author.id

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        return await self.interaction.edit_original_response(view=self)

    @discord.ui.button(label="Decrease Military Upkeep", style=discord.ButtonStyle.blurple, emoji="\U0001f4c9")
    async def decrease(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # establish connection
        conn = self.conn
        # pull user info
        self.user_info = await user_db_info(self.author.id, conn)
        # if the user is going to decrease below 0 spending, stop them
        if self.user_info['mil_upkeep'] - 1 < 0:
            button.disabled = True
            await interaction.followup.send(f"You cannot decrease your military upkeep "
                                            f"below 0 Military Authority.")
            await interaction.edit_original_response(view=self)
        else:
            # update public spending level
            await conn.execute('''UPDATE cnc_users
                                  SET mil_upkeep = mil_upkeep - 1
                                  WHERE user_id = $1;''',
                               self.author.id)
            # update embed
            self.govt_embed.set_field_at(-1, name="Military Upkeep",
                                         value=f"{self.user_info['mil_upkeep'] - 1} Military Authority")
            # enable increase button
            self.increase.disabled = False
            # update embed
            await interaction.edit_original_response(view=self, embed=self.govt_embed)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
    async def back(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # return to menu
        gov_menu = GovernmentModView(self.author, self.interaction, self.conn, self.govt_info, self.govt_embed)
        await interaction.edit_original_response(view=gov_menu)

    @discord.ui.button(label="Increase Military Upkeep", style=discord.ButtonStyle.blurple, emoji="\U0001f4c8")
    async def increase(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # establish connection
        conn = self.conn
        # pull user info
        self.user_info = await user_db_info(self.author.id, conn)
        # if the user is going to decrease below 0 spending, stop them
        if self.user_info['mil_upkeep'] + 1 > 10:
            button.disabled = True
            await interaction.followup.send(f"You cannot increase your Military Upkeep "
                                            f"above 10 Military Authority.")
            await interaction.edit_original_response(view=self)
        else:
            # update public spending level
            await conn.execute('''UPDATE cnc_users
                                  SET mil_upkeep = mil_upkeep + 1
                                  WHERE user_id = $1;''',
                               self.author.id)
            # update embed
            self.govt_embed.set_field_at(-1, name="Military Upkeep",
                                         value=f"{self.user_info['mil_upkeep'] + 1} Military Authority")
            # enable decrease button
            self.decrease.disabled = False
            # update embed
            await interaction.edit_original_response(embed=self.govt_embed, view=self)


# === Government Reform Views ===

class GovernmentReformMenu(View):

    def __init__(self, author: discord.User, interaction, conn: asyncpg.Pool, govt_embed: discord.Embed):
        super().__init__(timeout=120)
        self.conn = conn
        self.interaction = interaction
        self.author = author
        self.govt_embed = govt_embed

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.author.id

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        return await self.interaction.edit_original_response(view=self)

    @discord.ui.button(label="Reform Government Type", style=discord.ButtonStyle.blurple, emoji="\U0001f5ef")
    async def govt_type_reform(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # clear view
        await interaction.edit_original_response(view=None)
        # pull user info
        user_info = await user_db_info(self.author.id, self.conn)
        # anarchist nations cannot change government type
        if user_info['govt_type'] == "Anarchy":
            return await interaction.followup.send("Anarchist governments cannot voluntarily change government type.")
        # get development
        development = await self.conn.fetchval('''SELECT SUM(development)
                                                  FROM cnc_provinces
                                                  WHERE owner_id = $1;''',
                                               self.author.id)
        # if the nation has less than 50 development, disallow
        if development < 50:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send(f"{user_info['name']} does not have enough development "
                                                   f"to change government types.")
        # determine available government types
        govt_types = []
        # find monarchy
        if "Divine Right" in user_info['tech']:
            govt_types.append("Monarchy")
        # find republic
        if "Patrician Values" in user_info['tech']:
            govt_types.append("Republic")
        # find equalism
        if "Revolutionary Ideals" in user_info['tech']:
            govt_types.append("Equalism")
        if "Democratic Ideals" in user_info['tech']:
            govt_types.append("Democracy")
        # if there are no government types available, return such
        if len(govt_types) == 0:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send(f"No government types are available to {user_info['name']}.\n"
                                                   f"Government types can be unlocked by researching technology.")
        # create dropdown
        govt_type_dropdown = GovernmentReformTypeView(self.interaction, self.conn, govt_types, self.govt_embed)
        # update view
        await interaction.edit_original_response(view=govt_type_dropdown)

    @discord.ui.button(label="Reform Government Subtype", style=discord.ButtonStyle.blurple, emoji="\U0001f4dc")
    async def govt_subtype_reform(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # clear view
        await interaction.edit_original_response(view=None)
        # pull user info
        user_info = await user_db_info(self.author.id, self.conn)
        # anarchist nations cannot change government type
        if user_info['govt_type'] == "Anarchy":
            return await interaction.followup.send("Anarchist governments cannot voluntarily change government type.")
        # tribal government has no subtypes
        if user_info['govt_type'] == "Tribal":
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send("Tribal governments have no available subtypes.")
        # determine available government types
        govt_subtypes = await self.conn.fetch('''SELECT *
                                                 FROM cnc_govts
                                                 WHERE govt_type = $1;''', user_info['govt_type'])
        available_subtypes = [gs['govt_subtype'] for gs in govt_subtypes]
        # create dropdown view
        govt_subtype_view = GovernmentReformSubtypeView(self.interaction, self.conn,
                                                        available_subtypes, self.govt_embed)
        await interaction.edit_original_response(view=govt_subtype_view)

    @discord.ui.button(label="View Governments", style=discord.ButtonStyle.blurple, emoji="\U0001f4d6")
    async def view_govt_types(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # pull all government types
        govt_types = await self.conn.fetch('''SELECT DISTINCT govt_type
                                              FROM cnc_govts;''')
        # create list
        govt_types = [gt['govt_type'] for gt in govt_types]
        # dropdown view
        govt_types_dropdown = GovernmentTypesView(self.interaction, self.conn, govt_types, self.govt_embed)
        # execute view
        await interaction.edit_original_response(view=govt_types_dropdown)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        for child in self.children:
            child.disabled = True
        # close the view out
        await interaction.edit_original_response(view=self)


class GovernmentReformTypeView(discord.ui.View):
    def __init__(self, interaction, conn: asyncpg.Pool, govt_types: list, govt_embed: discord.Embed):
        super().__init__(timeout=120)
        self.conn = conn
        self.interaction = interaction
        self.govt_types = govt_types
        self.govt_embed = govt_embed
        govt_type_dropdown = GovernmentReformTypeDropdown(self.interaction, self.conn, self.govt_types, self.govt_embed)
        self.add_item(govt_type_dropdown)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.interaction.user.id

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        return await self.interaction.edit_original_response(view=self)


class GovernmentReformTypeDropdown(discord.ui.Select):

    def __init__(self, interaction: discord.Interaction, conn: asyncpg.Pool, govt_types: list,
                 govt_embed: discord.Embed):
        self.interaction = interaction
        self.conn = conn
        self.govt_embed = govt_embed
        # create the options
        govt_options = []
        for govt in govt_types:
            govt_options.append(discord.SelectOption(label=govt))
        # define the super
        super().__init__(placeholder="Choose a Government Type...", min_values=1, max_values=1,
                         options=govt_options)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.interaction.user.id

    async def callback(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer()
        # define variables
        type = self.values[0]
        # pull subtype information
        selected_type = await self.conn.fetchrow('''SELECT *
                                                    FROM cnc_govts
                                                    WHERE govt_type = $1;''', type)
        # build embed
        type_embed = discord.Embed(title=f"{selected_type['govt_type']}",
                                   color=discord.Color.dark_red(), description=f"*{selected_type['type_quote']}*")
        type_embed.add_field(name="Description", value=selected_type['type_description'], inline=False)
        # special note
        type_embed.add_field(name="Special Note", value=selected_type['type_note'], inline=False)
        # pull user_info
        user_info = await user_db_info(self.interaction.user.id, self.conn)
        # create enacting view
        govt_enact_view = GovernmentReformTypeEnact(self.interaction, self.conn, selected_type, user_info,
                                                    self.govt_embed)
        # update message
        await interaction.edit_original_response(embed=type_embed, view=govt_enact_view)


class GovernmentReformTypeEnact(discord.ui.View):

    def __init__(self, interaction: discord.Interaction, conn: asyncpg.Pool, govt_type: asyncpg.Record,
                 user_info: asyncpg.Record, govt_embed: discord.Embed):
        super().__init__(timeout=120)
        self.conn = conn
        self.interaction = interaction
        self.govt_type = govt_type
        self.user_info = user_info
        self.govt_embed = govt_embed

    @discord.ui.button(label="Reform", style=discord.ButtonStyle.success)
    async def reform_government(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # define connection
        conn = self.conn
        # if the user is already that government type, deny
        if self.user_info['govt_type'] == self.govt_type['govt_type']:
            main_govt_menu = GovernmentReformMenu(self.interaction.user, self.interaction, conn, self.govt_embed)
            await interaction.edit_original_response(view=main_govt_menu, embed=self.govt_embed)
            return await interaction.followup.send(
                f"{self.user_info['name']} is already a {self.govt_type['govt_type']}.\n"
                f"To change government subtypes, select the Reform Government Subtype"
                f" button on the Government Reform menu.")
        # calculate cost
        if not self.user_info['free_govt_change']:
            # calculate cost
            province_dev = await self.conn.fetchval('''SELECT SUM(development)
                                                       FROM cnc_provinces
                                                       WHERE owner_id = $1;''',
                                                    self.interaction.user.id)
            province_count = await self.conn.fetchval('''SELECT COUNT(*)
                                                         FROM cnc_provinces
                                                         WHERE owner_id = $1;''',
                                                      self.interaction.user.id)
            mean_dev = math.ceil(province_dev / province_count)
            total_cost = math.ceil(mean_dev / 5)
            # if the cost is greater than the 25-point limit, set it to 25
            if total_cost > 25:
                total_cost = 25
            # deny if not enough political auth
            if total_cost > self.user_info['pol_auth']:
                main_govt_menu = GovernmentReformMenu(self.interaction.user, self.interaction, conn, self.govt_embed)
                main_govt_menu.govt_type_reform.disabled = True
                await interaction.edit_original_response(view=main_govt_menu, embed=self.govt_embed)
                return await interaction.followup.send(
                    "You do not have enough Political Authority to Reform your government.\n"
                    f"To reform your government, you need a total of {total_cost} Political Authority.")
        # if the user has the free government change, set the total cost = 0
        else:
            await self.conn.execute('''UPDATE cnc_users
                                       SET free_govt_change = False
                                       WHERE user_id = $1;''',
                                    self.interaction.user.id)
            total_cost = 0
        # determine if an anarchist rebellion will occur
        if self.user_info['unrest'] > 25:
            # calculate the anarchy chance based on current unrest
            anarchy_chance = (self.user_info['unrest'] ** 2) / 75
            # calculate the roll based on the 100 minus the current unrest
            rebellion_roll = randrange((100 - self.user_info['unrest']), 100)
            # if the roll for a rebellion is less than the anarchy chance, rebellion occurs
            if rebellion_roll < anarchy_chance:
                await conn.execute('''UPDATE cnc_users
                                      SET anarchist_rebellion = TRUE
                                      WHERE user_id = $1;''',
                                   self.interaction.user.id)
        # enact government changes
        govt_info = self.govt_type
        # pull random subtype
        subtype = await conn.fetchrow('''SELECT *
                                         FROM cnc_govts
                                         WHERE govt_type = $1
                                         ORDER BY random();''',
                                      govt_info['govt_type'])
        # update the user's government type, subtype, pretitle, government info, increase unrest, and reduce pol auth
        await conn.execute('''UPDATE cnc_users
                              SET pretitle            = $1,
                                  govt_type           = $2,
                                  govt_subtype        = $3,
                                  manpower_access     = $4,
                                  govt_type_countdown = 10,
                                  temp_unrest         = '{10,8}',
                                  unrest              = unrest + 10,
                                  pol_auth            = pol_auth - $5
                              WHERE user_id = $6;''', subtype['pretitle'], govt_info['govt_type'],
                           subtype['govt_subtype'],
                           subtype['manpower'], total_cost, self.interaction.user.id)
        # edit embed
        govt_embed = self.govt_embed
        # update authority gains
        govt_embed.set_field_at(7, name="Base Economic Authority Gain", value=subtype['econ_auth'])
        govt_embed.set_field_at(8, name="Base Military Authority Gain", value=subtype['mil_auth'])
        govt_embed.set_field_at(9, name="Base Political Authority Gain", value=subtype['pol_auth'])
        # update unrest
        govt_embed.set_field_at(-8, name="Base Unrest Gain", value=f"{subtype['unrest_mod']:.0%}")
        # update manpower
        govt_embed.set_field_at(-7, name="Base Manpower Access", value=f"{subtype['manpower']:.0%}")
        # update development
        govt_embed.set_field_at(-6, name="Base Development Cost", value=f"{subtype['dev_cost']:.0%}")
        # update taxation
        govt_embed.set_field_at(-5, name="Base Taxation", value=f"{subtype['tax_level']:.0%}")
        govt_embed.set_field_at(-3, name="Maximum Taxation", value=f"{subtype['tax_level'] + 20:.0%}")
        # set up government view
        govt_reform_view = GovernmentReformMenu(self.interaction.user, self.interaction, self.conn, self.govt_embed)
        # send updates
        await interaction.edit_original_response(embed=govt_embed, view=govt_reform_view)
        # send confirmation message
        return await interaction.followup.send(f"The government of {self.user_info['name']} has been reformed into a "
                                               f"{subtype['govt_subtype']} {subtype['govt_type']}. Henceforth, the nation "
                                               f"shall be known as the {subtype['pretitle']} of {self.user_info['name']}!\n\n"
                                               f"*{subtype['type_quote']}*")

    @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # return to main menu
        main_govt_menu = GovernmentReformMenu(self.interaction.user, self.interaction, self.conn, self.govt_embed)
        return await interaction.edit_original_response(view=main_govt_menu, embed=self.govt_embed)


class GovernmentReformSubtypeView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, conn: asyncpg.Pool, govt_subtypes: list,
                 govt_embed: discord.Embed):
        super().__init__(timeout=120)
        self.conn = conn
        self.interaction = interaction
        self.govt_subtypes = govt_subtypes
        self.govt_embed = govt_embed
        govt_subtype_dropdown = GovernmentReformSubtypeDropdown(self.interaction, self.conn,
                                                                self.govt_subtypes, self.govt_embed)
        self.add_item(govt_subtype_dropdown)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.interaction.user.id

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        return await self.interaction.edit_original_response(view=self)


class GovernmentReformSubtypeDropdown(discord.ui.Select):

    def __init__(self, interaction: discord.Interaction, conn: asyncpg.Pool, govt_subtypes: list,
                 govt_embed: discord.Embed):
        self.interaction = interaction
        self.conn = conn
        self.govt_embed = govt_embed
        # create the options
        govt_options = []
        for govt in govt_subtypes:
            govt_options.append(discord.SelectOption(label=govt))
        # define the super
        super().__init__(placeholder="Choose a Government Subtype...", min_values=1, max_values=1,
                         options=govt_options)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.interaction.user.id

    async def callback(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer()
        # define variables
        subtype = self.values[0]
        # pull subtype information
        selected_subtype = await self.conn.fetchrow('''SELECT *
                                                       FROM cnc_govts
                                                       WHERE govt_subtype = $1;''', subtype)
        # build embed
        subtype_embed = discord.Embed(title=f"{selected_subtype['govt_subtype']} {selected_subtype['govt_type']}",
                                      color=discord.Color.dark_red(), description=f"*{selected_subtype['type_quote']}*")
        subtype_embed.add_field(name="Description", value=selected_subtype['subtype_description'], inline=False)
        # special note
        subtype_embed.add_field(name="Special Note", value=selected_subtype['subtype_note'], inline=False)
        # populate new authority gains
        subtype_embed.add_field(name="Base Economic Authority", value=selected_subtype['econ_auth'])
        subtype_embed.add_field(name="Base Military Authority", value=selected_subtype['mil_auth'])
        subtype_embed.add_field(name="Base Political Authority", value=selected_subtype['pol_auth'])
        # populate unrest
        subtype_embed.add_field(name="Base Unrest Gain", value=f"{selected_subtype['unrest_mod']:.0%}")
        # populate manpower
        subtype_embed.add_field(name="Base Manpower Access", value=f"{selected_subtype['manpower']:.0%}")
        # populate development
        subtype_embed.add_field(name="Base Development Cost", value=f"{selected_subtype['dev_cost']:.0%}")
        # populate tax level
        subtype_embed.add_field(name="Base Taxation", value=f"{selected_subtype['tax_level']:.0%}")
        # pull user_info
        user_info = await user_db_info(self.interaction.user.id, self.conn)
        # create enacting view
        govt_enact_view = GovernmentReformSubtypeEnact(self.interaction, self.conn, selected_subtype, user_info,
                                                       self.govt_embed)
        # update message
        await interaction.edit_original_response(embed=subtype_embed, view=govt_enact_view)


class GovernmentReformSubtypeEnact(discord.ui.View):

    def __init__(self, interaction: discord.Interaction, conn: asyncpg.Pool, govt_subtype: asyncpg.Record,
                 user_info: asyncpg.Record, govt_embed: discord.Embed):
        super().__init__(timeout=120)
        self.conn = conn
        self.interaction = interaction
        self.govt_subtype = govt_subtype
        self.user_info = user_info
        self.govt_embed = govt_embed

    @discord.ui.button(label="Reform", style=discord.ButtonStyle.success)
    async def reform_government(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # define connection
        conn = self.conn
        # if the user is already that government type, deny
        if self.user_info['govt_subtype'] == self.govt_subtype['govt_subtype']:
            main_govt_menu = GovernmentReformMenu(self.interaction.user, self.interaction, conn, self.govt_embed)
            await interaction.edit_original_response(view=main_govt_menu, embed=self.govt_embed)
            return await interaction.followup.send(
                f"{self.user_info['name']} is already a {self.govt_subtype['govt_subtype']} "
                f"{self.user_info['govt_type']}.")
        # calculate cost
        total_cost = 10
        # deny if not enough political auth
        if total_cost > self.user_info['pol_auth']:
            main_govt_menu = GovernmentReformMenu(self.interaction.user, self.interaction, conn, self.govt_embed)
            main_govt_menu.govt_type_reform.disabled = True
            await interaction.edit_original_response(view=main_govt_menu, embed=self.govt_embed)
            return await interaction.followup.send(
                "You do not have enough Political Authority to Reform your government.\n"
                f"To reform your government, you need a total of {total_cost} Political Authority.")
        # determine if an anarchist rebellion will occur
        if self.user_info['unrest'] > 25:
            # calculate the anarchy chance based on current unrest
            anarchy_chance = (self.user_info['unrest'] ** 2) / 100
            # calculate the roll based on the 100 minus the current unrest
            rebellion_roll = randrange((100 - self.user_info['unrest']), 100)
            # if the roll for a rebellion is less than the anarchy chance, rebellion occurs
            if rebellion_roll < anarchy_chance:
                await conn.execute('''UPDATE cnc_users
                                      SET anarchist_rebellion = TRUE
                                      WHERE user_id = $1;''',
                                   self.interaction.user.id)
        # enact government changes
        subtype_info = self.govt_subtype
        # update the user's government type, subtype, pretitle, government info, increase unrest, and reduce pol auth
        await conn.execute('''UPDATE cnc_users
                              SET pretitle            = $1,
                                  govt_subtype        = $2,
                                  manpower_access     = $3,
                                  govt_type_countdown = 10,
                                  temp_unrest         = '{10,8}',
                                  unrest              = unrest + 10,
                                  pol_auth            = pol_auth - $4
                              WHERE user_id = $5;''', subtype_info['pretitle'], subtype_info['govt_type'],
                           subtype_info['govt_subtype'],
                           subtype_info['manpower'], total_cost, self.interaction.user.id)
        # edit embed
        govt_embed = self.govt_embed
        # update authority gains
        govt_embed.set_field_at(7, name="Base Economic Authority Gain", value=subtype_info['econ_auth'])
        govt_embed.set_field_at(8, name="Base Military Authority Gain", value=subtype_info['mil_auth'])
        govt_embed.set_field_at(9, name="Base Political Authority Gain", value=subtype_info['pol_auth'])
        # update unrest
        govt_embed.set_field_at(-8, name="Base Unrest Gain", value=f"{subtype_info['unrest_mod']:.0%}")
        # update manpower
        govt_embed.set_field_at(-7, name="Base Manpower Access", value=f"{subtype_info['manpower']:.0%}")
        # update development
        govt_embed.set_field_at(-6, name="Base Development Cost", value=f"{subtype_info['dev_cost']:.0%}")
        # update taxation
        govt_embed.set_field_at(-5, name="Base Taxation", value=f"{subtype_info['tax_level']:.0%}")
        govt_embed.set_field_at(-3, name="Maximum Taxation", value=f"{subtype_info['tax_level'] + 20:.0%}")
        # set up government view
        govt_reform_view = GovernmentReformMenu(self.interaction.user, self.interaction, self.conn, self.govt_embed)
        # send updates
        await interaction.edit_original_response(embed=govt_embed, view=govt_reform_view)
        # send confirmation message
        return await interaction.followup.send(f"The government of {self.user_info['name']} has been reformed into a "
                                               f"{subtype_info['govt_subtype']} {subtype_info['govt_type']}. Henceforth, the nation "
                                               f"shall be known as the {subtype_info['pretitle']} of {self.user_info['name']}!\n\n"
                                               f"*{subtype_info['type_quote']}*")

    @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # return to main menu
        main_govt_menu = GovernmentReformMenu(self.interaction.user, self.interaction, self.conn, self.govt_embed)
        return await interaction.edit_original_response(view=main_govt_menu, embed=self.govt_embed)


class GovernmentTypesView(discord.ui.View):
    def __init__(self, interaction, conn: asyncpg.Pool, govt_types: list, govt_embed: discord.Embed):
        super().__init__(timeout=600)
        self.conn = conn
        self.interaction = interaction
        self.govt_types = govt_types
        self.govt_embed = govt_embed
        govt_type_dropdown = GovernmentTypesDropdown(self.interaction, self.conn, self.govt_types, self.govt_embed)
        self.add_item(govt_type_dropdown)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.interaction.user.id

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        return await self.interaction.edit_original_response(view=self)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # return to main menu
        govt_menu = GovernmentReformMenu(self.interaction.user, self.interaction, self.conn, self.govt_embed)
        return await interaction.edit_original_response(view=govt_menu, embed=self.govt_embed)


class GovernmentTypesDropdown(discord.ui.Select):

    def __init__(self, interaction: discord.Interaction, conn: asyncpg.Pool, govt_types: list,
                 govt_embed: discord.Embed):
        self.interaction = interaction
        self.conn = conn
        self.govt_embed = govt_embed
        # create the options
        govt_options = []
        for govt in govt_types:
            govt_options.append(discord.SelectOption(label=govt))
        # define the super
        super().__init__(placeholder="Choose a Government Type...", min_values=1, max_values=1,
                         options=govt_options)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.interaction.user.id

    async def callback(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer()
        # define variables
        govt_type = self.values[0]
        # pull subtype information
        selected_type = await self.conn.fetchrow('''SELECT *
                                                    FROM cnc_govts
                                                    WHERE govt_type = $1;''',
                                                 govt_type)
        # build embed
        type_embed = discord.Embed(title=f"{selected_type['govt_type']}",
                                   color=discord.Color.dark_red(), description=f"*{selected_type['type_quote']}*")
        type_embed.add_field(name="Description", value=selected_type['type_description'], inline=False)
        # special note
        type_embed.add_field(name="Special Note", value=selected_type['type_note'], inline=False)
        # get subtypes list
        subtypes = await self.conn.fetch('''SELECT govt_subtype
                                            FROM cnc_govts
                                            WHERE govt_type = $1;''',
                                         govt_type)
        subtypes_list = [sub['govt_subtype'] for sub in subtypes]
        # create enacting view
        govt_subtypes_dropdown = GovernmentSubtypesView(self.interaction, self.conn, subtypes_list, self.govt_embed,
                                                        govt_type)
        # update message
        await interaction.edit_original_response(embed=type_embed, view=govt_subtypes_dropdown)


class GovernmentSubtypesView(discord.ui.View):
    def __init__(self, interaction, conn: asyncpg.Pool, subtypes_list: list, govt_embed: discord.Embed, govt_type: str):
        super().__init__()
        self.conn = conn
        self.interaction = interaction
        self.subtypes_list = subtypes_list
        self.govt_embed = govt_embed
        govt_type_dropdown = GovernmentSubtypesDropdown(interaction, conn, subtypes_list, govt_embed, govt_type)
        self.add_item(govt_type_dropdown)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.interaction.user.id

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        return await self.interaction.edit_original_response(view=self)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # return to main menu
        govt_menu = GovernmentReformMenu(self.interaction.user, self.interaction, self.conn, self.govt_embed)
        return await interaction.edit_original_response(view=govt_menu, embed=self.govt_embed)


class GovernmentSubtypesDropdown(discord.ui.Select):

    def __init__(self, interaction: discord.Interaction, conn: asyncpg.Pool,
                 subtypes_list: list, govt_embed: discord.Embed, govt_type: str):
        self.interaction = interaction
        self.conn = conn
        self.govt_embed = govt_embed
        self.govt_type = govt_type
        # create the options
        subtype_options = []
        for subtype in subtypes_list:
            subtype_options.append(discord.SelectOption(label=subtype))
        # define the super
        super().__init__(placeholder="Choose a Government Subype...", min_values=1, max_values=1,
                         options=subtype_options)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.interaction.user.id

    async def callback(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer()
        # define variables
        subtype = self.values[0]
        # pull subtype information
        selected_subtype = await self.conn.fetchrow('''SELECT *
                                                       FROM cnc_govts
                                                       WHERE govt_subtype = $1
                                                         AND govt_type = $2;''',
                                                    subtype, self.govt_type)
        # build embed
        subtype_embed = discord.Embed(title=f"{selected_subtype['govt_subtype']} {selected_subtype['govt_type']}",
                                      color=discord.Color.dark_red())
        subtype_embed.add_field(name="Description", value=selected_subtype['subtype_description'], inline=False)
        # special note
        subtype_embed.add_field(name="Special Note", value=selected_subtype['subtype_note'], inline=False)
        # populate new authority gains
        subtype_embed.add_field(name="Base Economic Authority", value=selected_subtype['econ_auth'])
        subtype_embed.add_field(name="Base Military Authority", value=selected_subtype['mil_auth'])
        subtype_embed.add_field(name="Base Political Authority", value=selected_subtype['pol_auth'])
        # populate unrest
        subtype_embed.add_field(name="Base Unrest Gain", value=f"{selected_subtype['unrest_mod']:.0%}")
        # populate manpower
        subtype_embed.add_field(name="Base Manpower Access", value=f"{selected_subtype['manpower']:.0%}")
        # populate development
        subtype_embed.add_field(name="Base Development Cost", value=f"{selected_subtype['dev_cost']:.0%}")
        # populate tax level
        subtype_embed.add_field(name="Base Taxation", value=f"{selected_subtype['tax_level']:.0%}")
        # update message
        await interaction.edit_original_response(embed=subtype_embed)


# === Diplomacy Views ===

class DiplomaticMenuView(discord.ui.View):

    def __init__(self, interaction: discord.Interaction, conn: asyncpg.Pool, recipient_info: asyncpg.Record):
        super().__init__(timeout=120)
        self.interaction = interaction
        self.recipient_info = recipient_info
        self.conn = conn
        self.bot = interaction.client

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.interaction.user.id

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.interaction.edit_original_response(view=self)

    @discord.ui.button(label="Cooperative Relations", style=discord.ButtonStyle.success)
    async def cooperative(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer response
        await interaction.response.defer()
        # pull the db info for the user
        sender_info = await user_db_info(interaction.user.id, self.conn)
        # check to see if the nations are at war
        war_check = await self.conn.fetchrow('''SELECT *
                                                FROM cnc_wars
                                                WHERE $1 = ANY (array_cat(attackers, defenders))
                                                  AND $2 = ANY (array_cat(attackers, defenders));''',
                                             sender_info['name'], self.recipient_info['name'])
        # if the nations are at war, block the cooperative actions button
        if war_check is not None:
            button.disabled = True
            await self.interaction.edit_original_response(view=self)
            return await interaction.followup.send("Cooperative Relations are disabled while at war.")
        # add cooperative actions view
        cooperative_actions = CooperativeDiplomaticActions(interaction, self.conn, self.recipient_info)
        return await interaction.edit_original_response(view=cooperative_actions)

    @discord.ui.button(label="Hostile Relations", style=discord.ButtonStyle.danger)
    async def hostile(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer response
        await interaction.response.defer()
        # add hostile reactions
        hostile_actions = HostileDiplomaticActions(interaction, self.conn, self.recipient_info)
        return await interaction.edit_original_response(view=hostile_actions)


class CooperativeDiplomaticActions(discord.ui.View):

    def __init__(self, interaction: discord.Interaction, conn: asyncpg.Pool, recipient_info: asyncpg.Record):
        super().__init__(timeout=120)
        self.interaction = interaction
        self.recipient_info = recipient_info
        self.conn = conn
        self.bot = interaction.client

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.interaction.user.id

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.interaction.edit_original_response(view=self)

    @discord.ui.button(label="Diplomatic Relations", style=discord.ButtonStyle.blurple, emoji="\U0001f38c")
    async def diplomatic_relations(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # pull user info
        user_info = await user_db_info(interaction.user.id, self.conn)
        # create the recipient user
        recipient_user = self.bot.get_user(self.recipient_info['user_id'])
        # government type checks
        if self.recipient_info['govt_subtype'] == "Parish":
            return await interaction.followup.send("Voluntary diplomatic relations are disabled for nations with the"
                                                   " Parish Equalism ideology.")
        if ("Anarchic" in [self.recipient_info['govt_subtype'], user_info['govt_subtype']] and
                "Equalism" not in [self.recipient_info['govt_type'], user_info['govt_type']]):
            return await interaction.followup.send(
                "Nations with Anarchic Equalism cannot accept diplomatic relations with "
                "non-Equalist nations.")
        if (("Postcolonial" in [self.recipient_info['govt_subtype'], user_info['govt_subtype']]) and
                (any(idea not in ["Equalism", "Anarchy"]) for idea in
                 [self.recipient_info['govt_type'], user_info['govt_type']])):
            return await interaction.followup.send(
                "Nations with Postcolonial Anarchy cannot accept diplomatic relations "
                "with any non-Equalist or non-Anarchic nations.")
        elif self.recipient_info['govt_subtype'] in ["Primivitist", "Radical"]:
            return await interaction.followup.send("Nations with Primitivist or Radical Anarchy cannot take "
                                                   "any diplomatic actions.")
        # if either nation is pacificistic, it cannot participate in anything but diplomatic relations
        if "Pacifistic" in [self.recipient_info['govt_subtype'], self.recipient_info['govt_type']]:
            return await interaction.followup.send("Nations with the Pacifistic Anarchy ideology cannot use any "
                                                   "diplomatic action other than Diplomatic Relations.")
        # check if the nation already has diplomatic relations
        dp_check = await self.conn.fetchrow('''SELECT *
                                               FROM cnc_drs
                                               WHERE $1 = ANY (members)
                                                 AND $2 = ANY (members);''',
                                            user_info['name'], self.recipient_info['name'])
        # if the user already has diplomatic relations with the nation, deny
        if dp_check:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            accept_view = Accept(interaction)
            remove_msg = await interaction.followup.send(
                f"{self.recipient_info['name']} has already established diplomatic "
                f"relations with {user_info['name']}."
                f"\nWould you like to revoke these diplomatic relations?", view=accept_view)
            # wait for the accept/deny response
            await accept_view.wait()
            # if accept
            if accept_view.value:
                # remove diplomatic relations
                await self.conn.execute('''DELETE
                                           FROM cnc_drs
                                           WHERE $1 = ANY (members)
                                             AND $2 = ANY (members)
                                             AND pending = False;''',
                                        user_info['name'], self.recipient_info['name'])
                await remove_msg.edit(view=None)
                await recipient_user.send(f"{user_info['name']} has ended diplomatic relations with "
                                          f"{self.recipient_info['name']}.")
                # return to menu
                diplo_menu = DiplomaticMenuView(self.interaction, self.conn, self.recipient_info)
                await interaction.edit_original_response(view=diplo_menu)
                return await interaction.followup.send(f"{user_info['name']} has ended diplomatic relations with "
                                                       f"{self.recipient_info['name']}.")
            if not accept_view.value:
                # renable button
                button.disabled = False
                await interaction.edit_original_response(view=self)
                # remove accept/deny buttons
                return await remove_msg.edit(view=None)
        pending_check = await self.conn.fetchrow('''SELECT *
                                                    FROM cnc_pending_requests
                                                    WHERE $1 = ANY (members)
                                                      AND $2 = ANY (members)
                                                      AND type = 'Diplomatic Relations';''', user_info['name'],
                                                 self.recipient_info['name'])
        if pending_check:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send(f"{self.recipient_info['name']} is already considering an "
                                                   f"existing proposal from {user_info['name']}.")
        # check if the user has any hostile actions
        # check wars
        wars = await self.conn.fetchrow('''SELECT *
                                           FROM cnc_wars
                                           WHERE active = True
                                             AND ($1 = ANY (array_cat(attackers, defenders))
                                               AND $2 = ANY (array_cat(attackers, defenders));''',
                                        user_info['name'], self.recipient_info['name'])
        if wars is not None:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send(
                "Cooperative diplomatic actions are disabled for hostile nations.")
        # check embargoes
        embargoes = await self.conn.fetchrow('''SELECT *
                                                FROM cnc_embargoes
                                                WHERE $1 = ANY (sender)
                                                  AND $2 = ANY (target);''',
                                             user_info['name'], self.recipient_info['name'])
        if embargoes is not None:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send(
                "Cooperative diplomatic actions are disabled for hostile nations.\n"
                "*Embargoes are considered hostile actions.*")
        # check to ensure that the sender has sufficient political authority
        if user_info['pol_auth'] < 1:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send("You do not have sufficient Political Authority to send that "
                                                   "proposal.")
        # otherwise, send the message
        recipient_dm = await recipient_user.send(content=f"The {user_info['pretitle']} of "
                                                         f"{user_info['name']} has issued a request"
                                                         f" to establish diplomatic relations with"
                                                         f" {self.recipient_info['name']}. Please use"
                                                         f" the buttons below within 24 hours to "
                                                         f"respond to the request.")
        # create the response view
        dp_response = DiplomaticRelationsRespondView(interaction, self.conn, user_info, self.recipient_info,
                                                     recipient_dm,
                                                     self.bot)
        # edit the DM with the buttons
        await recipient_dm.edit(view=dp_response)
        # let the user know that they have sent a request
        await interaction.followup.send(f"{self.recipient_info['name']} has received a request to "
                                        f"establish diplomatic relations. ")
        # update the db to show pending
        await self.conn.execute('''INSERT INTO cnc_pending_requests
                                   VALUES ($1, $2, TRUE);''', interaction.message.id,
                                [self.recipient_info['name'], user_info['name']])
        # pre-emptively remove one political authoriy
        await self.conn.execute('''UPDATE cnc_users
                                   SET pol_auth = pol_auth - 1
                                   WHERE user_id = $1;''',
                                user_info['user_id'])
        # return to menu
        diplo_menu = DiplomaticMenuView(self.interaction, self.conn, self.recipient_info)
        return await interaction.edit_original_response(view=diplo_menu)

    @discord.ui.button(label="Military Alliance", style=discord.ButtonStyle.blurple, emoji="\U0001f6e1")
    async def military_alliance(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # pull user info
        user_info = await user_db_info(interaction.user.id, self.conn)
        # get recipient user
        recipient_user = self.bot.get_user(self.recipient_info['user_id'])
        # government type checks
        if self.recipient_info['govt_subtype'] == "Parish":
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send("Voluntary diplomatic relations are disabled for nations with the"
                                                   " Parish Equalism ideology.")
        if ("Anarchic" in [self.recipient_info['govt_subtype'], user_info['govt_subtype']] and
                "Equalism" not in [self.recipient_info['govt_type'], user_info['govt_type']]):
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send(
                "Nations with Anarchic Equalism cannot accept diplomatic relations with "
                "non-Equalist nations.")
        if (("Postcolonial" in [self.recipient_info['govt_subtype'], user_info['govt_subtype']]) and
                (any(idea not in ["Equalism", "Anarchy"]) for idea in
                 [self.recipient_info['govt_type'], user_info['govt_type']])):
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send(
                "Nations with Postcolonial Anarchy cannot accept diplomatic relations "
                "with any non-Equalist or non-Anarchic nations.")
        elif self.recipient_info['govt_subtype'] in ["Primivitist", "Radical"]:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send("Nations with Primitivist or Radical Anarchy cannot take "
                                                   "any diplomatic actions.")
        # if either nation is pacificistic, it cannot participate in anything but diplomatic relations
        if "Pacifistic" in [self.recipient_info['govt_subtype'], self.recipient_info['govt_type']]:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send("Nations with the Pacifistic Anarchy ideology cannot use any "
                                                   "diplomatic action other than Diplomatic Relations.")
        # if the user is a puppet, disallow
        if user_info['overlord'] is not None:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send("Puppeted nations are permitted only to join the military alliance"
                                                   " of their overlord.")
        # check if the user already has an alliance
        existing_ma_check = await self.conn.fetchrow('''SELECT *
                                                        FROM cnc_alliances
                                                        WHERE $1 = ANY (members)
                                                          AND $2 = ANY (members);''',
                                                     user_info['name'], self.recipient_info['name'])
        if existing_ma_check is not None:
            # disable button
            button.disabled = True
            await interaction.edit_original_response(view=self)
            # create the accept/reject view
            accept_view = Accept(interaction)
            # reject
            remove_msg = await interaction.followup.send(f"{self.recipient_info['name']} already has a "
                                                         f"military alliance with {user_info['name']}. "
                                                         f"Would you like to leave the military alliance?",
                                                         view=accept_view)
            # wait for the interaction
            await accept_view.wait()
            # if yes, remove the user from the alliance
            if accept_view.value:
                # remove user from alliance
                await self.conn.execute('''UPDATE cnc_alliances
                                           SET members = ARRAY_REMOVE(members, $1)
                                           WHERE $1 = ANY (members);''', user_info['name'])
                # if there are now alliances with only one user, delete them
                await self.conn.execute('''DELETE
                                           FROM cnc_alliances
                                           WHERE cardinality(members) < 2;''')
                # notify all other members of the alliance
                for member in existing_ma_check['members']:
                    # get info and user
                    member_info = await self.conn.fetchrow('''SELECT *
                                                              FROM cnc_users
                                                              WHERE name = $1;''',
                                                           member)
                    if member_info['name'] == user_info['name']:
                        continue
                    member_user = self.bot.get_user(member_info['user_id'])
                    # send dm
                    await member_user.send(content=f"{user_info['name']} has left the military alliance with "
                                                   f"{member_info['name']}!")
                # return to menu
                diplo_menu = DiplomaticMenuView(self.interaction, self.conn, self.recipient_info)
                await interaction.edit_original_response(view=diplo_menu)
                # remove accept/deny buttons
                await remove_msg.edit(view=None)
                # notify user
                return await interaction.followup.send(f"{user_info['name']} has left the military alliance with "
                                                       f"{self.recipient_info['name']}!")
            elif not accept_view.value:
                # renable button
                button.disabled = False
                await interaction.edit_original_response(view=self)
                # remove accept/deny buttons
                return await remove_msg.edit(view=None)
        # check if the user is in another alliance
        other_ma_check = await self.conn.fetchrow('''SELECT *
                                                     FROM cnc_alliances
                                                     WHERE $1 != ANY(members) AND $2 = ANY (members);''',
                                                  user_info['name'], self.recipient_info['name'])
        if other_ma_check is not None:
            # disable button
            button.disabled = True
            await interaction.edit_original_response(view=self)
            # reject
            return await interaction.followup.send(f"{self.recipient_info['name']} is already a member of a military "
                                                   f"alliance.")
        # pending ma check
        pending_ma_check = await self.conn.fetchrow('''SELECT *
                                                       FROM cnc_pending_requests
                                                       WHERE $1 = ANY (members)
                                                         AND $2 = ANY (members);''',
                                                    user_info['name'], self.recipient_info['name'])
        if pending_ma_check is not None:
            # disable button
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send(f"{self.recipient_info['name']} is already considering an "
                                                   f"existing proposal from {user_info['name']}.")
        # check if the user has any hostile actions
        # check wars
        wars = await self.conn.fetchrow('''SELECT *
                                           FROM cnc_wars
                                           WHERE active = True
                                             AND ($1 = ANY (array_cat(attackers, defenders))
                                               AND $2 = ANY (array_cat(attackers, defenders));''',
                                        user_info['name'], self.recipient_info['name'])
        if wars is not None:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send("Cooperative diplomatic actions are disabled for hostile nations.")
        # check embargoes
        embargoes = await self.conn.fetchrow('''SELECT *
                                                FROM cnc_embargoes
                                                WHERE $1 = ANY (sender)
                                                  AND $2 = ANY (target);''',
                                             user_info['name'], self.recipient_info['name'])
        if embargoes is not None:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send("Cooperative diplomatic actions are disabled for hostile nations.\n"
                                                   "*Embargoes are considered hostile actions.*")
        # check to ensure that the sender has sufficient military authority
        if user_info['mil_auth'] < 1:
            # disable button
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send("You do not have sufficient Military Authority.")
        # otherwise, send the dm
        recipient_dm = await recipient_user.send(f"The {user_info['pretitle']} of {user_info['name']} has proposed that"
                                                 f" {self.recipient_info['name']} join their Military Alliance. Please"
                                                 f" use the buttons below to respond to the request within 24 hours.")
        # create the response view
        ma_response = MilitaryAllianceRespondView(interaction, self.conn, user_info, self.recipient_info, recipient_dm,
                                                  self.bot)
        # edit the dm with the response
        await recipient_dm.edit(view=ma_response)
        # let the sender know the request has been successfully sent
        await interaction.followup.send(f"{self.recipient_info['name']} has recieved a "
                                        f"request to join the Military Alliance.")
        # remove one military authority from sender
        await self.conn.execute('''UPDATE cnc_users
                                   SET mil_auth = mil_auth - 1
                                   WHERE user_id = $1;''',
                                interaction.user.id)
        # return to menu
        diplo_menu = DiplomaticMenuView(self.interaction, self.conn, self.recipient_info)
        return await interaction.edit_original_response(view=diplo_menu)

    @discord.ui.button(label="Trade Pact", style=discord.ButtonStyle.blurple, emoji="\U0001fa99")
    async def trade_pacts(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # pull user info
        user_info = await user_db_info(interaction.user.id, self.conn)
        # create the recipient user
        recipient_user = self.bot.get_user(self.recipient_info['user_id'])
        # government type checks
        if self.recipient_info['govt_subtype'] == "Parish":
            return await interaction.followup.send("Voluntary diplomatic actions are disabled for nations with the"
                                                   " Parish Equalism ideology.")
        if ("Anarchic" in [self.recipient_info['govt_subtype'], user_info['govt_subtype']] and
                "Equalism" not in [self.recipient_info['govt_type'], user_info['govt_type']]):
            return await interaction.followup.send(
                "Nations with Anarchic Equalism cannot accept diplomatic actions from "
                "non-Equalist nations.")
        if (("Postcolonial" in [self.recipient_info['govt_subtype'], user_info['govt_subtype']]) and
                (any(idea not in ["Equalism", "Anarchy"]) for idea in
                 [self.recipient_info['govt_type'], user_info['govt_type']])):
            return await interaction.followup.send(
                "Nations with Postcolonial Anarchy cannot accept diplomatic actions "
                "from any non-Equalist or non-Anarchic nations.")
        elif self.recipient_info['govt_subtype'] in ["Primivitist", "Radical"]:
            return await interaction.followup.send("Nations with Primitivist or Radical Anarchy cannot take "
                                                   "any diplomatic actions.")
        # if either nation is pacificistic, it cannot participate in anything but diplomatic relations
        if "Pacifistic" in [self.recipient_info['govt_subtype'], self.recipient_info['govt_type']]:
            return await interaction.followup.send("Nations with the Pacifistic Anarchy ideology cannot use any "
                                                   "diplomatic action other than Diplomatic Relations.")
        # check if the nation already has diplomatic relations
        tp_check = await self.conn.fetchrow('''SELECT *
                                               FROM cnc_trade_pacts
                                               WHERE $1 = ANY (members)
                                                 AND $2 = ANY (members);''',
                                            user_info['name'], self.recipient_info['name'])
        # if the user already has diplomatic relations with the nation, deny
        if tp_check:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            accept_view = Accept(interaction)
            remove_msg = await interaction.followup.send(
                f"{self.recipient_info['name']} has already established a trade pact with {user_info['name']}."
                f"\nWould you like to end the trade pact?", view=accept_view)
            # wait for the accept/deny response
            await accept_view.wait()
            # if accept
            if accept_view.value:
                # remove diplomatic relations
                await self.conn.execute('''DELETE
                                           FROM cnc_trade_pacts
                                           WHERE $1 = ANY (members)
                                             AND $2 = ANY (members);''',
                                        user_info['name'], self.recipient_info['name'])
                await remove_msg.edit(view=None)
                await recipient_user.send(f"{user_info['name']} has ended the trade pact with "
                                          f"{self.recipient_info['name']}.")
                # return to menu
                diplo_menu = DiplomaticMenuView(self.interaction, self.conn, self.recipient_info)
                await interaction.edit_original_response(view=diplo_menu)
                return await interaction.followup.send(f"{user_info['name']} has ended the trade pact with "
                                                       f"{self.recipient_info['name']}.")
            if not accept_view.value:
                # renable button
                button.disabled = False
                await interaction.edit_original_response(view=self)
                # remove accept/deny buttons
                return await remove_msg.edit(view=None)
        pending_check = await self.conn.fetchrow('''SELECT *
                                                    FROM cnc_pending_requests
                                                    WHERE $1 = ANY (members)
                                                      AND $2 = ANY (members)
                                                      AND type = 'Trade Pact';''', user_info['name'],
                                                 self.recipient_info['name'])
        if pending_check:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send(f"{self.recipient_info['name']} is already considering an "
                                                   f"existing proposal from {user_info['name']}.")
        # check if the user has any hostile actions
        # check wars
        wars = await self.conn.fetchrow('''SELECT *
                                           FROM cnc_wars
                                           WHERE active = True
                                             AND ($1 = ANY (array_cat(attackers, defenders))
                                               AND $2 = ANY (array_cat(attackers, defenders)));''',
                                        user_info['name'], self.recipient_info['name'])
        if wars is not None:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send("Cooperative diplomatic actions are disabled for hostile nations.")
        # check embargoes
        embargoes = await self.conn.fetchrow('''SELECT *
                                                FROM cnc_embargoes
                                                WHERE $1 = ANY (sender)
                                                  AND $2 = ANY (target);''',
                                             user_info['name'], self.recipient_info['name'])
        if embargoes is not None:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send("Cooperative diplomatic actions are disabled for hostile nations.\n"
                                                   "*Embargoes are considered hostile actions.*")
        # check to ensure that the sender has sufficient political authority
        if user_info['pol_auth'] < 1:
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send("You do not have sufficient Political Authority to send that "
                                                   "proposal.")
        # otherwise, send the message
        recipient_dm = await recipient_user.send(content=f"The {user_info['pretitle']} of "
                                                         f"{user_info['name']} has issued a request"
                                                         f" to establish a trade pact with"
                                                         f" {self.recipient_info['name']}. Please use"
                                                         f" the buttons below within 24 hours to "
                                                         f"respond to the request.")
        # create the response view
        tp_response = TradePactRespondView(interaction, self.conn, user_info, self.recipient_info,
                                           recipient_dm,
                                           self.bot)
        # edit the DM with the buttons
        await recipient_dm.edit(view=tp_response)
        # let the user know that they have sent a request
        await interaction.followup.send(f"{self.recipient_info['name']} has received a request to "
                                        f"establish a trade pact. ")
        # update the db to show pending
        await self.conn.execute('''INSERT INTO cnc_pending_requests
                                   VALUES ($1, $2, TRUE);''', interaction.message.id,
                                [self.recipient_info['name'], user_info['name']])
        # pre-emptively remove one political authoriy
        await self.conn.execute('''UPDATE cnc_users
                                   SET pol_auth = pol_auth - 1
                                   WHERE user_id = $1;''',
                                user_info['user_id'])
        # return to menu
        diplo_menu = DiplomaticMenuView(self.interaction, self.conn, self.recipient_info)
        return await interaction.edit_original_response(view=diplo_menu)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # return to menu
        diplo_menu = DiplomaticMenuView(self.interaction, self.conn, self.recipient_info)
        await interaction.edit_original_response(view=diplo_menu)


class HostileDiplomaticActions(discord.ui.View):

    def __init__(self, interaction: discord.Interaction, conn: asyncpg.Pool, recipient_info: asyncpg.Record):
        super().__init__(timeout=120)
        self.interaction = interaction
        self.recipient_info = recipient_info
        self.conn = conn
        self.bot = interaction.client

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.interaction.user.id

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.interaction.edit_original_response(view=self)

    @discord.ui.button(label="Embargo", style=discord.ButtonStyle.grey, emoji="\U0001f4e6")
    async def embargo(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # pull user info
        user_info = await user_db_info(interaction.user.id, self.conn)
        # create the recipient user
        recipient_user = self.bot.get_user(self.recipient_info['user_id'])

        # check if the user is already embargoing
        embargo_check = await self.conn.fetchrow('''SELECT *
                                                    FROM cnc_embargoes
                                                    WHERE sender = $1
                                                      AND target = $2;''',
                                                 user_info['name'], self.recipient_info['name'])
        if embargo_check is not None:
            accept_view = Accept(interaction)
            button.disabled = True
            await interaction.edit_original_response(view=self)
            remove_msg = await interaction.followup.send(f"{user_info['name']} has already issued an embargo against "
                                                         f"{self.recipient_info['name']}.\n"
                                                         f"Would you like to recall the embargo?", view=accept_view)
            # wait for the accept/deny response
            await accept_view.wait()
            # if accept
            if accept_view.value:
                # remove diplomatic relations
                await self.conn.execute('''DELETE
                                           FROM cnc_embargoes
                                           WHERE $1 = ANY (members)
                                             AND $2 = ANY (members);''',
                                        user_info['name'], self.recipient_info['name'])
                await remove_msg.edit(view=None)
                await recipient_user.send(f"{user_info['name']} has ended the embargo against "
                                          f"{self.recipient_info['name']}.")
                # return to menu
                diplo_menu = DiplomaticMenuView(self.interaction, self.conn, self.recipient_info)
                await interaction.edit_original_response(view=diplo_menu)
                return await interaction.followup.send(f"{user_info['name']} has ended the embargo against "
                                                       f"{self.recipient_info['name']}.")
            if not accept_view.value:
                # renable button
                button.disabled = False
                await interaction.edit_original_response(view=self)
                # remove accept/deny buttons
                return await remove_msg.edit(view=None)
        # check if the user has any existing cooperative relationships
        alliances = await self.conn.fetchrow('''SELECT *
                                                FROM cnc_alliances
                                                WHERE $1 = ANY (members)
                                                  AND $2 = ANY (members);''',
                                             user_info['name'], self.recipient_info['name'])
        trade_pacts = await self.conn.fetchrow('''SELECT *
                                                  FROM cnc_trade_pacts
                                                  WHERE $1 = ANY (members)
                                                    AND $2 = ANY (members);''',
                                               user_info['name'], self.recipient_info['name'])
        diplomatic_relations = await self.conn.fetchrow('''SELECT *
                                                           FROM cnc_drs
                                                           WHERE $1 = ANY (members)
                                                             AND $2 = ANY (members);''',
                                                        user_info['name'], self.recipient_info['name'])
        pending_cooperation = await self.conn.fetchrow('''SELECT *
                                                          FROM cnc_pending_requests
                                                          WHERE $1 = ANY (members)
                                                            AND $2 = ANY (members)
                                                            AND type = ANY ($3);''',
                                                       user_info['name'], self.recipient_info['name'],
                                                       ["Military Alliance, Trade Pact, Diplomatic Relations"])
        if (alliances is not None) or (trade_pacts is not None) or (diplomatic_relations is not None) or (
                pending_cooperation is not None):
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send(f"Hostile actions cannot be performed while {user_info['name']} "
                                                   f"maintains cooperative relations or awaits responses to "
                                                   f"cooperative relations requests.")
        # if all the checks pass, add the embargo
        await self.conn.execute('''INSERT INTO cnc_embargoes
                                   VALUES ($1, $2, $3);''',
                                interaction.id, user_info['name'], self.recipient_info['name'])
        # notify target
        await recipient_user.send(f"{user_info['name']} has issued an embargo against {self.recipient_info['name']}.")
        # notify user
        await interaction.followup.send(f"{user_info['name']} has issued an embargo against "
                                        f"{self.recipient_info['name']}.")
        # return to menu
        diplo_menu = DiplomaticMenuView(self.interaction, self.conn, self.recipient_info)
        return await interaction.edit_original_response(view=diplo_menu)

    @discord.ui.button(label="War", style=discord.ButtonStyle.grey, emoji="\U00002694")
    async def war(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # pull user info
        sender_info = await user_db_info(interaction.user.id, self.conn)
        # create the recipient user
        recipient_user = self.bot.get_user(self.recipient_info['user_id'])
        # government type checks
        if sender_info["govt_subtype"] in ["Populist", "Parish", "Radical", "Primitivist", "Pacifistic"]:
            # if the government subtype disables declarations of war, disable the button and send a message
            button.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send(f"{sender_info['govt_subtype']} {sender_info['govt_type']} "
                                                   f"nations may not declare war.")
        # war declaration cost
        if self.recipient_info['govt_type'] == "Equalism":
            declaration_cost = 0
        else:
            declaration_cost = 2
        # check if the user has enough military authority for the declaration
        if sender_info['mil_auth'] < declaration_cost:
            # disable the button and send a message
            button.disabled = True
            await self.interaction.edit_original_response(view=self)
            return await interaction.followup.send("You do not have enough Military Authority to declare war.")
        # check to see if the two nations are already at war
        war_check = await self.conn.fetchrow('''SELECT *
                                                FROM cnc_wars
                                                WHERE $1 = ANY (array_cat(attackers, defenders))
                                                  AND $2 = ANY (array_cat(attackers, defenders));''',
                                             sender_info['name'], self.recipient_info['name'])
        # check to see if the the nations have a truce
        truce_check = await self.conn.fetchrow('''SELECT * FROM cnc_peace_treaties 
                                                  WHERE $1 = ANY (members) 
                                                    AND $2 = ANY (members) 
                                                    AND truce_length > 0;''',
                                               sender_info['name'], self.recipient_info['name'])
        # if the users already have a truce, disable the button and send a message
        if truce_check is not None:
            # disable button
            button.disabled = True
            await interaction.edit_original_response(view=self)
            # send message and return
            return await interaction.followup.send(f"{sender_info['name']} and {self.recipient_info['name']} have an"
                                            f"active truce, which will last for "
                                            f"`{truce_check['truce_length']}` more turns.")
        if war_check is not None:
            # disable the button and return a message
            button.disabled = True
            await self.interaction.edit_original_response(view=self)
            return await interaction.followup.send(f"You are already participating in a war against "
                                                   f"{self.recipient_info['name']} and cannot declare another war.\n"
                                                   f"To negotiate a peace with this nation, "
                                                   f"use `/cnc war war_id:{war_check['id']}`.")
        # create a base list of CBs available
        available_cbs = ["Conquest", "Subjugate", "Force Reparations"]
        # check CBs available by tech
        if "Ideological Crusade" in sender_info['tech']:
            available_cbs.append("Indoctrinate")
        if "National Humiliation" in sender_info['tech']:
            available_cbs.append("Humiliate")
        if "Subjugation" in sender_info['tech']:
            # calculate the average national developments of sender and receiver
            sender_dev = await self.conn.fetchval('''SELECT AVG(development)
                                                     FROM cnc_provinces
                                                     WHERE owner_id = $1;''',
                                                  sender_info['id'])
            recipient_dev = await self.conn.fetchval('''SELECT AVG(development)
                                                        FROM cnc_provinces
                                                        WHERE owner_id = $1;''',
                                                     self.recipient_info['user_id'])
            # if 50% of the senders dev is larger than the recipient's dev, permit subjugation
            if recipient_dev < sender_dev * .5:
                available_cbs.append("Subjugate")
        if "Total War" in sender_info['tech']:
            available_cbs.append("Total War")
        # check to see if the recipient has any puppets
        overlord_check = await self.conn.fetch('''SELECT *
                                                  FROM cnc_users
                                                  WHERE overlord = $1;''', recipient_user.id)
        if overlord_check:
            available_cbs.append("Force Independence")
        # if the recipient is equalist and the sender is not equalist, add the suppress the revolution CB
        if (self.recipient_info['govt_type'] == "Equalism") and (sender_info['govt_type'] != "Equalism"):
            available_cbs.append("Suppress the Revolution")
        # if the recipient is not equalist and the sender is equalist, add the Spread the Revolution CB
        if (self.recipient_info['govt_type'] != "Equalism") and (sender_info['govt_type'] == "Equalism"):
            available_cbs.append("Spread the Revolution")
        # if the recipient is the sender's overlord, clear all other options and leave "Rebel Against Overlord"
        if recipient_user.id == sender_info['overlord']:
            available_cbs.clear()
            available_cbs = ['Rebel Against Overlord']
        # add the war declaration view
        war_view = WarDeclarationView(self.interaction, self.conn, sender_info,
                                      self.recipient_info, self.bot, available_cbs)
        # change the view
        return await self.interaction.edit_original_response(view=war_view)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # return to menu
        diplo_menu = DiplomaticMenuView(self.interaction, self.conn, self.recipient_info)
        await interaction.edit_original_response(view=diplo_menu)


class DiplomaticRelationsRespondView(discord.ui.View):

    def __init__(self, interaction: discord.Interaction, conn: asyncpg.Pool, sender_info: asyncpg.Record,
                 recipient_info: asyncpg.Record, dm: discord.Message, bot: discord.Client):
        super().__init__(timeout=86400)
        self.interaction = interaction
        self.conn = conn
        self.sender_info = sender_info
        self.dm = dm
        self.recipient_info = recipient_info
        self.bot = bot

    async def on_timeout(self):
        # disable buttons and update view
        self.stop()
        # send message that the user has failed to react in time
        await self.dm.reply(content="You have failed to reply within 24 hours. The request has been auto-rejected.")
        # send message to the sender that the request has been denied
        sender_user = self.bot.get_user(self.sender_info['user_id'])
        # delete pending request
        await self.conn.execute('''DELETE
                                   FROM cnc_pending_requests
                                   WHERE id = $1;''', self.interaction.message.id)
        await safe_dm(self.bot, self.sender_info['user_id'], content=(
            f"The {self.recipient_info['pretitle']} of "
            f"{self.recipient_info['name']} has auto-rejected your "
            f"diplomatic relations request."))
        return

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept_dr(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # ensure that the user has enough diplomatic authority
        if self.recipient_info['pol_auth'] < 1:
            return await interaction.followup.send("You do not have enough Political Authority to accept that request.")
        # change pending status
        await self.conn.execute('''INSERT INTO cnc_drs
                                   VALUES ($1, $2);''',
                                self.interaction.message.id, [self.recipient_info['name'],
                                                              self.sender_info['name']])
        # subtract one diplomatic authority from recipient
        await self.conn.execute('''UPDATE cnc_users
                                   SET pol_auth = pol_auth - 1
                                   WHERE user_id = $1;''',
                                self.recipient_info['user_id'])
        # delete the pending
        await self.conn.execute('''DELETE
                                   FROM cnc_pending_requests
                                   WHERE id = $1;''',
                                self.interaction.message.id)
        # confirm with both parties
        await interaction.followup.send(f"{self.recipient_info['name']} has established diplomatic relations with "
                                        f"{self.sender_info['name']}!")
        # notify sender via DM (with fallback on failure)
        await safe_dm(self.bot, self.sender_info['user_id'], content=(
            f"{self.recipient_info['name']} has accepted "
            f"the request for diplomatic relations from {self.sender_info['name']}!"))
        # close out the buttons
        return await interaction.edit_original_response(view=None)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject_dr(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # delete pending request
        await self.conn.execute('''DELETE
                                   FROM cnc_pending_requests
                                   WHERE id = $1;''', self.interaction.message.id)
        # add political authority back to sender
        await self.conn.execute('''UPDATE cnc_users
                                   SET pol_auth = pol_auth + 1
                                   WHERE user_id = $1;''',
                                self.sender_info['user_id'])
        # notify recipient
        await interaction.followup.send(f"{self.recipient_info['name']} has rejected diplomatic relations with "
                                        f"{self.sender_info['name']}!")
        # notify sender via DM (with fallback on failure)
        await safe_dm(self.bot, self.sender_info['user_id'], content=(
            f"{self.recipient_info['name']} has rejected "
            f"the request for diplomatic relations from {self.sender_info['name']}!"))
        # close out the buttons
        return await interaction.edit_original_response(view=None)


class MilitaryAllianceRespondView(discord.ui.View):

    def __init__(self, interaction: discord.Interaction, conn: asyncpg.Pool, sender_info: asyncpg.Record,
                 recipient_info: asyncpg.Record, dm: discord.Message, bot: discord.Client):
        super().__init__(timeout=86400)
        self.interaction = interaction
        self.conn = conn
        self.sender_info = sender_info
        self.dm = dm
        self.recipient_info = recipient_info
        self.bot = bot

    async def on_timeout(self):
        # disable buttons and update view
        self.stop()
        # send message that the user has failed to react in time
        await self.dm.reply(content="You have failed to reply within 24 hours. The request has been auto-rejected.")
        # send message to the sender that the request has been denied
        sender_user = self.bot.get_user(self.sender_info['user_id'])
        # delete pending request
        await self.conn.execute('''DELETE
                                   FROM cnc_pending_requests
                                   WHERE id = $1;''', self.interaction.message.id)
        return await sender_user.send(
            f"The {self.recipient_info['pretitle']} of "
            f"{self.recipient_info['name']} has auto-rejected your "
            f"military alliance request.")

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept_alliance(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # ensure that the user has enough military authority
        if self.recipient_info['mil_auth'] < 1:
            return await interaction.followup.send("You do not have enough Military Authority to accept that request.")
        # if the sender is already in a military alliance, add the recipient to that alliance
        existing_alliance = await self.conn.execute('''UPDATE cnc_alliances
                                                       SET members = members || $1
                                                       WHERE $2 = ANY (members);''',
                                                    list(self.recipient_info['name']), self.sender_info['name'])
        # if there is no exising alliance, indicated by an UPDATE 0, create a new alliance
        if existing_alliance == "UPDATE 0":
            await self.conn.execute('''INSERT INTO cnc_alliances
                                       VALUES ($1, $2);''',
                                    self.interaction.message.id, [self.recipient_info['name'],
                                                                  self.sender_info['name']])
        # reduce recipient's military authority by one
        await self.conn.execute('''UPDATE cnc_users
                                   SET mil_auth = mil_auth - 1
                                   WHERE user_id = $1;''',
                                self.recipient_info['user_id'])
        # notify recipient
        await interaction.followup.send(f"{self.recipient_info['name']} is now in a military alliance with "
                                        f"{self.sender_info['name']}! ")
        # notify sender
        sender_user = self.bot.get_user(self.sender_info['user_id'])
        await sender_user.send(content=f"{self.recipient_info['name']} has accepted the request to join a "
                                       f"military alliance with {self.sender_info['name']}!")
        # close out buttons
        return await interaction.edit_original_response(view=None)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject_alliance(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # delete pending request
        await self.conn.execute('''DELETE
                                   FROM cnc_pending_requests
                                   WHERE id = $1;''', self.interaction.message.id)
        # add political authority back to sender
        await self.conn.execute('''UPDATE cnc_users
                                   SET mil_auth = mil_auth + 1
                                   WHERE user_id = $1;''',
                                self.sender_info['user_id'])
        # notify recipient
        await interaction.followup.send(f"{self.recipient_info['name']} has rejected a military alliance with "
                                        f"{self.sender_info['name']}!")
        # create sender dm
        sender_user = self.bot.get_user(self.sender_info['user_id'])
        # send sender confirmation
        await sender_user.send(content=f"{self.recipient_info['name']} has rejected "
                                       f"the request for a military alliance from {self.sender_info['name']}!")
        # close out the buttons
        return await interaction.edit_original_response(view=None)


class TradePactRespondView(discord.ui.View):

    def __init__(self, interaction: discord.Interaction, conn: asyncpg.Pool, sender_info: asyncpg.Record,
                 recipient_info: asyncpg.Record, dm: discord.Message, bot: discord.Client):
        super().__init__(timeout=86400)
        self.interaction = interaction
        self.conn = conn
        self.sender_info = sender_info
        self.dm = dm
        self.recipient_info = recipient_info
        self.bot = bot

    async def on_timeout(self):
        # disable buttons and update view
        self.stop()
        # send message that the user has failed to react in time
        await self.dm.reply(content="You have failed to reply within 24 hours. The request has been auto-rejected.")
        # delete pending request
        await self.conn.execute('''DELETE
                                   FROM cnc_pending_requests
                                   WHERE id = $1;''', self.interaction.message.id)
        await safe_dm(self.bot, self.sender_info['user_id'], content=(
            f"The {self.recipient_info['pretitle']} of "
            f"{self.recipient_info['name']} has auto-rejected your "
            f"trade pact offer."))
        return

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept_tp(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # ensure that the user has enough diplomatic authority
        if self.recipient_info['pol_auth'] < 1:
            return await interaction.followup.send("You do not have enough Political Authority to accept that request.")
        # change pending status
        await self.conn.execute('''INSERT INTO cnc_trade_pacts
                                   VALUES ($1, $2);''',
                                self.interaction.message.id, [self.recipient_info['name'],
                                                              self.sender_info['name']])
        # subtract one diplomatic authority from recipient
        await self.conn.execute('''UPDATE cnc_users
                                   SET pol_auth = pol_auth - 1
                                   WHERE user_id = $1;''',
                                self.recipient_info['user_id'])
        # delete the pending
        await self.conn.execute('''DELETE
                                   FROM cnc_pending_requests
                                   WHERE id = $1;''',
                                self.interaction.message.id)
        # confirm with both parties
        await interaction.followup.send(f"{self.recipient_info['name']} has established a trade pact with "
                                        f"{self.sender_info['name']}!")
        # notify sender via DM (with fallback on failure)
        await safe_dm(self.bot, self.sender_info['user_id'], content=(
            f"{self.recipient_info['name']} has accepted "
            f"the offer of a trade pact with {self.sender_info['name']}!"))
        # close out the buttons
        return await interaction.edit_original_response(view=None)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject_tp(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # delete pending request
        await self.conn.execute('''DELETE
                                   FROM cnc_pending_requests
                                   WHERE id = $1;''', self.interaction.message.id)
        # add political authority back to sender
        await self.conn.execute('''UPDATE cnc_users
                                   SET pol_auth = pol_auth + 1
                                   WHERE user_id = $1;''',
                                self.sender_info['user_id'])
        # notify recipient
        await interaction.followup.send(f"{self.recipient_info['name']} has rejected the trade pact offer from "
                                        f"{self.sender_info['name']}!")
        # create sender dm
        sender_user = self.bot.get_user(self.sender_info['user_id'])
        # send sender confirmation
        await sender_user.send(content=f"{self.recipient_info['name']} has rejected "
                                       f"the offer for a trade pact from {self.sender_info['name']}!")
        # close out the buttons
        return await interaction.edit_original_response(view=None)


# === WAR VIEWS ===

class WarDeclarationView(discord.ui.View):

    def __init__(self, interaction: discord.Interaction, conn: asyncpg.Pool,
                 sender_info: asyncpg.Record, recipient_info: asyncpg.Record, bot: discord.Client, cbs: list):
        super().__init__(timeout=180)
        self.interaction = interaction
        # add the dropdown
        cb_options_dropdown = CasusBelliDropdown(interaction, cbs)
        self.add_item(cb_options_dropdown)
        # establish the view
        self.cb_option = None
        # establish the variables
        self.conn = conn
        self.sender_info = sender_info
        self.recipient_info = recipient_info
        self.bot = bot

    async def on_timeout(self):
        # disable the buttons and update the view
        for child in self.children:
            child.disabled = True
        await self.interaction.edit_original_response(view=self)

    @discord.ui.button(label="Declare War!", style=discord.ButtonStyle.danger, emoji="\U0001f525")
    async def declare_war(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # get the cnc channel
        cnc_channel = self.bot.get_channel(927288304301387816)
        # if no option has been selected, send message
        if self.cb_option is None:
            return await interaction.followup.send("You have not selected a Casus Belli!")
        # if an option has been selected, declare the war
        # pull information about the cb type
        cb_info = await self.conn.fetchrow('''SELECT *
                                              FROM cnc_cbs
                                              WHERE name = $1;''', self.cb_option)
        # define variables
        cb_war_goals = cb_info['war_goal']
        cb_prohib_pts = cb_info['prohibited_pts']
        dynamic_war_name_raw = cb_info['dynamic_war_name']
        # build simple attacker/defender name lists for storage
        attackers_names = [self.sender_info['name']]
        defenders_names = [self.recipient_info['name']]
        # pull all defender's allies and add to defenders
        defender_alliances = await self.conn.fetchrow('''SELECT *
                                                         FROM cnc_alliances
                                                         WHERE $1 = ANY (members);''',
                                                      self.recipient_info['name'])
        defenders_names.append(defender_alliances['members'].remove(self.recipient_info['name']))
        # check if the user has already had a war with this nation with this CB and how many
        historic_war_check = await self.conn.fetch('''SELECT *
                                                      FROM cnc_wars
                                                      WHERE primary_attacker = $1
                                                        AND primary_defender = $2
                                                        AND cb = $3;''',
                                                   self.sender_info['name'],
                                                   self.recipient_info['name'],
                                                   self.cb_option)
        # if there is a historic war, check the number of how many it's been
        if historic_war_check:
            # get the number of wars
            number_of_wars = len(historic_war_check)
            # pull the ordinal version
            ordinal_war_number = ordinal_suffix(number_of_wars)
            dynamic_war_name = dynamic_war_name_raw.replace("#", ordinal_war_number).replace("ATTACKER",
                                                                                             self.sender_info[
                                                                                                 'name']).replace(
                "DEFENDER", self.recipient_info['name'])
        # otherwise, it's the first war
        else:
            dynamic_war_name = dynamic_war_name_raw.replace("# ", "").replace("ATTACKER",
                                                                              self.sender_info['name']).replace(
                "DEFENDER", self.recipient_info['name'])
        # add the war to the db
        await self.conn.execute('''INSERT INTO cnc_wars(id, attackers, defenders,
                                                        cb, primary_attacker, primary_defender, name)
                                   VALUES ($1, $2, $3, $4, $5, $6, $7);''',
                                self.interaction.message.id, attackers_names,
                                defenders_names, self.cb_option, self.sender_info['name'], self.recipient_info['name'],
                                dynamic_war_name)
        # create the war embed
        war_embed = discord.Embed(title=f"The {dynamic_war_name}",
                                  description=f"The hounds of war have been released by "
                                              f"{self.sender_info['name']} against {self.recipient_info['name']}!",
                                  color=discord.Color.red())
        war_embed.set_thumbnail(url="https://i.ibb.co/bbxhJtx/Command-Conquest-symbol.png")
        war_embed.add_field(name="Casus Belli", value=self.cb_option, inline=False)
        war_embed.add_field(name="War Goal(s)", value=cb_war_goals)
        war_embed.add_field(name="Prohibited Peace Treaties", value=cb_prohib_pts)
        war_embed.add_field(name="\u200b", value="\u200b")
        war_embed.set_footer(text=f"War ID: {self.interaction.message.id}")
        # notify all parties
        for uid in (self.sender_info['user_id'], self.recipient_info['user_id']):
            await safe_dm(self.bot, uid, embed=war_embed)
        # send the war embed in the public channel
        await cnc_channel.send(embed=war_embed)
        await interaction.followup.send(embed=war_embed)
        # disable the views
        return await self.interaction.edit_original_response(view=None)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.danger)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer interaction
        await interaction.response.defer()
        # return to menu
        diplo_menu = DiplomaticMenuView(self.interaction, self.conn, self.recipient_info)
        await interaction.edit_original_response(view=diplo_menu)


class CasusBelliDropdown(discord.ui.Select):

    def __init__(self, interaction: discord.Interaction, cbs):
        self.interaction = interaction
        # create the options
        cb_options = []
        for cb in cbs:
            cb_options.append(discord.SelectOption(label=cb))
        # define the super
        super().__init__(placeholder="Choose a Casus Belli...", min_values=1, max_values=1,
                         options=cb_options)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.interaction.user.id

    async def callback(self, interaction: discord.Interaction):
        # pull the selected value
        self.view.cb_option = self.values[0]
        # disable and update view
        self.disabled = True
        await self.interaction.edit_original_response(view=self.view)
        return await interaction.response.send_message(f"{self.view.cb_option} Casus Belli selected.", ephemeral=True)


class DefensioBelliView(discord.ui.View):

    def __init__(self, interaction: discord.Interaction, conn: asyncpg.Pool,
                 sender_info: asyncpg.Record, recipient_info: asyncpg.Record,
                 bot: discord.Client, dbs: list, war_id: int):
        super().__init__(timeout=86400)
        self.interaction = interaction
        # add the dropdown
        db_options_dropdown = DefensioBelliDropdown(interaction, dbs, war_id)
        self.add_item(db_options_dropdown)
        # establish the view
        self.db_option = None
        # establish the variables
        self.conn = conn
        self.sender_info = sender_info
        self.recipient_info = recipient_info
        self.bot = bot
        self.war_id = war_id

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.interaction.user.id

    async def on_timeout(self) -> None:
        # disable all the views
        for child in self.children:
            child.disabled = True
        # update the view and send a message
        await self.interaction.edit_original_response(view=self)
        return await self.interaction.followup.send(f"No Defensio Belli selected. "
                                                    f"You may select a Defensio Belli by using the "
                                                    f"`/cnc war id:{self.war_id}` command.")


class DefensioBelliDropdown(discord.ui.Select):

    def __init__(self, interaction: discord.Interaction, dbs: list, war_id: int):
        self.interaction = interaction
        # create the options
        db_options = [discord.SelectOption(label="Status Quo")]
        for db in dbs:
            db_options.append(discord.SelectOption(label=db))
        # define the super
        super().__init__(placeholder="Choose a Defensio Belli...", min_values=1, max_values=1,
                         options=db_options)
        self.war_id = war_id
        self.conn = interaction.client.pool

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.interaction.user.id

    async def callback(self, interaction: discord.Interaction):
        # pull the selected value
        db_option = self.values[0]
        # disable and update view
        self.disabled = True
        await self.interaction.edit_original_response(view=self.view)
        # add the defensio belli
        await self.conn.execute('''UPDATE cnc_wars
                                   SET db = $1
                                   WHERE id = $2;''',
                                db_option, self.war_id)
        return await interaction.response.send_message(f"{db_option} Defensio Belli selected.")


class WarsPaginator(discord.ui.View):

    def __init__(self, interaction, all_wars: asyncpg.Record, wars_embed: discord.Embed):
        self.interaction = interaction
        self.page = 1
        self.all_wars = all_wars
        self.wars_embed = wars_embed
        super().__init__(timeout=300)

    async def on_timeout(self):
        # remove dropdown
        for item in self.children:
            self.remove_item(item)
        return await self.interaction.edit_original_response(view=self)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.blurple, disabled=True, emoji="\u23ea")
    async def back(self, interaction: discord.Interaction, back_button: discord.Button):
        # defer response
        await interaction.response.defer()
        # set forward button on
        self.forward.disabled = False
        # subtract from page
        self.page -= 1
        # page cannot be less than 1
        if self.page <= 1:
            self.page = 1
            back_button.disabled = True
        # count the wars
        start = (self.page - 1) * 10
        end = self.page * 10
        wars_to_display = self.all_wars[start:end]
        # clear the embed
        self.wars_embed.clear_fields()
        # populate the embed with the next set of wars
        for war in wars_to_display:
            # get the list of attackers and defenders, placing the primary first and adding asterisk
            attackers_list = list(war['attackers']) if war['attackers'] is not None else []
            defenders_list = list(war['defenders']) if war['defenders'] is not None else []
            attackers_others = [a for a in attackers_list if a != war['primary_attacker']]
            defenders_others = [d for d in defenders_list if d != war['primary_defender']]
            attackers = ", ".join([f"**{war['primary_attacker']}**"] + attackers_others) if war[
                'primary_attacker'] else ", ".join(attackers_list)
            defenders = ", ".join([f"**{war['primary_defender']}**"] + defenders_others) if war[
                'primary_defender'] else ", ".join(defenders_list)
            self.wars_embed.add_field(name=f"The {war['name']}",
                                      value=f"ID: {war['id']}\n"
                                            f"Attackers: {attackers}\n"
                                            f"Defenders: {defenders}\n"
                                            f"Casus Belli: {war['cb']}\n"
                                            f"Defensio Belli: {war['db'] or 'None'}\n"
                                            f"Turns: {war['turns']}\n"
                                            f"Deaths: {war['deaths']}")
        # update the embed and the view
        return await self.interaction.edit_original_response(embed=self.wars_embed, view=self)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, close: discord.Button):
        # defer response
        await interaction.response.defer()
        # remove all components and close the view
        for item in list(self.children):
            self.remove_item(item)
        return await self.interaction.edit_original_response(view=None)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, emoji="\u23e9")
    async def forward(self, interaction: discord.Interaction, forward_button: discord.Button):
        # defer response
        await interaction.response.defer()
        # enable back button
        self.back.disabled = False
        # add page
        self.page += 1
        # set max
        max_page = math.ceil(len(self.all_wars) / 10) if self.all_wars else 1
        # disable forward on last page
        if self.page >= max_page:
            self.page = max_page
            forward_button.disabled = True
        # count the wars
        start = (self.page - 1) * 10
        end = self.page * 10
        wars_to_display = self.all_wars[start:end]
        # clear the embed
        self.wars_embed.clear_fields()
        # populate the embed with the next set of wars
        for war in wars_to_display:
            # get the list of attackers and defenders, placing the primary first and adding asterisk
            attackers_list = list(war['attackers']) if war['attackers'] is not None else []
            defenders_list = list(war['defenders']) if war['defenders'] is not None else []
            attackers_others = [a for a in attackers_list if a != war['primary_attacker']]
            defenders_others = [d for d in defenders_list if d != war['primary_defender']]
            attackers = ", ".join([f"**{war['primary_attacker']}**"] + attackers_others) if war[
                'primary_attacker'] else ", ".join(attackers_list)
            defenders = ", ".join([f"**{war['primary_defender']}**"] + defenders_others) if war[
                'primary_defender'] else ", ".join(defenders_list)
            self.wars_embed.add_field(name=f"The {war['name']}",
                                      value=f"ID: {war['id']}\n"
                                            f"Attackers: {attackers}\n"
                                            f"Defenders: {defenders}\n"
                                            f"Casus Belli: {war['cb']}\n"
                                            f"Defensio Belli: {war['db'] or 'None'}\n"
                                            f"Turns: {war['turns']}\n"
                                            f"Deaths: {war['deaths']}")
        # update the embed and the view
        return await self.interaction.edit_original_response(embed=self.wars_embed, view=self)


class AllianceWarInvitiation(discord.ui.View):

    def __init__(self, conn: asyncpg.Pool, war_info: asyncpg.Record, attacker: bool,
                 alliance_name: str, sender_info: asyncpg.Record):
        self.war_info = war_info
        self.attacker = attacker
        self.conn = conn
        self.alliance_name = alliance_name
        self.sender_info = sender_info
        super().__init__(timeout=86400)

    async def on_timeout(self):
        # remove dropdown
        for item in self.children:
            self.remove_item(item)
        return await self.interaction.edit_original_response(view=self)

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept_war(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.conn
        # pull user info
        user_info = user_db_info(interaction.user.id, conn)
        # add the user to the correct side
        if self.attacker:
            # if the user is an attacker, add them to the attacker list
            await conn.execute('''UPDATE cnc_wars
                                  SET attackers = array_append(attackers, $1)
                                  WHERE id = $2;''',
                               user_info['name'], self.war_info['id'])
            # dm the attackers notifying them that a new nation has joined on the side of the attackers
            for belligerent in self.war_info['attackers']:
                # get belligerent info
                belligerent_info = await user_db_info(belligerent, conn)
                # pull the user id
                belligerent_id = belligerent_info['user_id']
                # attempt to DM the user
                belligerent_joined_msg = (f"**The {user_info['pretitle']} of {user_info['name']}**, "
                                          f"a member of {self.alliance_name}, has joined our glorious war against "
                                          f"**{self.war_info['primary_defender']}**!")
                await safe_dm(interaction.client, belligerent_id, content=belligerent_joined_msg)
            # get the cnc channel
            cnc_channel = interaction.client.get_channel(927288304301387816)
            # send a message to that channel
            await cnc_channel.send(f"**{user_info['name']}** has joined the {self.war_info['name']} "
                                   f"as an attacker.")
        # if the user is not an attacker, they must be a defender
        else:
            # add them to the defender list
            await conn.execute('''UPDATE cnc_wars
                                  SET defenders = array_append(defenders, $1)
                                  WHERE id = $2;''',
                               user_info['name'], self.war_info['id'])
            # dm the attackers notifying them that a new nation has joined on the side of the attackers
            for belligerent in self.war_info['defenders']:
                # get belligerent info
                belligerent_info = await user_db_info(belligerent, conn)
                # pull the user id
                belligerent_id = belligerent_info['user_id']
                # attempt to DM the user
                belligerent_joined_msg = (f"**The {user_info['pretitle']} of {user_info['name']}**, "
                                          f"a member of {self.alliance_name}, has joined in our valiant defense against"
                                          f"**{self.war_info['primary_attacker']}**!")
                await safe_dm(interaction.client, belligerent_id, content=belligerent_joined_msg)
            # get the cnc channel
            cnc_channel = interaction.client.get_channel(927288304301387816)
            # send a message to that channel
            await cnc_channel.send(f"**{user_info['name']}** has joined the {self.war_info['name']} "
                                   f"as a defender.")
        # update the view with the disabled button
        for child in self.children:
            child.disabled = True
        return await interaction.edit_original_response(view=self)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline_war(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.conn
        # pull user info
        user_info = user_db_info(interaction.user.id, conn)
        # send a message to the primary attacker/defender
        if self.attacker:
            # use safe dm to send them the decline message
            decline_message = (f"**The {user_info['pretitle']} of {user_info['name']}** has declined to join the "
                               f"{self.war_info['name']} against {self.war_info['primary_defender']}.")
            await safe_dm(interaction.client, self.sender_info['id'], content=decline_message)
        else:
            # declining a call to war for a defender automatically ends the military alliance
            pass
        # disable the buttons
        for child in self.children:
            child.disabled = True
        return await interaction.edit_original_message(view=self)


class MilitaryAllianceButton(discord.ui.Button):

    def __init__(self, conn: asyncpg.Pool, war_info: asyncpg.Record, user_info: asyncpg.Record):
        self.conn = conn
        self.war_info = war_info
        self.user_info = user_info
        super().__init__(label="Call Allies to War!", style=discord.ButtonStyle.blurple, emoji="\U0001f6e1")

    async def callback(self, interaction: discord.Interaction):
        # defer the interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.conn
        # define the war info
        war_info = self.war_info
        # check to see if any members of the user's military alliance are not yet in the war
        # pull the alliance information
        alliance_info = await conn.fetchval('''SELECT members
                                               FROM cnc_alliances
                                               WHERE $1 = ANY (members);''',
                                            self.user_info['name'])
        # if the user is the defender, pull the defenders
        if self.user_info['name'] == self.war_info['primary_defender']:
            # get a list of any allied nations that are not in the war
            non_participants = list(set(alliance_info).difference(set(war_info['defenders'])))
            # for each non-participant
            for np in non_participants:
                # get their user object
                ally_user_info = await user_db_info(np, conn)
                # get the name of the alliance or set it as "your alliance"
                alliance_name = alliance_info['name'] or "your alliance"
                # create a small embed about the war
                war_embed = discord.Embed(title=f"The {war_info['name']}", color=discord.Color.red(),
                                          description="An invitation to the following war has been received.")
                # get the list of attackers and defenders, placing the primary first and bolding
                attackers_list = list(war_info['attackers']) if war_info['attackers'] is not None else []
                defenders_list = list(war_info['defenders']) if war_info['defenders'] is not None else []
                attackers_others = [a for a in attackers_list if a != war_info['primary_attacker']]
                defenders_others = [d for d in defenders_list if d != war_info['primary_defender']]
                attackers = ", ".join([f"**{war_info['primary_attacker']}**"] + attackers_others) if war_info[
                    'primary_attacker'] else ", ".join(attackers_list)
                defenders = ", ".join([f"**{war_info['primary_defender']}**"] + defenders_others) if war_info[
                    'primary_defender'] else ", ".join(defenders_list)
                war_embed.add_field(name=f"The {war_info['name']}",
                                    value=f"ID: {war_info['id']}\n"
                                          f"Attackers: {attackers}\n"
                                          f"Defenders: {defenders}\n"
                                          f"Casus Belli: {war_info['cb']}\n"
                                          f"Defensio Belli: {war_info['db'] or 'None'}\n"
                                          f"Turns: {war_info['turns']}\n"
                                          f"Deaths: {war_info['deaths']}")
                # create the accept/decline view
                war_invitation_view = AllianceWarInvitiation(conn=conn, war_info=war_info, attacker=False,
                                                             alliance_name=alliance_name, sender_info=self.user_info)
                # create the content for the message
                war_invitation_message = (f"War has been declared on our ally, {self.user_info['name']}! "
                                          f"They have requested our aid. How shall we respond?")
                # send the DM safely
                await safe_dm(interaction.client, ally_user_info['user_id'], content=war_invitation_message,
                              embed=war_embed, view=war_invitation_view)
        # if the user is not the defender, they must be the attacker
        else:
            # get a list of any allied nations that are not in the war
            non_participants = list(set(alliance_info['members']).difference(set(war_info['attackers'])))
            # for each non-participant
            for np in non_participants:
                # get their user object
                ally_user_info = await user_db_info(np, conn)
                # get the name of the alliance or set it as "your alliance"
                alliance_name = alliance_info['name'] or "your alliance"
                # create a small embed about the war
                war_embed = discord.Embed(title=f"The {war_info['name']}", color=discord.Color.red(),
                                          description="An invitation to the following war has been received.")
                # get the list of attackers and defenders, placing the primary first and bolding
                attackers_list = list(war_info['attackers']) if war_info['attackers'] is not None else []
                defenders_list = list(war_info['defenders']) if war_info['defenders'] is not None else []
                attackers_others = [a for a in attackers_list if a != war_info['primary_attacker']]
                defenders_others = [d for d in defenders_list if d != war_info['primary_defender']]
                attackers = ", ".join([f"**{war_info['primary_attacker']}**"] + attackers_others) if war_info[
                    'primary_attacker'] else ", ".join(attackers_list)
                defenders = ", ".join([f"**{war_info['primary_defender']}**"] + defenders_others) if war_info[
                    'primary_defender'] else ", ".join(defenders_list)
                war_embed.add_field(name=f"The {war_info['name']}",
                                    value=f"ID: {war_info['id']}\n"
                                          f"Attackers: {attackers}\n"
                                          f"Defenders: {defenders}\n"
                                          f"Casus Belli: {war_info['cb']}\n"
                                          f"Defensio Belli: {war_info['db'] or 'None'}\n"
                                          f"Turns: {war_info['turns']}\n"
                                          f"Deaths: {war_info['deaths']}")
                # create the accept/decline view
                war_invitation_view = AllianceWarInvitiation(conn=conn, war_info=war_info, attacker=False,
                                                             alliance_name=alliance_name, sender_info=self.user_info)
                # create the content for the message
                war_invitation_message = (f"War has been declared by our ally, {self.user_info['name']}! "
                                          f"They have requested our aid. How shall we respond?")
                # send the DM safely
                await safe_dm(interaction.client, ally_user_info['user_id'], content=war_invitation_message,
                              embed=war_embed, view=war_invitation_view)
        # disable all the buttons and update the view
        for child in self.view.children:
            child.disabled = True
        return await interaction.edit_original_response(view=self.view)


class DefensioBelliButton(discord.ui.Button):

    def __init__(self, conn: asyncpg.Pool, war_info: asyncpg.Record, user_info: asyncpg.Record):
        self.conn = conn
        self.war_info = war_info
        self.user_info = user_info
        super().__init__(label="Declare a Defensio Belli", style=discord.ButtonStyle.blurple, emoji="\U0001f4dc")

    async def callback(self, interaction: discord.Interaction):
        # defer the interaction
        await interaction.response.defer(thinking=False)
        # establish the connection
        conn = self.conn
        # define user info
        sender_info = self.user_info
        # get recipient info
        recipient_info = await user_db_info(self.war_info['primary_attacker'], conn)
        # get all the options for the defensio belli
        # create a base list of CBs available
        available_dbs = ["Conquest", "Subjugate", "Force Reparations"]
        # check CBs available by tech
        if "Ideological Crusade" in sender_info['tech']:
            available_dbs.append("Indoctrinate")
        if "National Humiliation" in sender_info['tech']:
            available_dbs.append("Humiliate")
        if "Subjugation" in sender_info['tech']:
            # calculate the average national developments of sender and receiver
            sender_dev = await self.conn.fetchval('''SELECT AVG(development)
                                                     FROM cnc_provinces
                                                     WHERE owner_id = $1;''',
                                                  sender_info['id'])
            recipient_dev = await self.conn.fetchval('''SELECT AVG(development)
                                                        FROM cnc_provinces
                                                        WHERE owner_id = $1;''',
                                                     recipient_info['user_id'])
            # if 50% of the senders dev is larger than the recipient's dev, permit subjugation
            if recipient_dev < sender_dev * .5:
                available_dbs.append("Subjugate")
        if "Total War" in sender_info['tech']:
            available_dbs.append("Total War")
        # check to see if the recipient has any puppets
        overlord_check = await self.conn.fetch('''SELECT *
                                                  FROM cnc_users
                                                  WHERE overlord = $1;''', recipient_info['user_id'])
        if overlord_check:
            available_dbs.append("Force Independence")
        # if the recipient is equalist and the sender is not equalist, add the suppression the revolution CB
        if (recipient_info['govt_type'] == "Equalism") and (sender_info['govt_type'] != "Equalism"):
            available_dbs.append("Suppress the Revolution")
        # if the recipient is not equalist and the sender is equalist, add the Spread the Revolution CB
        if (recipient_info['govt_type'] != "Equalism") and (sender_info['govt_type'] == "Equalism"):
            available_dbs.append("Spread the Revolution")
        # create the dbs dropdown view
        db_dropdown_view = DefensioBelliView(interaction=interaction, conn=conn, sender_info=sender_info,
                                             recipient_info=recipient_info, bot=interaction.client, dbs=available_dbs,
                                             war_id=self.war_info['id'])
        # add the dropdown view and disable our button
        await interaction.edit_original_response(view=db_dropdown_view)


class WarOptionsView(discord.ui.View):

    def __init__(self, interaction: discord.Interaction, conn: asyncpg.Pool, war_info: asyncpg.Record,
                 alliance_button: bool, db_button: bool, user_info: asyncpg.Record, war_embed: discord.Embed):
        super().__init__(timeout=180)
        self.interaction = interaction
        self.conn = conn
        self.war_info = war_info
        self.user_info = user_info
        self.war_embed = war_embed
        # add military alliance button
        if alliance_button:
            self.add_item(MilitaryAllianceButton(conn=self.conn, war_info=self.war_info, user_info=self.user_info))
        if db_button:
            self.add_item(DefensioBelliButton(conn=self.conn, war_info=self.war_info, user_info=self.user_info))

    async def on_timeout(self):
        # remove dropdown
        for item in self.children:
            self.remove_item(item)
        # delete the view and update with the war embed
        await self.interaction.edit_original_response(view=None)
        return await self.interaction.edit_original_response(embed=self.war_embed)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.interaction.user.id

    @discord.ui.button(label="Sue for Peace", style=discord.ButtonStyle.success, emoji="\U0001f54a")
    async def peace_negotiation(self, interaction: discord.Interaction, button: discord.Button):
        # defer the interaction
        await interaction.response.defer(thinking=False)
        # establish the connection
        conn = self.conn
        # establish other variables
        war_info = self.war_info
        user_info = self.user_info
        # check if a peace negotiation is pending
        pending_peace_negotiation = await conn.fetchrow('''SELECT *
                                                           FROM cnc_peace_negotiations
                                                           WHERE war_id = $1;''',
                                                        war_info['id'])
        # if there is a pending negotiation, return
        if pending_peace_negotiation is not None:
            for child in self.children:
                child.disabled = True
            await interaction.edit_original_response(view=self)
            return await interaction.followup.send("A peace negotiation is already pending for this war.")
        # create the negotiation embed
        peace_embed = discord.Embed(title=f"Peace Negotiations for the {war_info['name']}", color=discord.Color.red(),
                                    description="Peace negotiations have begun between the belligerents of this war.")
        # add the details of the proposal
        peace_embed.add_field(name="Proposed by",
                              value=f"The {user_info['pretitle']} of {user_info['name']}",
                              inline=False)
        peace_embed.add_field(name="War Score",
                              value=f"(A) {war_info['war_score'][0]} \U00002694 {war_info['war_score'][1]} (D)",
                              inline=False)
        # get the list of attackers and defenders, placing the primary first bolding
        attackers_list = list(war_info['attackers']) if war_info['attackers'] is not None else []
        defenders_list = list(war_info['defenders']) if war_info['defenders'] is not None else []
        attackers_others = [a for a in attackers_list if a != war_info['primary_attacker']]
        defenders_others = [d for d in defenders_list if d != war_info['primary_defender']]
        attackers = ", ".join([f"**{war_info['primary_attacker']}**"] + attackers_others) if war_info[
            'primary_attacker'] else ", ".join(attackers_list)
        defenders = ", ".join([f"**{war_info['primary_defender']}**"] + defenders_others) if war_info[
            'primary_defender'] else ", ".join(attackers_list)
        peace_embed.add_field(name="Aggressor(s)",
                              value=attackers,
                              inline=False)
        peace_embed.add_field(name="Defender(s)",
                              value=defenders,
                              inline=False)
        peace_embed.add_field(name="Information",
                              value=f"*Turns*: {war_info['turns']}\n"
                                    f"*Deaths*: {war_info['deaths']}\n"
                                    f"*Casus Belli*: {war_info['cb']}\n"
                                    f"*Defensio Belli*: {war_info['db'] or 'None'}")
        peace_embed.set_footer(text="Use the dropdown below to begin negotiations.",
                               icon_url="https://i.ibb.co/CKScCw9P/Command-Conquest-symbol-circular.png")
        # send the embed
        await self.interaction.edit_original_response(embed=peace_embed)
        # select any peace negotiation options
        peace_treaty_options = [
            "White Peace",
            "Cede Province",
            "Give Province",
            "Demand Reparations",
            "End Embargo",
            "End Military Alliance",
            "End Trade Pacts",
            "Subjugate",
            "End Overlordship",
            "Dismantle",
            "Force Government Type",
            "Humiliate"
        ]

        # create modal input function
        async def demanding_provinces_wait_for_modal(parent_interaction: discord.Interaction, title: str, label: str):
            """
            Waits for user input via a modal interaction and returns the value entered by the user.

            This asynchronous function creates a custom modal dialog using a specific
            title and label for the text input. It sends the modal to the user and waits
            for their interaction. The user's input is captured and returned.

            Parameters:
                parent_interaction (discord.Interaction): The interaction object representing
                    the initial interaction to which the modal is a response. MUST BE A RESPONSE, NOT FOLLOWUP.
                title (str): The title of the modal to be displayed to the user.
                label (str): The label for the text input field inside the modal.

            Returns:
                str | None: The value entered by the user in the modal's input field,
                or None if the modal times out or no value is provided.
            """

            class ProvinceInputModal(discord.ui.Modal):
                def __init__(self):
                    super().__init__(title=title, timeout=60)
                    # define and add the text input
                    self.demand_input = discord.ui.TextInput(label=label, style=discord.TextStyle.short, required=True)
                    self.add_item(self.demand_input)
                    # define variables
                    self.value = None
                    self.parent_interaction = parent_interaction

                async def on_submit(self, submit_interaction: Interaction):
                    # defer the interaction
                    await submit_interaction.response.defer(thinking=False)
                    # define the value and stop listening to the modal
                    self.value = self.demand_input.value
                    self.stop()

                async def on_timeout(self):
                    # if the user fails to respond, stop listening
                    # and remove all the options from the original interaction message, effectively canceling
                    self.stop()
                    # if the user gives no response or cancels
                    await conn.execute('''DELETE
                                          FROM cnc_peace_negotiations
                                          WHERE war_id = $1;''', war_info['id'])
                    # remove the view
                    return await parent_interaction.edit_original_response(view=None)

            # create and send the modal
            modal = ProvinceInputModal()
            await parent_interaction.response.send_modal(modal)
            # await the modal response
            await modal.wait()
            # return the value
            return modal.value

        # define total negotiations
        total_negotiation = False

        # if the user is using a cb (attacker), then search for the cb prohibited options for that cb
        if user_info['name'] in war_info['attackers']:
            # define the target of the negotiation, defaulting to the primary attacker
            target = war_info['primary_defender']
            # define the target war score
            target_war_score = war_info['war_score'][1]
            # if the war has multiple belligerents on the opposing side, the proposer may select which one to target
            if len(attackers_list) > 1:
                # add the "General Peace" to the list as a whole option
                attackers_list = ["General Peace"] + attackers_list

                # create view check to ensure proper parsing
                def target_check(inter: discord.Interaction):
                    # Ensure it's the same message & same user
                    return (
                            inter.user == self.interaction.user
                            and inter.data['custom_id'] == "target_dropdown"
                    )

                # create a view for the dropdown and add it
                peace_target_view = discord.ui.View()
                peace_target_view.add_item(PeaceNegotiationTargetsDropdown(attackers_list))
                # add a cancel button to the view
                cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)

                async def cancel_button_callback(interaction: discord.Interaction, view: discord.ui.View):
                    await interaction.response.defer()
                    for child in view.children:
                        child.disabled = True
                    return await self.interaction.edit_original_response(view=peace_negotiation_dropdown_view)

                cancel_button.callback = cancel_button_callback
                peace_target_view.add_item(cancel_button)
                # add the view to the embed
                await self.interaction.edit_original_response(view=peace_target_view)

                # wait for the options to be selected
                try:
                    target_returned = await interaction.client.wait_for("interaction", check=target_check,
                                                                        timeout=120)
                    await target_returned.response.defer()
                except asyncio.TimeoutError:
                    # return and remove the view if the user does not interact
                    return await self.interaction.edit_original_response(view=None)

                # if the target is "General Peace", keep the target at the default
                if target_returned.data['values'][0] == "General Peace":
                    target = target
                    total_negotiation = True
                else:
                    target = target_returned.data['values'][0]
            # if there is only one possible target, the total negotiation should be true
            else:
                total_negotiation = True
            # get target data
            target_info = await user_db_info(target, conn)
            # pull cb info
            cb_info = await conn.fetchrow('''SELECT *
                                             FROM cnc_cbs
                                             WHERE name = $1;''', war_info['cb'])
            # remove prohibited targets
            for prohibited_pt in cb_info['prohibited_pts']:
                peace_treaty_options.remove(prohibited_pt)

        # otherwise, they are defender
        else:
            # define the target of the negotiation, defaulting to the primary attacker
            target = war_info['primary_attacker']
            # define the target war score
            target_war_score = war_info['war_score'][0]
            # if the war has multiple belligerents on the opposing side, the proposer may select which one to target
            if len(attackers_list) > 1:
                # add the "General Peace" to the list as a whole option
                attackers_list = ["General Peace"] + attackers_list

                # create view check to ensure proper parsing
                def target_check(inter: discord.Interaction):
                    # Ensure it's the same message & same user
                    return (
                            inter.user == self.interaction.user
                            and inter.data['custom_id'] == "target_dropdown"
                    )

                # create a view for the dropdown and add it
                peace_target_view = discord.ui.View()
                peace_target_view.add_item(PeaceNegotiationTargetsDropdown(attackers_list))
                # add a cancel button to the view
                cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)

                async def cancel_button_callback(interaction: discord.Interaction, view: discord.ui.View):
                    await interaction.response.defer()
                    for child in view.children:
                        child.disabled = True
                    return await self.interaction.edit_original_response(view=peace_negotiation_dropdown_view)

                cancel_button.callback = cancel_button_callback
                peace_target_view.add_item(cancel_button)
                # add the view to the embed
                await self.interaction.edit_original_response(view=peace_target_view)

                # wait for the options to be selected
                try:
                    target_returned = await interaction.client.wait_for("interaction", check=target_check,
                                                                        timeout=120)
                    await target_returned.response.defer()
                except asyncio.TimeoutError:
                    # return and remove the view if the user does not interact
                    return await self.interaction.edit_original_response(view=None)

                # if the target is "General Peace", keep the target at the default
                if target_returned.data['values'][0] == "General Peace":
                    target = target
                    total_negotiation = True
                else:
                    target = target_returned.data['values'][0]
            # if there is only one possible target, the total negotiation should be true
            else:
                total_negotiation = True
            # get target data
            target_info = await user_db_info(target, conn)
            # if there is no db, only white peace is an option
            if war_info['db'] is None:
                peace_treaty_options = ["White Peace"]
            # if the db is status quo, also only permit white peace
            elif war_info['db'] == "Status Quo":
                peace_treaty_options = ["White Peace"]
            # if the db is anything else, proceed
            else:
                # pull db info
                db_info = await conn.fetchrow('''SELECT *
                                                 FROM cnc_cbs
                                                 WHERE name = $1;''', war_info['db'])
                # remove prohibited targets
                for prohibited_pt in db_info['prohibited_pts']:
                    peace_treaty_options.remove(prohibited_pt)

        # create view check to ensure proper parsing
        def pnd_check(inter: discord.Interaction):
            """
            This function ensures that the user ID of the interaction input is the same as the parent interaction user.
            """
            # Ensure it's the same message & same user
            return (
                    inter.user == self.interaction.user
                    and inter.data['custom_id'] == "peace_treaty_negotiations_dropdown"
            )

        # create and add the view
        peace_negotiation_dropdown_view = discord.ui.View()
        peace_negotiation_dropdown_view.add_item(PeaceNegotiationOptionsDropdown(peace_treaty_options))
        # add a cancel button to the view
        cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)

        async def cancel_button_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            for child in peace_negotiation_dropdown_view.children:
                child.disabled = True
            # destroy any pending negotiation
            await conn.execute('''DELETE
                                  FROM cnc_peace_negotiations
                                  WHERE war_id = $1;''', war_info['id'])
            return await self.interaction.edit_original_response(view=peace_negotiation_dropdown_view)

        cancel_button.callback = cancel_button_callback
        peace_negotiation_dropdown_view.add_item(cancel_button)
        # update the original message with the embed and the view
        await self.interaction.edit_original_response(embed=peace_embed, view=peace_negotiation_dropdown_view)

        # wait for the options to be selected
        try:
            negotiation_demands = await interaction.client.wait_for("interaction", check=pnd_check,
                                                                          timeout=120)
            await negotiation_demands.response.send_message("Processing...", ephemeral=True, delete_after=1)
        except asyncio.TimeoutError:
            # destroy any pending negotiation
            await conn.execute('''DELETE
                                  FROM cnc_peace_negotiations
                                  WHERE war_id = $1;''', war_info['id'])
            # return and remove the view if the user does not interact
            return await self.interaction.edit_original_response(view=None)

        # parse the options
        negotiation_demands = negotiation_demands.data['values']
        # define the demand score
        total_war_score = 0
        # define white peace
        white_peace = False
        # send the updated embed
        await self.interaction.edit_original_response(embed=peace_embed)
        # create the pending peace negotiation
        await conn.execute('''INSERT INTO cnc_peace_negotiations(war_id, total_negotiation, sender, target)
                              VALUES ($1, $2, $3, $4);''',
                           war_info['id'], total_negotiation, user_info['name'], target)
        # parse out the demands and handle each
        for demand in negotiation_demands:
            # get the provinces owned by the target
            target_provinces_raw = await conn.fetch('''SELECT *
                                                       FROM cnc_provinces
                                                       WHERE owner_id = $1;''',
                                                    target_info['user_id'])
            target_provinces = [p['id'] for p in target_provinces_raw]

            # if the demand is white peace, immediately break
            if demand == "White Peace":
                # update the pending peace negotiation
                await conn.execute('''UPDATE cnc_peace_negotiations
                                      SET white_peace = True
                                      WHERE war_id = $1;''',
                                   war_info['id'])
                # update the embed
                peace_embed.add_field(name="White Peace", value="Offered", inline=False)
                # send the updated embed
                await self.interaction.edit_original_response(embed=peace_embed)
                # return and remove the view if the user does not interact
                await self.interaction.followup.send("White Peace has been offered. No other demands can be made.")
                # break the cycle and do not process any other demands
                white_peace = True
                break

            # if the demand is to cede a province, determine which provinces the demander claims
            elif demand == "Cede Province":
                # query demand for provinces using the peace options dropdown interaction response
                provinces_demanded = await demanding_provinces_wait_for_modal(negotiation_demands,
                                                                              "Demand Provinces",
                                                                              "List province IDs separated by comma:")
                # separate the list
                provinces_demanded = [int(p.strip()) for p in provinces_demanded.split(',')]
                # if the list has no items (somehow?), return
                if not provinces_demanded:
                    # reject message
                    await self.interaction.followup.send("You must specify at least one province.", ephemeral=True)
                    # skip this option
                    continue
                # if the list has items, proceed
                else:
                    # if the list of provinces demanded has any provinces that are not owned by the target
                    if not set(provinces_demanded).issubset(set(target_provinces)):
                        # get the provinces that are not
                        provinces_not_of_target: set[int] = set(set(provinces_demanded) - set(target_provinces))
                        # send a message of denial
                        await self.interaction.followup.send(
                            "You must specify provinces that are owned by the target.\n"
                            f"Target does not own: "
                            f"{(', '.join(map(str, sorted(provinces_not_of_target))))}.",
                            ephemeral=True)
                        # skip this option
                        continue
                    else:
                        # calculate the war score
                        war_score = 0
                        for province in provinces_demanded:
                            # pull the province info
                            p_dev = await conn.fetchval('''SELECT development
                                                           FROM cnc_provinces
                                                           WHERE id = $1;''', province)
                            # calculate demand score as dev * .5
                            war_score = p_dev * .5
                        # ensure the war score is a round number
                        war_score = int(war_score)
                        # otherwise, add the list of provinces to the tracker
                        await conn.execute('''UPDATE cnc_peace_negotiations
                                              SET cede_provinces = cede_provinces || $1,
                                                  war_score_cost = war_score_cost + $2
                                              WHERE war_id = $3;''',
                                           provinces_demanded, war_score, war_info['id'])
                        await self.interaction.followup.send(f"Cede Provinces demand added to the Peace Negotiations "
                                                             f"for `{war_score}` War Score for the following provinces:\n" +
                                                             ", ".join(map(str, provinces_demanded)))
                        # add to the total war score
                        total_war_score += war_score
                        # add to the embed
                        peace_embed.add_field(name="Cede Provinces", value=", ".join(map(str, provinces_demanded)),
                                              inline=False)
                        continue

            # if the demand is to give provinces, determine which ally the provinces will go to and which provinces those are
            elif demand == "Give Province":
                # pull all the allies of the target if they are the attacker
                if user_info['name'] in war_info['attackers']:
                    potential_ally_targets = war_info['attackers'].remove(user_info['name'])
                # pull all the allies of the target if they are the defender
                else:
                    potential_ally_targets = war_info['defenders'].remove(user_info['name'])
                # if the list is empty, skip this option
                if not potential_ally_targets:
                    await self.interaction.followup.send("No potential allies to give provinces to.", ephemeral=True)
                    continue
                # otherwise, proceed
                else:
                    # create view check to ensure proper parsing
                    def gp_target_check(inter: discord.Interaction):
                        # Ensure it's the same message & same user
                        return (
                                inter.user == self.interaction.user
                                and inter.data['custom_id'] == "target_dropdown"
                        )

                    # create the view and dropdown to select the ally
                    ally_select_view = discord.ui.View()
                    ally_select_view.add_item(PeaceNegotiationGiveProvincesDropdown(potential_ally_targets))
                    # create and add the cancel button
                    cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)

                    async def cancel_button_callback(interaction: discord.Interaction):
                        await interaction.response.defer()
                        # destroy the pending negotiation
                        await conn.execute('''DELETE
                                              FROM cnc_peace_negotiations
                                              WHERE war_id = $1;''', war_info['id'])
                        for child in peace_negotiation_dropdown_view.children:
                            child.disabled = True
                        return await self.interaction.edit_original_response(view=peace_negotiation_dropdown_view)

                    cancel_button.callback = cancel_button_callback
                    ally_select_view.add_item(cancel_button)
                    # update the original message with the embed and the view
                    await self.interaction.edit_original_response(view=ally_select_view)

                    # wait for the ally to be selected
                    try:
                        target_returned = await interaction.client.wait_for("interaction",
                                                                            check=gp_target_check,
                                                                            timeout=120)
                        await target_returned.response.defer()
                    except asyncio.TimeoutError:
                        # destroy the pending negotiation
                        await conn.execute('''DELETE
                                              FROM cnc_peace_negotiations
                                              WHERE war_id = $1;''', war_info['id'])
                        # return and remove the view if the user does not interact
                        return await self.interaction.edit_original_response(view=None)

                    # define target option
                    ally_target = target_returned.data['values'][0]
                    # with the target defined, create the text modal to get the provinces demanded
                    provinces_demanded = await demanding_provinces_wait_for_modal(target_returned,
                                                                                  title=f"Give Provinces to {ally_target}",
                                                                                  label="List province IDs separated by comma:")
                    # separate the list
                    provinces_demanded = [int(p.strip()) for p in provinces_demanded.split(',')]
                    # if the list has no items, return
                    if not provinces_demanded:
                        # send a message of denial
                        await self.interaction.followup.send("You must specify at least one province.", ephemeral=True)
                        # skip this option
                        continue
                    # if the list has items, proceed
                    else:
                        # if the list of provinces demanded has any province that are not owned by the target
                        if not set(provinces_demanded).issubset(set(target_provinces)):
                            # get the provinces that are not
                            provinces_not_of_target: set[int] = set(provinces_demanded) - set(target_provinces)
                            # send a message of denial
                            await self.interaction.followup.send(
                                "You must specify provinces that are owned by the target.\n"
                                f"Target does not own: "
                                f"{(', '.join(map(str, sorted(provinces_not_of_target))))}.",
                                ephemeral=True)
                            # skip this option
                            continue
                        else:
                            # calculate war score
                            war_score = 0
                            for province in provinces_demanded:
                                p_dev = await conn.fetchval('''SELECT development
                                                               FROM cnc_provinces
                                                               WHERE id = $1;''', province)
                                war_score += p_dev * 1
                            # ensure the war score is a round number
                            war_score = int(war_score)
                            # update negotiation
                            await conn.execute('''UPDATE cnc_peace_negotiations
                                                  SET give_provinces = hstore($1, $2),
                                                      war_score_cost = war_score_cost + $3
                                                  WHERE war_id = $4;''',
                                               ally_target, ",".join(map(str, provinces_demanded)),
                                               war_score, war_info['id'])
                            # notify of success
                            await self.interaction.followup.send("Give Provinces demand added to the Peace Negotiations"
                                                                 f"at a cost of `{war_score}` War Score for the "
                                                                 f"following provinces:\n"
                                                                 ", ".join(map(str, provinces_demanded)))
                            # add to the total war score
                            total_war_score += war_score
                            # add to the embed
                            peace_embed.add_field(name="Cede Provinces", value=", ".join(map(str, provinces_demanded)),
                                                  inline=False)
                            continue

            # if the demand is to give reparations, determine which authority will be taken and how much
            elif demand == "Demand Reparations":
                # create the auth demand view
                auth_demand_view = AuthDemandView(self.interaction, conn, war_info)
                # remove the view and send the new one
                await self.interaction.edit_original_response(view=None)
                await self.interaction.edit_original_response(view=auth_demand_view)
                # wait
                await auth_demand_view.wait()
                # if the user cancels
                if auth_demand_view.cancelled:
                    return
                else:
                    # update embed
                    peace_embed.add_field(name="Reparations Demanded",
                                          value=f"{auth_demand_view.mil_authority} Military\n"
                                                f"{auth_demand_view.econ_authority} Economic\n"
                                                f"{auth_demand_view.diplo_authority} Diplomatic\n",
                                          inline=False)
                    await self.interaction.edit_original_response(embed=peace_embed, view=None)
                    # add to total
                    total_war_score += auth_demand_view.war_score

            # if the demand is to end embargo
            elif demand == "End Embargo":
                # pull all potential targets
                all_targets = await conn.fetch('''SELECT *
                                                  FROM cnc_embargoes
                                                  WHERE sender = $1;''',
                                               target_info['name'])
                # if it's empty, don't bother
                if not all_targets:
                    # send a message
                    await self.interaction.followup.send("No embargoes to end.", ephemeral=True)
                    continue
                # otherwise, carry on
                else:
                    # query who is the target
                    class EndEmbargoTargetDropdown(discord.ui.Select):

                        # hypersimplistic dropdown
                        def __init__(self):
                            # create the options
                            nation_options = []
                            for n in all_targets:
                                nation_options.append(discord.SelectOption(label=n['name']))
                            # define the super
                            super().__init__(placeholder="Choose End Embargo Target(s)...", min_values=1,
                                             max_values=len(nation_options),
                                             options=nation_options, custom_id="endembargodropdown")

                    # create a view
                    end_overlord_view = discord.ui.View(timeout=120)
                    # add the dropdown
                    end_overlord_view.add_item(EndEmbargoTargetDropdown())
                    # add the cancel button
                    cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)
                    # define the cancel callback
                    cancel_button.callback = cancel_button_callback(self.interaction)
                    # add the cancel button to the view
                    end_overlord_view.add_item(cancel_button)

                    # send the view
                    await self.interaction.edit_original_response(view=end_overlord_view)

                    # create view check to ensure proper parsing
                    def embargo_check(inter: discord.Interaction):
                        """
                        This function ensures that the user ID of the interaction input is the same as the parent interaction user.
                        """
                        # Ensure it's the same message & same user
                        return (
                                inter.user == self.interaction.user
                                and inter.data['custom_id'] == "endembargodropdown"
                        )

                    # wait for the options to be selected
                    try:
                        embargo_targets_returned = await interaction.client.wait_for("interaction",
                                                                                      check=embargo_check,
                                                                                      timeout=120)
                    except asyncio.TimeoutError:
                        # destroy any pending negotiation
                        await conn.execute('''DELETE
                                              FROM cnc_peace_negotiations
                                              WHERE war_id = $1;''', war_info['id'])
                        # return and remove the view if the user does not interact
                        return await self.interaction.edit_original_response(view=None)
                    # parse the results
                    end_embargo_targets = embargo_targets_returned.data['values']
                    # calculate war score
                    war_score = len(end_embargo_targets) * 10
                    # add the embargo releases to the negotiation
                    await conn.execute('''UPDATE cnc_peace_negotiations
                                          SET end_embargo    = $1,
                                              war_score_cost = war_score_cost + $2
                                          WHERE war_id = $3;''',
                                       end_embargo_targets, war_score, war_info['id'])
                    # update embed
                    peace_embed.add_field(name="End Embargo(s)", value=', '.join(end_embargo_targets), inline=False)
                    # send notification
                    await self.interaction.followup.send(f"End Embargo against `{', '.join(end_embargo_targets)}`"
                                                         f" has been added at a cost of `{war_score}` war score.")
                    # add to total
                    total_war_score += war_score
                    continue

            # if the demand is to end a military alliance
            elif demand == "End Military Alliance":
                # check to see if target is in a military alliance
                target_alliance = await conn.fetchrow('''SELECT *
                                                         FROM cnc_alliances
                                                         WHERE $1 = ANY (members);''',
                                                      target_info['name'])
                # if they aren't in one, skip
                if not target_alliance:
                    # send a message
                    await self.interaction.followup.send(f"{target_info['name']} is not a member of any "
                                                         f"military alliances.", ephemeral=True)
                    continue
                # otherwise, carry on
                else:
                    # calculate war score
                    war_score = 15
                    # update the peace negotiation
                    await conn.execute('''UPDATE cnc_peace_negotiations
                                          SET end_ma         = $1,
                                              war_score_cost = war_score_cost + $2
                                          WHERE war_id = $3;''',
                                       target_alliance['id'], war_score, war_info['id'])
                    # update the embed
                    peace_embed.add_field(name="End Military Alliance", value="Demanded", inline=False)
                    # send notification
                    await self.interaction.followup.send(f"Demand for the end of any Military Alliance with "
                                                         f"{target_info['name']} added for `15` War Score.")
                    # add total war score
                    total_war_score += war_score
                    continue

            # if the demand is to end a trade pact
            elif demand == "End Trade Pacts":
                # check to see if target is in a trade pact
                target_pact = await conn.fetchrow('''SELECT *
                                                     FROM cnc_trade_pacts
                                                     WHERE $1 = ANY (members);''',
                                                  target_info['name'])
                # if they aren't in one, skip
                if not target_pact:
                    # send a message
                    await self.interaction.followup.send(f"{target_info['name']} is not a member of any "
                                                         f"Trade Pacts.", ephemeral=True)
                    continue
                # otherwise, carry on
                else:
                    # calculate war score
                    war_score = 20
                    # update the peace negotiation
                    await conn.execute('''UPDATE cnc_peace_negotiations
                                          SET end_tp         = True,
                                              war_score_cost = war_score_cost + $1
                                          WHERE war_id = $2;''', war_score, war_info['id'])
                    # update the embed
                    peace_embed.add_field(name="End Trade Pacts", value="Demanded", inline=False)
                    # send notification
                    await self.interaction.followup.send(f"Demand for the end of any Trade Pact with "
                                                         f"{target_info['name']} added for `20` War Score.")
                    # add total war score
                    total_war_score += war_score
                    continue

            # if the demand is subjugation
            elif demand == "Subjugate":
                # check if the target already has an overlord
                if target_info['overlord']:
                    # send a message
                    await self.interaction.followup.send(f"{target_info['name']} already has an Overlord.",
                                                         ephemeral=True)
                    continue
                # check to see if the user has a puppet slot
                puppets_check = await conn.fetch('''SELECT *
                                                    FROM cnc_users
                                                    WHERE overlord = $1;''',
                                                 user_info['user_id'])
                # if the user has 2 puppets (3 if GP), then reject
                if len(puppets_check) >= 2:
                    # if the user is a GP, they can have 3
                    if not user_info['gp']:
                        # reject
                        await self.interaction.followup.send("Nations cannot have more than 2 puppets.", ephemeral=True)
                        # skip this option
                        continue
                    elif (user_info['gp']) and (len(puppets_check) >= 3):
                        # reject
                        await self.interaction.followup.send("Great Powers cannot have more than 3 puppets.",
                                                             ephemeral=True)
                        # skip this option
                        continue
                # otherwise, carry on
                else:
                    # fetch the total development of the target
                    target_total_development = await conn.fetchval('''SELECT SUM(development)
                                                                      FROM cnc_provinces
                                                                      WHERE owner_id = $1;''',
                                                                   target_info['user_id'])
                    # calculate war score
                    war_score = max(2 * target_total_development, 25)
                    # if the war score for this option is less than 25, set at
                    # update the peace negotiation
                    await conn.execute('''UPDATE cnc_peace_negotiations
                                          SET subjugate      = True,
                                              war_score_cost = war_score_cost + $1
                                          WHERE war_id = $2;''', war_score, war_info['id'])
                    # update the embed
                    peace_embed.add_field(name="Subjugate", value="Demanded", inline=False)
                    # send the notification
                    await self.interaction.followup.send(f"Demand for Subjugation of {target_info['name']} added for "
                                                         f"`{war_score}` War Score.")
                    # add total war score
                    total_war_score += war_score
                    continue

            # if the demand is release subject
            elif demand == "End Overlordship":
                # check if the target already is an overlord
                overlord_list = await conn.fetch('''SELECT *
                                                    FROM cnc_users
                                                    WHERE overlord = $1;''',
                                                 target_info['user_id'])
                # if the target is not the overlord of anyone
                if not overlord_list:
                    # send a message
                    await self.interaction.followup.send(f"{target_info['name']} is not an Overlord.",
                                                         ephemeral=True)
                    continue
                # otherwise, carry on
                else:
                    # query who is the target
                    class EndOverlordTargetDropdown(discord.ui.Select):

                        # hypersimplistic dropdown
                        def __init__(self):
                            # create the options
                            nation_options = []
                            for n in overlord_list:
                                nation_options.append(discord.SelectOption(label=n['name']))
                            # define the super
                            super().__init__(placeholder="Choose End Overlordship Target(s)...", min_values=1,
                                             max_values=len(nation_options),
                                             options=nation_options, custom_id="endoverlorddropdown")

                    # create a view
                    end_overlord_view = discord.ui.View(timeout=120)
                    # add the dropdown
                    end_overlord_view.add_item(EndOverlordTargetDropdown())
                    # add the cancel button
                    cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)
                    # define the cancel callback
                    cancel_button.callback = cancel_button_callback(self.interaction)
                    # add the cancel button to the view
                    end_overlord_view.add_item(cancel_button)

                    # send the view
                    await self.interaction.edit_original_response(view=end_overlord_view)

                    # create view check to ensure proper parsing
                    def overlord_check(inter: discord.Interaction):
                        """
                        This function ensures that the user ID of the interaction input is the same as the parent interaction user.
                        """
                        # Ensure it's the same message & same user
                        return (
                                inter.user == self.interaction.user
                                and inter.data['custom_id'] == "endoverlorddropdown"
                        )

                    # wait for the options to be selected
                    try:
                        negotiation_demands = await interaction.client.wait_for("interaction",
                                                                                      check=overlord_check,
                                                                                      timeout=120)
                    except asyncio.TimeoutError:
                        # destroy any pending negotiation
                        await conn.execute('''DELETE
                                              FROM cnc_peace_negotiations
                                              WHERE war_id = $1;''', war_info['id'])
                        # return and remove the view if the user does not interact
                        return await self.interaction.edit_original_response(view=None)
                    # parse the results
                    end_overlord_targets = negotiation_demands.data['values']
                    # calculate war score
                    war_score = len(end_overlord_targets) * 20
                    # add the embargo releases to the negotiation
                    await conn.execute('''UPDATE cnc_peace_negotiations
                                          SET end_overlord   = $1,
                                              war_score_cost = war_score_cost + $2
                                          WHERE war_id = $3;''',
                                       end_overlord_targets, war_score, war_info['id'])
                    # update embed
                    peace_embed.add_field(name="End Overlordship", value=', '.join(end_overlord_targets), inline=False)
                    # send notification
                    await self.interaction.followup.send(f"Demand to End the Overlordship of {target_info['name']} over"
                                                         f" {', '.join(end_overlord_targets)} added for "
                                                         f"`{war_score}` War Score.")
                    # add total war score
                    total_war_score += war_score
                    # proceed
                    continue

            # if the demand is Force Government Type
            elif demand == "Force Government Type":
                # check if the target's government type is already the same
                if target_info['govt_type'] == user_info['govt_type']:
                    # send a message
                    await self.interaction.followup.send(f"{target_info['name']}'s government type is already "
                                                         f"{user_info['govt_type']}.", ephemeral=True)
                    # skip this option
                    continue
                # otherwise, carry on
                else:
                    # calculate war score
                    war_score = 50
                    # update the peace negotiation
                    await conn.execute('''UPDATE cnc_peace_negotiations
                                          SET force_govt     = $1,
                                              war_score_cost = war_score_cost + $2
                                          WHERE war_id = $3;''',
                                       user_info['govt_type'], war_score, war_info['id'])
                    # update the embed
                    peace_embed.add_field(name="Force Government Type", value="Demanded", inline=False)
                    # send notification
                    await self.interaction.followup.send(f"Demand for {target_info['name']} to be forced into the"
                                                         f"{user_info['govt_type']} Government Type added for "
                                                         f"`{war_score}` War Score.")
                    # add the total war score
                    total_war_score += war_score
                    # proceed
                    continue

            # if the demand is humiliate
            elif demand == "Humiliate":
                # calculate the war score
                war_score = 75
                # update the peace negotiation
                await conn.execute('''UPDATE cnc_peace_negotiations
                                      SET humiliate      = True,
                                          war_score_cost = war_score_cost + $1
                                      WHERE war_id = $2;''', war_score, war_info['id'])
                # update the embed
                peace_embed.add_field(name="Humiliate", value="Demanded", inline=False)
                # add the total war score
                total_war_score += war_score
                # send notification
                await self.interaction.followup.send(f"Demand for the Humiliation of {target_info['name']} added for "
                                                     f"{war_score} War Score.")
                # proceed
                continue

            # if the demand is dismantle
            elif demand == "Dismantle":
                # calculate the war score
                war_score = 90
                # update the peace negotiation
                await conn.execute('''UPDATE cnc_peace_negotiations
                                      SET dismantle      = True,
                                          war_score_cost = war_score_cost + $1
                                      WHERE war_id = $2;''', war_score, war_info['id'])
                # update the embed
                peace_embed.add_field(name="Dismantle", value="Demanded", inline=False)
                # add the total war score
                total_war_score += war_score
                # send notification
                await self.interaction.followup.send(f"Demand for the Dismantling of {target_info['name']} added for "
                                                     f"{war_score} War Score.")
                # proceed
                continue

        # when the loop has finished, clear the view
        peace_negotiation_dropdown_view.clear_items()
        # if the war score is 0, meaning there are no demands, do not bother sending
        if (total_war_score == 0) and (not white_peace):
            await self.interaction.edit_original_response(view=None, embed=peace_embed)
            # destroy any pending negotiation, remove the view, and send rejection
            await conn.execute('''DELETE
                                  FROM cnc_peace_negotiations
                                  WHERE war_id = $1;''', war_info['id'])
            return await self.interaction.followup.send("No demands were added to the Peace Negotiations.",
                                                        ephemeral=True)
        # calculate the war score cost double if this is not a total negotiation
        if not total_negotiation:
            total_war_score *= 2
            await conn.execute('''UPDATE cnc_peace_negotiations
                                  SET war_score_cost = war_score_cost * 2
                                  WHERE war_id = $1;''', war_info['id'])
        # calculate the truce length where every 10% war score equals a turn of truce
        truce_length = max(total_war_score // 10, 2)
        # add a turn for each demand
        truce_length += len(negotiation_demands)
        # add the total peace negotiation amount at the bottom
        peace_embed.add_field(name="Total War Score Cost", value=f"{total_war_score}", inline=False)
        # send the updated embed
        await self.interaction.edit_original_response(embed=peace_embed, view=peace_negotiation_dropdown_view)
        # add the buttons
        send_button = discord.ui.Button(label="Send Negotiation", style=discord.ButtonStyle.success)
        cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)

        # define the callback for send
        async def send_callback(interaction: discord.Interaction):
            # defer the interaction
            await interaction.response.defer(thinking=False)
            # removing the view
            await self.interaction.edit_original_response(view=None)
            # get the recipient(s) if it is a total negotiation
            if total_negotiation:
                if user_info['name'] in war_info['attackers']:
                    recipients_names = war_info['defenders']
                else:
                    recipients_names = war_info['attackers']
            # otherwise, just have the target name
            else:
                recipients_names = [target]
            # primary recipient
            primary = recipients_names[0]
            # create the peace treaty
            await conn.execute('''INSERT INTO cnc_peace_treaties
                                  VALUES ($1, $2, $3, $4);''',
                               war_info['id'], war_info['attackers'].append(war_info['defenders']),
                               primary, truce_length)

            # define the peace negotiation parse function
            async def negotiation_parse(war_info: asyncpg.Record):
                # pull peace negotiation information
                peace_negotiation = await conn.fetchrow('''SELECT *
                                                           FROM cnc_peace_negotiations
                                                           WHERE war_id = $1;''', war_info['id'])
                # parse out and execute demands
                # if none of the default options were demanded, set to 0
                if not peace_negotiation['end_embargo']:
                    await conn.execute('''UPDATE cnc_peace_treaties
                                          SET end_embargo = 0
                                          WHERE war_id = $1;''',
                                       war_info['id'])
                if not peace_negotiation['end_ma']:
                    await conn.execute('''UPDATE cnc_peace_treaties
                                          SET end_ma = 0
                                          WHERE war_id = $1;''',
                                       war_info['id'])
                if not peace_negotiation['end_tp']:
                    await conn.execute('''UPDATE cnc_peace_treaties
                                          SET end_tp = 0
                                          WHERE war_id = $1;''',
                                       war_info['id'])
                if not peace_negotiation['humiliate']:
                    await conn.execute('''UPDATE cnc_peace_treaties
                                          SET humiliate = 0
                                          WHERE war_id = $1;''',
                                       war_info['id'])
                if not peace_negotiation['dismantle']:
                    await conn.execute('''UPDATE cnc_peace_treaties
                                          SET dismantle = 0
                                          WHERE war_id = $1;''',
                                       war_info['id'])
                # if there are cede province demands, update the owner and occupier
                if peace_negotiation['cede_provinces']:
                    # for every province, update the db with the new owner and occupier
                    for demanded_province in peace_negotiation['cede_provinces']:
                        # update the owner and occupier
                        await conn.execute('''UPDATE cnc_provinces
                                              SET owner_id    = $1,
                                                  occupier_id = $1
                                              WHERE id = $2;''',
                                           user_info['user_id'], demanded_province)
                # if there are give province demands, update the owner and occupier
                elif peace_negotiation['give_provinces']:
                    # parse out the recipients and their provinces, updating as necessary
                    for recipient in peace_negotiation['give_provinces']:
                        # pull their data
                        gpr_info = await conn.fetchrow('''SELECT *
                                                          FROM cnc_users
                                                          WHERE name = $1;''',
                                                       recipient)
                        # update the owner and the occupier for each province
                        for demanded_province in peace_negotiation['give_provinces'][recipient]:
                            await conn.execute('''UPDATE cnc_provinces
                                                  SET owner_id    = $1,
                                                      occupier_id = $1
                                                  WHERE id = $2;''',
                                               gpr_info['user_id'], demanded_province)
                # if there are end embargo demands, update the embargo
                elif peace_negotiation['end_embargo']:
                    # for every nation listed in the end embargo list, remove the embargo
                    for end_embargo in peace_negotiation['end_embargo']:
                        # update the database
                        await conn.execute('''DELETE
                                              FROM cnc_embargoes
                                              WHERE target = $1;''',
                                           end_embargo)
                        # notify target
                        ended_embargo_user_id = await conn.fetchval('''SELECT user_id
                                                                       FROM cnc_users
                                                                       WHERE name = $1;''',
                                                                    end_embargo)
                        await self.interaction.client.get_user(ended_embargo_user_id).send(f"The Embargo against"
                                                                                           f" {end_embargo} "
                                                                                           f"issued by "
                                                                                           f"{target_info['name']}"
                                                                                           f" has been ended by "
                                                                                           f"a Peace Treaty.")
                
                # if there are end military alliance demands, update the military alliance
                elif peace_negotiation['end_ma']:
                    # pull ma info
                    ma_info = await conn.fetchrow('''SELECT *
                                                     FROM cnc_alliances
                                                     WHERE $1 = ANY (members);''',
                                                  target_info['name'])
                    # message other members
                    for member in ma_info['members']:
                        # pull the member id
                        member_info = await conn.fetchval('''SELECT user_id
                                                             FROM cnc_users
                                                             WHERE name = $1;''', member)
                        # send the message
                        await self.interaction.client.get_user(member_info).send(f"{target_info['name']} is no "
                                                                                 f"longer an ally of {member} "
                                                                                 f"due to a Peace Treaty.")
                    # remove the target from the alliance
                    await conn.execute('''UPDATE cnc_alliances
                                          SET members = array_remove(members, $1)
                                          WHERE id = $2;''', target_info['name'], ma_info['id'])

                # if there are end trade pact demands, update the trade pacts
                elif peace_negotiation['end_tp']:
                    # pull tp info
                    tp_info = await conn.fetch('''SELECT *
                                                  FROM cnc_trade_partners
                                                  WHERE $1 = ANY (members);''',
                                               target_info['name'])
                    # for every trade pact
                    for trade_pact in tp_info:
                        # message other members
                        for member in trade_pact['members']:
                            # pull the member id
                            member_info = await conn.fetchval('''SELECT user_id
                                                                 FROM cnc_users
                                                                 WHERE name = $1;''', member)
                            # send the message
                            await self.interaction.client.get_user(member_info).send(f"{target_info['name']} has "
                                                                                     f"ended its Trade Pact with "
                                                                                     f"{member} due to a "
                                                                                     f"Peace Treaty.")
                        # delete the trade pact
                        await conn.execute('''DELETE
                                              FROM cnc_trade_pacts
                                              WHERE id = $1;''',
                                           trade_pact['id'])

                # if there are subjugate demands, create the puppet
                elif peace_negotiation['subjugate']:
                    # update the new puppet's overlord info
                    await conn.execute('''UPDATE cnc_users
                                          SET overlord = $1
                                          WHERE user_id = $2;''',
                                       user_info['name'], target_info['user_id'])

                # if there are dismantle demands, execute the dismantle stipulations
                elif peace_negotiation['dismantle']:
                    # reduce army size cap by a random amount between 10% and 25%
                    await conn.execute('''UPDATE cnc_users
                                          SET army_size = FLOOR(army_size *
                                                                (1 - (random() * (.25 - .10) + .10)))
                                          WHERE user_id = $1;''', target_info['user_id'])

                # if there are end overlordship demands, remove the overlordship
                elif peace_negotiation['end_overlordship']:
                    # for each of the demanded puppets
                    for puppet in peace_negotiation['end_overlord']:
                        # remove the overlordship
                        await conn.execute('''UPDATE cnc_users
                                              SET overlord = NULL
                                              WHERE name = $1;''',
                                           puppet)

                # if there are force govt demands, execute force government
                elif peace_negotiation['force_govt']:
                    # pull the victor's govt type
                    govt_type = await conn.fetchval('''SELECT govt_type
                                                       FROM cnc_users
                                                       WHERE user_id = $1;''',
                                                    user_info['user_id'])
                    # grab a random subtype
                    govt_subtype = await conn.fetchval('''SELECT RAND(govt_subtype)
                                                          FROM cnc_govts
                                                          WHERE govt_type = $1;''', govt_type)
                    # set the target's type and subtype
                    await conn.execute('''UPDATE cnc_users
                                          SET govt_type    = $1,
                                              govt_subtype = $2
                                          WHERE user_id = $3;''',
                                       govt_type, govt_subtype, target_info['user_id'])

            # send notification
            await interaction.followup.send("The Peace Negotiation has been delivered!")
            # update the embed footer
            peace_embed.set_footer(text=f"Peace Negotiation send.")
            await self.interaction.edit_original_response(embed=peace_embed)

            # if the current war score is less than a 100% or if the target is not the primary
            if (target_war_score < 100) or (target != primary):
                # pull their user ids and send the dm
                for recipient in recipients_names:
                    # make db call
                    r_info = await conn.fetchrow('''SELECT *
                                                    FROM cnc_users
                                                    WHERE name = $1;''', recipient)
                    # if the recipient is NOT the primary, because the primary code blocks
                    if recipient != primary:
                        await safe_dm(embed=peace_embed, user_id=r_info['user_id'], bot=interaction.client)
                    # continue
                    else:
                        continue
                # send dm (with options for the primary)
                # create a view for the dropdown and add it
                peace_negotiation_view = discord.ui.View(timeout=86400)

                # define callbacks`
                async def accept_callback(interaction: discord.Interaction):
                    # defer the interaction
                    await interaction.response.defer(thinking=True)
                    # parse negotiations
                    await negotiation_parse(war_info)
                    # send the acceptance dm to all participants
                    for member in [war_info['attackers'], war_info['defenders']]:
                        # pull their user id
                        user_id = await conn.fetchval('''SELECT user_id
                                                         FROM cnc_users
                                                         WHERE name = $1;''',
                                                      member)
                        # send notification
                        await safe_dm(embed=peace_embed, user_id=user_id, bot=interaction.client,
                                      content=f"The Peace Negotiations to end the **{war_info['name']}** "
                                              f"have been accepted by {target_info['name']}. "
                                              f"The terms are as follows:")
                        # delete the peace negotiation
                        await conn.execute('''DELETE
                                              FROM cnc_peace_negotiations
                                              WHERE war_id = $1;''',
                                           war_info['id'])

                async def decline_callback(interaction: discord.Interaction):
                    # defer the interaction
                    await interaction.response.defer(thinking=True)
                    # destroy any pending negotiation
                    await conn.execute('''DELETE
                                          FROM cnc_peace_negotiations
                                          WHERE war_id = $1;''', war_info['id'])
                    # send notifications
                    await interaction.edit_original_response(view=None, content="Declined")
                    await interaction.followup.send("Peace Negotiation declined.")
                    return await safe_dm(
                        content=f"Peace Negotiation **declined** for war `{war_info['id']}` "
                        f"by {target_info['name']}.", embed=peace_embed, bot=interaction.client,
                        user_id=target_info['user_id'])

                # create the accept button
                accept_button = discord.ui.Button(label="Accept", style=discord.ButtonStyle.success)
                accept_button.callback = accept_callback
                # create decline button
                decline_button = discord.ui.Button(label="Decline", style=discord.ButtonStyle.danger)
                decline_button.callback = decline_callback
                # add buttons to view
                peace_negotiation_view.add_item(accept_button)
                peace_negotiation_view.add_item(decline_button)
                # send to user with view
                await safe_dm(embed=peace_embed, view=peace_negotiation_view, user_id=target_info['user_id'],
                              bot=interaction.client)
                # check to see if it has timed out
                timed_out = await peace_negotiation_view.wait()
                # if the primary message times out
                if timed_out:
                    # send messages and auto reject
                    await interaction.edit_original_response(view=None)
                    # delete the negotiation
                    await conn.execute('''DELETE
                                          FROM cnc_peace_negotiations
                                          WHERE war_id = $1;''', war_info['id'])
                    await interaction.followup.send("Peace Negotiation has timed out and been auto-rejected.")
                    return await safe_dm(content=f"Peace Negotiation **declined** for war `{war_info['id']}` "
                                                 f"by {target_info['name']}.",
                                         embed=peace_embed, bot=interaction.client, user_id=target_info['user_id'])
            # otherwise, no negotiations required
            else:
                # check to ensure the demands are less than 100
                if total_war_score > 100:
                    # destroy any pending negotiation, remove the view, and send rejection
                    await conn.execute('''DELETE
                                          FROM cnc_peace_negotiations
                                          WHERE war_id = $1;''', war_info['id'])
                    await interaction.edit_original_response(view=None)
                    return await interaction.followup.send("Peace Negotiations for wars at 100% war score may not "
                                                           "exceed 100 demand cost.")
                # otherwise, carry on
                else:
                    # parse out demands
                    await negotiation_parse(war_info)
                    # notify the recipients that they have lost the war
                    for recipient in recipients_names:
                        # make db call
                        r_info = await conn.fetchrow('''SELECT *
                                                        FROM cnc_users
                                                        WHERE name = $1;''', recipient)
                        # send notification
                        await safe_dm(content=f"{user_info['name']} has demanded the following peace treaty. "
                                      f"The forces of {primary} and their allies have been overwhelmed "
                                      f"entirely. The negotiation has been automatically accepted.",
                                      embed=peace_embed, user_id=r_info['user_id'], bot=interaction.client)

        # add the callback for send
        send_button.callback = send_callback
        # define the callback for cancel
        cancel_button.callback = cancel_button_callback
        # create the send button view
        send_button_view = discord.ui.View(timeout=120)
        # add the buttons
        send_button_view.add_item(send_button)
        send_button_view.add_item(cancel_button)
        # add the view to the embed
        await self.interaction.edit_original_response(view=send_button_view)
        # check to see if it has timed out
        timed_out = await send_button_view.wait()
        # if the primary message times out
        if timed_out:
            # delete the pending negotiation
            await conn.execute('''DELETE
                                  FROM cnc_peace_negotiations
                                  WHERE war_id = $1;''', war_info['id'])
            # remove view and send update
            return await self.interaction.edit_original_response(view=None)


class AuthDemandView(discord.ui.View):
    def __init__(self, parent_interaction: discord.Interaction, conn: asyncpg.Pool,
                 war_info: asyncpg.Record):
        super().__init__(timeout=120)

        self.parent_interaction = parent_interaction

        self.mil_authority = None
        self.econ_authority = None
        self.diplo_authority = None
        self.auths_demanded = None
        self.war_score = 0
        self.cancelled = False
        self.conn = conn
        self.war_info = war_info

        # Add selects
        self.add_item(self.MilSelect())
        self.add_item(self.EconSelect())
        self.add_item(self.DiploSelect())

    # on timeout
    async def on_timeout(self):
        await self.conn.execute(
            '''DELETE
                FROM cnc_peace_negotiations
                WHERE war_id = $1;''',
            self.war_info['id']
        )
        return await self.parent_interaction.edit_original_response(view=None)

    # create the select classes

    class MilSelect(discord.ui.Select):
        def __init__(self):
            options = [discord.SelectOption(label=str(i), value=str(i)) for i in range(7)]
            super().__init__(
                placeholder="Select amount of Military Authority to demand...",
                options=options,
                row=0
            )

        async def callback(self, interaction: discord.Interaction):
            self.view.mil_authority = self.values[0]
            await interaction.response.defer()

    class EconSelect(discord.ui.Select):
        def __init__(self):
            options = [discord.SelectOption(label=str(i), value=str(i)) for i in range(7)]
            super().__init__(
                placeholder="Select amount of Economic Authority to demand...",
                options=options,
                row=1
            )

        async def callback(self, interaction: discord.Interaction):
            self.view.econ_authority = self.values[0]
            await interaction.response.defer()  # or thinking=False if you want silent

    class DiploSelect(discord.ui.Select):
        def __init__(self):
            options = [discord.SelectOption(label=str(i), value=str(i)) for i in range(7)]
            super().__init__(
                placeholder="Select amount of Diplomatic Authority to demand...",
                options=options,
                row=2
            )

        async def callback(self, interaction: discord.Interaction):
            self.view.diplo_authority = self.values[0]
            await interaction.response.defer() 

    # create submit and cancel buttons

    @discord.ui.button(label="Submit", style=discord.ButtonStyle.success, row=3)
    async def submit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # defer the interaction
        await interaction.response.defer()
        # if the user has not selected one of the options as is necessary
        if None in (self.mil_authority, self.econ_authority, self.diplo_authority):
            return await interaction.followup.send(
                "You must select all three authority values first.",
                ephemeral=True
            )
        # otherwise, define the auths demanded
        self.auths_demanded = [
            int(self.mil_authority),
            int(self.econ_authority),
            int(self.diplo_authority)
        ]
        # calculate the war score
        self.war_score = sum(self.auths_demanded) * 5
        # execute the update
        await self.conn.execute('''UPDATE cnc_peace_negotiations
                                SET demand_reparations = $1,
                                    war_score_cost     = war_score_cost + $2
                                WHERE war_id = $3;''',
                            self.auths_demanded,
                            self.war_score,
                            self.war_info['id']
                            )
        # send notification
        await interaction.followup.send(f"Demand Reparations has been "
                                                f"added at a cost of `{self.war_score}` War Score.")
        # stop the listening
        return self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, row=3)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # determine if cancelled
        self.cancelled = True
        # delete the pending interaction
        await self.conn.execute(
            '''DELETE
                FROM cnc_peace_negotiations
                WHERE war_id = $1;''',
            self.war_info['id']
        )
        # stop listening
        self.stop()
        # update the view
        return await self.parent_interaction.edit_original_response(view=None)


class PeaceNegotiationOptionsDropdown(discord.ui.Select):

    # hypersimplistic dropdown
    def __init__(self, pts: list):
        # create the options
        pt_options = []
        for pt in pts:
            pt_options.append(discord.SelectOption(label=pt))
        # define the super
        super().__init__(placeholder="Choose Peace Treaty Demands...", min_values=1, max_values=len(pt_options),
                         options=pt_options, custom_id="peace_treaty_negotiations_dropdown")


class PeaceNegotiationTargetsDropdown(discord.ui.Select):

    # hypersimplistic dropdown
    def __init__(self, targets: list):
        # create the options
        target_options = []
        for pt in targets:
            target_options.append(discord.SelectOption(label=pt))
        # define the super
        super().__init__(placeholder="Choose Treaty Target...", min_values=1, max_values=1,
                         options=target_options, custom_id="target_dropdown")


class PeaceNegotiationGiveProvincesDropdown(discord.ui.Select):

    # hypersimplistic dropdown
    def __init__(self, potential_targets: list):
        # create the options
        potential_targets = []
        for target in potential_targets:
            potential_targets.append(discord.SelectOption(label=target))
        # define the super
        super().__init__(placeholder="Choose Give Provinces Target...", min_values=1, max_values=1,
                         options=potential_targets, custom_id="give_provinces_target")


class CNC(commands.Cog):

    def __init__(self, bot: Shard):
        self.map_directory = r"/root/Shard/CNC/Map Files/Maps/"
        self.province_directory = r"/root/Shard/CNC/Map Files/Province Layers/"
        self.interaction_directory = r"/root/Shard/CNC/Interaction Files/"
        self.tech_directory = r"/root/Shard/CNC/Tech Tree/"
        self.bot = bot
        self.banned_colors = ["#000000", "#ffffff", "#808080", "#0071BC", "#0084E2", "#2BA5E2", "#999999", "#FF0000"]
        self.version = "version 4.0 New Horizons"
        self.version_notes = ""

    async def interaction_check(self, interaction: discord.Interaction):
        # establish connection
        conn = self.bot.pool
        # pull data
        user_data = await conn.fetchrow('''SELECT *
                                           FROM cnc_users
                                           WHERE user_id = $1;''', interaction.user.id)
        # check if existing
        if user_data is None:
            return True
        # check blacklisted
        if user_data['blacklisted'] is True:
            return False
        # otherwise, return true
        else:
            return True

    async def occupy_color(self, province: int, occupy_color: str, owner_color: str):
        # establish connection
        conn = self.bot.pool
        # pull province information
        province_info = await conn.fetchrow('''SELECT *
                                               FROM cnc_provinces
                                               WHERE id = $1;''', province)
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

    async def locate_color(self, province: int, prov_cords: tuple):
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
        cord = (int(prov_cords[0]), int(prov_cords[1]))
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

    async def nation_db_info(self, nation_name: str):
        """Pulls user info from the database using the nation name."""
        # estbalish connection
        conn = self.bot.pool
        # pull user information based on nation name
        user_info = await conn.fetchrow('''SELECT *
                                           FROM cnc_users
                                           WHERE LOWER(name) = $1;''', nation_name.lower())
        return user_info

    async def nation_provinces_db_sort(self, user_id: int):
        """Pulls info from the database about ALL of a user's provinces using Discord user ID.
        Returns a sorted list of provinces and the count of provinces."""
        # establish connection
        conn = self.bot.pool
        # pull territory information
        provinces = await conn.fetch('''SELECT id
                                        FROM cnc_provinces
                                        WHERE owner_id = $1;''', user_id)
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
        provinces = await conn.fetch('''SELECT *
                                        FROM cnc_provinces
                                        WHERE owner_id = $1;''', user_id)
        return provinces

    async def province_db_info(self, province_id: int = None, province_name: str = None):
        """Pulls info from the database about a particular province using province ID."""
        # establish connection
        conn = self.bot.pool
        # pull province information
        if province_id is not None:
            province = await conn.fetchrow('''SELECT *
                                              FROM cnc_provinces
                                              WHERE id = $1;''', province_id)
        elif province_name is not None:
            province = await conn.fetchrow('''SELECT *
                                              FROM cnc_provinces
                                              WHERE name = $1;''', province_name)
        else:
            raise TypeError
        return province

    def hex_to_rgb(self, hex_color):
        """Converts a hex color code to RGB values."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def color_difference(self, color1, color2):
        """Calculates the Euclidean distance between two RGB colors."""
        rgb1 = self.hex_to_rgb(color1)
        rgb2 = self.hex_to_rgb(color2)
        return sum((c1 - c2) ** 2 for c1, c2 in zip(rgb1, rgb2)) ** 0.5

    # the CnC command group
    cnc = app_commands.Group(name="cnc", description="...")

    # === User Commands and View Commands === #

    @cnc.command(name="register", description="Registers a new player nation.")
    @app_commands.describe(nation_name="The name of your new nation.",
                           color="The hex code of your new nation. Include the '#'.")
    async def register(self, interaction: discord.Interaction, nation_name: str, color: str):
        # defer the interaction
        await interaction.response.defer(thinking=True)
        # deny access if in DMs
        if not interaction.guild:
            return commands.NoPrivateMessage
        # establish connection
        conn = self.bot.pool
        # define user
        user = interaction.user
        # check if the user already exists
        check_call = await user_db_info(user.id, conn)
        if check_call is not None:
            return await interaction.followup.send(
                f"You are already a registered player of the Command and Conquest system. "
                f"Your nation name is {check_call['name']}.", ephemeral=True)
        # otherwise, continue with player registration
        else:
            # check if the color is taken, banned, or even a color
            check_color_taken = await conn.fetchrow('''SELECT *
                                                       FROM cnc_users
                                                       WHERE color = $1;''', color)
            if check_color_taken is not None:
                return await interaction.followup.send("That color is already taken. "
                                                       "Please register with a different color.")
            # pull all colors
            pull_all_colors = await conn.fetch('''SELECT name, color
                                                  FROM cnc_users;''')
            # check each color
            for c in pull_all_colors:
                color_check = c['color']
                if self.color_difference(color, color_check) < 25:
                    return await interaction.followup.send(f"Your selected color, {color}, is too similar to an "
                                                           f"existing color, registered to {c['name']} ({c['color']}).")

            if color in self.banned_colors:
                return await interaction.followup.send("That color is a restricted color. "
                                                       "Please register with a different color.")
            for c in self.banned_colors:
                if self.color_difference(c, color) < 25:
                    return await interaction.followup.send(f"That color is too similar to a banned color, {c}.")
            # try and get the color from the hex code
            try:
                ImageColor.getrgb(color)
            except ValueError:
                # if the color isn't a real hex code, return that they need to get the right hex code
                return await interaction.followup.send(
                    "That doesn't appear to be a valid hex color code. Include the `#` symbol.")
            # insert the new player into the user database
            await conn.execute('''INSERT INTO cnc_users(user_id, name, color)
                                  VALUES ($1, $2, $3);''', user.id,
                               nation_name.title(), color)
            # select the starting province
            # the starting province cannot be on one of the few islands do prevent impossible starts
            # the starting province cannot be owned by any player
            # (and since unowned provinces cannot be occupied, that too)
            starting_province = await conn.fetchrow('''SELECT *
                                                       FROM cnc_provinces
                                                       WHERE owner_id = 0
                                                         and id NOT IN
                                                             (130, 441, 442, 621, 622, 623, 65, 486, 215, 923, 926, 924,
                                                              925, 771, 772, 770, 769, 768, 909, 761, 762, 763, 764,
                                                              765, 766, 767, 1207,
                                                              1208, 1209, 1210, 1211, 1212, 1213, 1214, 744)
                                                       ORDER BY random();''')
            # update the provinces database to set the player as the new owner and occupier
            await conn.execute('''UPDATE cnc_provinces
                                  SET owner_id    = $1,
                                      occupier_id = $1
                                  WHERE id = $2;''',
                               user.id, starting_province['id'])
            # color the map using the province coordinates and the ID
            await map_color(starting_province['id'], color, conn)
            # create an army of 3,000 troops in the starting province
            await conn.execute('''INSERT INTO cnc_armies(owner_id, troops, location, army_name)
                                  VALUES ($1, $2, $3, $4);''', user.id, 3000, starting_province['id'],
                               f"Army of {starting_province['name']}")
            # send welcome message
            return await interaction.followup.send(
                f"Welcome to the Command and Conquest System, {user.mention}!\n\n"
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
                f"**\"I came, I saw, I conquered.\" -Julius Caesar**"
            )

    # @cnc.command(name="change_color", description="Changes your nation's color on the map.")
    # @app_commands.checks.cooldown(1, 30)
    # @app_commands.describe(color="The hex code of your new map color. Include the '#'.")
    # async def recolor(self, interaction: discord.Interaction, color: str):
    #     # defer interaction
    #     await interaction.response.defer(thinking=True)
    #     # deny access if in DMs
    #     if not interaction.guild:
    #         return commands.NoPrivateMessage
    #     # establish connection
    #     conn = self.bot.pool
    #     # pull userinfo
    #     user_info = await user_db_info(interaction.user.id)
    #     # check for registration
    #     if user_info is None:
    #         return await interaction.followup.send("You are not a registered member of the CNC system.")
    #     # check if the color is taken, banned, or even a color
    #     check_color_taken = await conn.fetchrow('''SELECT *
    #                                                FROM cnc_users
    #                                                WHERE color = $1;''', color)
    #     if check_color_taken is not None:
    #         return await interaction.followup.send("That color is already taken. "
    #                                                "Please select a different color.")
    #     # pull all colors
    #     pull_all_colors = await conn.fetch('''SELECT name, color
    #                                           FROM cnc_users;''')
    #     # check each color
    #     for c in pull_all_colors:
    #         color_check = c['color']
    #         if self.color_difference(color_check, color) < 50:
    #             return await interaction.followup.send(f"Your selected color, {color}, is too similar to an "
    #                                                    f"existing color, registered to {c['name']} ({c['color']}).")
    #
    #     if color in self.banned_colors:
    #         return await interaction.followup.send("That color is a restricted color. "
    #                                                "Please select a different color.")
    #     for c in self.banned_colors:
    #         if self.color_difference(c, color) < 50:
    #             return await interaction.followup.send(f"That color is too similar to a banned color, {c}.")
    #     # try and get the color from the hex code
    #     try:
    #         ImageColor.getrgb(color)
    #     except ValueError:
    #         # if the color isn't a real hex code, return that they need to get the right hex code
    #         return await interaction.followup.send(
    #             "That doesn't appear to be a valid hex color code. Include the `#` symbol.")
    #     # if the color is valid, update the database
    #     await conn.execute('''UPDATE cnc_users
    #                           SET color = $1
    #                           WHERE user_id = $2;''', color, interaction.user.id)
    #     # get all provinces
    #     all_provinces = await conn.fetch('''SELECT *
    #                                         FROM cnc_provinces
    #                                         WHERE owner_id = $1;''', interaction.user.id)
    #     for p in all_provinces:
    #         p_id = p['id']
    #         if p['occupier_id'] == user_info['user_id']:
    #             await map_color(p_id, color, conn)
    #         elif p['occupier_id'] == 0:
    #             await self.occupy_color(p_id, '#000000', color)
    #         elif p['occupier_id'] != user_info['user_id']:
    #             occupier_color = await conn.fetchrow('''SELECT color
    #                                                     FROM cnc_users
    #                                                     WHERE user_id = $1;''',
    #                                                  p['occupier_id'])
    #             await self.occupy_color(p_id, occupier_color, color)
    #     return await interaction.followup.send(f"Color successfully changed to {color}!")

    @cnc.command(name="map", description="Opens the map for viewing.")
    async def map(self, interaction: discord.Interaction):
        # defer the interaction
        await interaction.response.defer(thinking=True)
        # deny access if in DMs
        if not interaction.guild:
            return commands.NoPrivateMessage
        # send the map
        map = await interaction.followup.send("https://i.ibb.co/6RtH47v/Terrain-with-Numbers-Map.png")
        map_buttons = MapButtons(map, author=interaction.user)
        await map.edit(view=map_buttons)

    @cnc.command(name="locate_province", description="Highlights a province on the map.")
    @app_commands.describe(province="The ID of the province to locate.")
    async def locate_province(self, interaction: discord.Interaction, province: int):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # deny access if in DMs
        if not interaction.guild:
            return commands.NoPrivateMessage
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
    @app_commands.describe(nation="The name of the nation you wish to query.", user="The user you wish to query.")
    async def nation(self, interaction: discord.Interaction, user: discord.Member = None, nation: str = None):
        # if neither argument is submitted, return error message
        if (nation is None) and (user is None):
            user_info = await user_db_info(interaction.user.id, self.bot.pool)
            if user_info is None:
                return await interaction.followup.send(f"That user is not a registered player of the CNC system.",
                                                       ephemeral=True)
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
        # if the user is called
        elif user is not None:
            user_info = await user_db_info(user.id, self.bot.pool)
            if user_info is None:
                return await interaction.followup.send(f"That user is not a registered player of the CNC system.",
                                                       ephemeral=True)
        # define connection
        conn = self.bot.pool
        # pull the caller's info to check their government type
        caller_info = await conn.fetchrow('''SELECT *
                                             FROM cnc_users
                                             WHERE user_id = $1;''', interaction.user.id)
        # pull province data
        province_list, province_count = await self.nation_provinces_db_sort(user_info['user_id'])
        # pull the name of the capital
        capital = await conn.fetchrow('''SELECT *
                                         FROM cnc_provinces
                                         WHERE id = $1;''', user_info['capital'])
        if capital is None:
            capital = "None"
        else:
            capital = capital['name']
        # pull relations information
        alliances = await conn.fetch('''SELECT *
                                        FROM cnc_alliances
                                        WHERE $1 = ANY (members);''',
                                     user_info['name'])
        wars = await conn.fetch('''SELECT *
                                   FROM cnc_wars
                                   WHERE $1 = ANY (array_cat(attackers, defenders));''',
                                user_info['name'])
        trade_pacts = await conn.fetch('''SELECT *
                                          FROM cnc_trade_pacts
                                          WHERE $1 = ANY (members);''',
                                       user_info['name'])
        military_access = await conn.fetch('''SELECT *
                                              FROM cnc_military_access
                                              WHERE $1 = ANY (members);''', user_info['name'])
        diplomatic_relations = await conn.fetch('''SELECT *
                                                   FROM cnc_drs
                                                   WHERE $1 = ANY (members);''',
                                                user_info['name'])
        embargoes = await conn.fetch('''SELECT *
                                        FROM cnc_embargoes
                                        WHERE sender = $1;''',
                                     user_info['name'])

        def parse_relations(relations: list, wars: bool = False) -> str:
            """
            Parses out the names of nations within the input relations.
            ``wars``, if true, parses out attackers and defenders rather than "members".
            """
            if not relations:
                output = "None"
                return output
            elif wars:
                output = ""
                # for each relation, join to a comma-separated list if the relation "member" isn't the user's nation
                for relation in relations:
                    buffer_output = ", ".join([r for r in relation['attackers'] if r != user_info['name']])
                    buffer_output += ", ".join([r for r in relation['defenders'] if r != user_info['name']])
                    output += buffer_output
                return output
            else:
                output = ""
                # for each relation, join to a comma-separated list if the relation "member" isn't the user's nation
                for relation in relations:
                    buffer_output = ", ".join([r for r in relation['members'] if r != user_info['name']])
                    output += buffer_output
                return output

        allies = parse_relations(alliances)
        trade_pacts = parse_relations(trade_pacts)
        wars = parse_relations(wars, True)
        military_access = parse_relations(military_access)
        diplomatic_relations = parse_relations(diplomatic_relations)
        if not embargoes:
            embargoes = "None"
        else:
            embargoes = ", ".join([e['target'] for e in embargoes])
        # build embed, populate title with pretitle and nation name, set color to user color,
        # and set description to Discord user.
        user_embed = discord.Embed(title=f"The {user_info['pretitle']} of {user_info['name']}",
                                   color=discord.Color(int(user_info["color"].lstrip('#'), 16), ),
                                   description=f"Registered nation of "
                                               f"{(self.bot.get_user(user_info['user_id'])).mention}.\n")
        user_embed.set_thumbnail(url=r"https://i.ibb.co/bbxhJtx/Command-Conquest-symbol.png")
        # populate government type and subtype
        user_embed.add_field(name="====================GOVERNMENT====================",
                             value="Information known about the nation's government.", inline=False)
        user_embed.add_field(name="Government", value=f"{user_info['govt_subtype']} {user_info['govt_type']}")
        # populate territory and count
        user_embed.add_field(name=f"Territory (Total: {province_count})", value=f"{province_list}")
        # populate capital
        user_embed.add_field(name="Capital", value=f"{capital}")
        # populate stability
        user_embed.add_field(name="Stability", value=f"{user_info['stability']}")
        # populate all three types of authority
        user_embed.add_field(name="=====================AUTHORITY=====================",
                             value="Information known about the nation's authority.", inline=False)
        user_embed.add_field(name="Political Authority", value=f"{user_info['pol_auth']}")
        user_embed.add_field(name="Military Authority", value=f"{user_info['mil_auth']}")
        user_embed.add_field(name="Economic Authority", value=f"{user_info['econ_auth']}")
        # populate all four types of relations
        user_embed.add_field(name="=====================RELATIONS=====================",
                             value="Information known about the nation's international relationships.", inline=False)
        user_embed.add_field(name="Allies", value=f"{allies}")
        user_embed.add_field(name="Wars", value=f"{wars}")
        user_embed.add_field(name="Military Access", value=f"{military_access}")
        user_embed.add_field(name="Diplomatic Relations", value=diplomatic_relations)
        user_embed.add_field(name="Trade Pacts", value=f"{trade_pacts}")
        user_embed.add_field(name="Embargoes", value=embargoes)
        # if the user has called their own nation, add a footnote to show that relations are disabled with their own nation
        if user_info['user_id'] == interaction.user.id:
            user_embed.set_footer(text="Diplomatic actions are disabled for your own nation.")
            # send the embed
            return await interaction.followup.send(embed=user_embed)
        else:
            diplomacy_view = DiplomaticMenuView(interaction, conn, user_info)
            # send the embed
            return await interaction.followup.send(embed=user_embed, view=diplomacy_view)

    @cnc.command(name="dossier", description="Displays detailed information about your nation.")
    async def dossier(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True, ephemeral=True)
        # establish connection
        conn = self.bot.pool
        # fetch user information
        user_id = interaction.user.id
        user_info = await user_db_info(user_id, self.bot.pool)
        # if the user does not exist
        if user_info is None:
            # return error message
            return await interaction.followup.send("You are not a registered member of the CNC system`.")
        # pull province data
        province_list = await self.nation_provinces_db_info(user_id)
        province_list = [p['id'] for p in province_list]
        province_count = len(province_list)
        province_list = ", ".join(str(p) for p in province_list)
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
        # create dossier view
        doss_view = DossierView(interaction, user_embed, user_info, conn)
        # send and include view
        await interaction.followup.send(embed=user_embed, view=doss_view)

    @cnc.command(name="strategic_view", description="Displays information about every province owned.")
    @app_commands.describe(direct_message="Optional: select True to send a private DM.")
    async def strategic_view(self, interaction: discord.Interaction, direct_message: bool = None):
        # defer interaction
        await interaction.response.defer(thinking=True, ephemeral=True)
        # pull user information
        user_id = interaction.user.id
        user_info = await user_db_info(user_id, self.bot.pool)
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
                               value=f"Terrain: {await terrain_name(p['terrain'], self.bot.pool)}\n"
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

        # if the user owns the province, open the ownership view
        if prov_info['owner_id'] == interaction.user.id:
            user_info = await user_db_info(interaction.user.id, conn)
            author = interaction.user
            owned_province_view = OwnedProvinceModifiation(author, prov_info, user_info, conn)
            owned_province_view.interaction = interaction
            await interaction.edit_original_response(view=owned_province_view,
                                                     embed=await create_prov_embed(prov_info, conn))

        # if the user does not own the province, and it is unowned, open the unowned view
        elif prov_info['owner_id'] == 0:
            # if the user is a player, check if they have the colonialism tech
            user_info = await user_db_info(interaction.user.id, conn)
            if user_info is not None:
                if 'Colonialism' in user_info['tech']:
                    colony_view = UnownedProvince(interaction.user, prov_info, user_info, conn)
                    colony_view.interaction = interaction
                    await interaction.edit_original_response(view=colony_view,
                                                             embed=await create_prov_embed(prov_info, conn))
            else:
                return await interaction.edit_original_response(embed=await create_prov_embed(prov_info, conn))

        # if the user does not own the province, and it is owned by another player, send the embed
        elif prov_info['owner_id'] != 0:
            await interaction.edit_original_response(embed=await create_prov_embed(prov_info, conn))

    @cnc.command(name="army_view", description="Displays information about a specific army.")
    @app_commands.describe(army_id="The ID of the army")
    async def army_view(self, interaction: discord.Interaction, army_id: int):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # pull army information
        army_info = await conn.fetchrow('''SELECT *
                                           FROM cnc_armies
                                           WHERE army_id = $1;''', army_id)
        # if there is no such army
        if army_info is None:
            return await interaction.followup.send("No such army found.")
        # otherwise, carry on
        # define values
        army_name = army_info['army_name']
        owner_id = army_info['owner_id']
        troops = army_info['troops']
        location = army_info['location']
        general = army_info['general']
        if general == 0:
            general = "None"
        else:
            general_info = await conn.fetchrow('''SELECT *
                                                  FROM cnc_generals
                                                  WHERE general_id = $1;''', general)
            general = f"{general_info['name']} (ID: {general_info['general_id']})"
        movement = army_info['movement']
        # pull userinfo
        userinfo = await user_db_info(owner_id, conn)
        user = self.bot.get_user(owner_id)
        # build embed
        army_embed = discord.Embed(title=f"{army_name}", description=f"Information about an army (ID {army_id}).",
                                   color=discord.Color.from_str(userinfo['color']))
        army_embed.set_thumbnail(url=r"https://i.ibb.co/bbxhJtx/Command-Conquest-symbol.png")
        army_embed.add_field(name="Owner", value=f"{userinfo['name']}\n({user.mention})")
        army_embed.add_field(name="Troops", value=troops)
        army_embed.add_field(name="Province Location ID", value=location, inline=False)
        army_embed.add_field(name="General", value=general)
        army_embed.add_field(name="Movement Available", value=movement)
        return await interaction.followup.send(embed=army_embed)

    @cnc.command(name="army_report", description="Displays information about all armies.")
    async def army_report(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True, ephemeral=True)
        # establish connection
        conn = self.bot.pool
        # pull user info
        userinfo = await user_db_info(interaction.user.id, conn)
        # if the user isn't a player, deny
        if userinfo is None:
            return await interaction.followup.send("You are not a registered member of the CNC system.")
        # pull army information
        army_info = await conn.fetch('''SELECT *
                                        FROM cnc_armies
                                        WHERE owner_id = $1;''', interaction.user.id)
        # if there is no info
        if army_info is None:
            return await interaction.followup.send(f"{userinfo['name']} does not control any armies.")
        # otherwise, carry on
        # create embed
        armies_embed = discord.Embed(title=f"Army Report for {userinfo['name']}",
                                     description="Information concerning all controlled armies.")
        # for each of the entries, make a field
        for army in army_info:
            army_name = army['army_name']
            army_id = army['army_id']
            troops = army['troops']
            location = army['location']
            general = army['general']
            if general == 0:
                general = "No"
            else:
                general = "Yes"
            armies_embed.add_field(name=f"{army_name} (ID: {army_id})", value=f"**Troops**: {troops}\n"
                                                                              f"**Location**: {location}\n"
                                                                              f"**General**: {general}")
        return await interaction.followup.send(embed=armies_embed)

    @cnc.command(name="view_wars", description="Displays information about all ongoing wars.")
    @app_commands.describe(view_all="Optional: select True for viewing all ongoing wars.")
    async def view_wars(self, interaction: discord.Interaction, view_all: bool = False):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # define the pool
        conn = self.bot.pool
        # if the user opted to see all wars, display them
        if view_all is True:
            all_wars = await conn.fetch('''SELECT *
                                           FROM cnc_wars
                                           WHERE active = True;''')
            # if there are no active wars, send such
            if not all_wars:
                return await interaction.followup.send("There are no ongoing wars. "
                                                       "Peace on earth! Goodwill towards men!")
            # list out all the wars
            else:
                # create the initial embed
                all_wars_embed = discord.Embed(title="Global Wars", color=discord.Color.red(),
                                               description="A directory of all ongoing wars.")
                # populate the first ten options
                wars_to_display = all_wars[:10]
                for war in wars_to_display:
                    # get the list of attackers and defenders, placing the primary first and bolding
                    attackers_list = list(war['attackers']) if war['attackers'] is not None else []
                    defenders_list = list(war['defenders']) if war['defenders'] is not None else []
                    attackers_others = [a for a in attackers_list if a != war['primary_attacker']]
                    defenders_others = [d for d in defenders_list if d != war['primary_defender']]
                    attackers = ", ".join([f"**{war['primary_attacker']}**"] + attackers_others) if war[
                        'primary_attacker'] else ", ".join(attackers_list)
                    defenders = ", ".join([f"**{war['primary_defender']}**"] + defenders_others) if war[
                        'primary_defender'] else ", ".join(defenders_list)
                    all_wars_embed.add_field(name=f"The {war['name']}",
                                             value=f"ID: {war['id']}\n"
                                                   f"Attackers: {attackers}\n"
                                                   f"Defenders: {defenders}\n"
                                                   f"Casus Belli: {war['cb']}\n"
                                                   f"Defensio Belli: {war['db'] or 'None'}\n"
                                                   f"Turns: {war['turns']}\n"
                                                   f"Deaths: {war['deaths']}")
                # if there are less than 10, send embed
                if len(all_wars) <= 10:
                    return await interaction.followup.send(embed=all_wars_embed)
                else:
                    all_wars_pages = WarsPaginator(interaction, all_wars, all_wars_embed)
                    return await interaction.followup.send(embed=all_wars_embed, view=all_wars_pages)
        # check for the user's data
        user_info = await user_db_info(interaction.user.id, conn)
        # if the user is not registered, return denial
        if user_info is None:
            return await interaction.followup.send("You are not a registered user of the Command and Conquest system.\n"
                                                   "To register, use the `\cnc register` command!")
        # check for what wars the user is in
        user_wars = await conn.fetch('''SELECT *
                                        FROM cnc_wars
                                        WHERE $1 = ANY (array_cat(attackers, defenders))
                                          AND active = True;''',
                                     user_info['name'])
        # if they have no active wars, send such
        if not user_wars:
            return await interaction.followup.send(f"{user_info['name']} is not currently at war.")
        # otherwise, display all the wars the user is a part of
        # create the initial embed
        all_wars_embed = discord.Embed(title="National Wars", color=discord.Color.red(),
                                       description=f"A directory of all ongoing wars involving {user_info['name']}.")
        # populate the first ten options
        wars_to_display = user_wars[:10]
        for war in wars_to_display:
            # get the list of attackers and defenders, placing the primary first and adding asterisk
            attackers_list = list(war['attackers']) if war['attackers'] is not None else []
            defenders_list = list(war['defenders']) if war['defenders'] is not None else []
            attackers_others = [a for a in attackers_list if a != war['primary_attacker']]
            defenders_others = [d for d in defenders_list if d != war['primary_defender']]
            attackers = ", ".join([f"**{war['primary_attacker']}**"] + attackers_others) if war[
                'primary_attacker'] else ", ".join(attackers_list)
            defenders = ", ".join([f"**{war['primary_defender']}**"] + defenders_others) if war[
                'primary_defender'] else ", ".join(defenders_list)
            all_wars_embed.add_field(name=f"The {war['name']}",
                                     value=f"ID: {war['id']}\n"
                                           f"Attackers: {attackers}\n"
                                           f"Defenders: {defenders}\n"
                                           f"Casus Belli: {war['cb']}\n"
                                           f"Defensio Belli: {war['db'] or 'None'}\n"
                                           f"Turns: {war['turns']}\n"
                                           f"Deaths: {war['deaths']}")
        # if there are less than 10, send embed
        if len(user_wars) <= 10:
            return await interaction.followup.send(embed=all_wars_embed)
        else:
            all_wars_pages = WarsPaginator(interaction, user_wars, all_wars_embed)
            return await interaction.followup.send(embed=all_wars_embed, view=all_wars_pages)

    @cnc.command(name="war", description="Displays information about a specific war and option related to that war.")
    @app_commands.describe(war_id="The war's ID or full name.")
    async def war_info(self, interaction: discord.Interaction, war_id: str):
        # defer the interaction
        await interaction.response.defer(thinking=True)
        # establish the conn
        conn = self.bot.pool
        # look for the user info, if any
        user_info = await conn.fetchrow('''SELECT *
                                           FROM cnc_users
                                           WHERE user_id = $1;''', interaction.user.id)
        # parse the war id
        try:
            war_id = int(war_id)
            # search for the active war using the id
            war_info = await conn.fetchrow('''SELECT *
                                              FROM cnc_wars
                                              WHERE id = $1
                                                AND active = True;''',
                                           war_id)
        except ValueError:
            war_id = str(war_id)
            # search for the active war using the name
            war_info = await conn.fetchrow('''SELECT *
                                              FROM cnc_wars
                                              WHERE name = $1
                                                AND active = True;''',
                                           war_id)
        # create the war embed
        war_embed = discord.Embed(title=f"{war_info['name']}", color=discord.Color.red(),
                                  description="Information about an ongoing war.")
        # get the list of attackers and defenders, placing the primary first and bolding
        attackers_list = list(war_info['attackers']) if war_info['attackers'] is not None else []
        defenders_list = list(war_info['defenders']) if war_info['defenders'] is not None else []
        attackers_others = [a for a in attackers_list if a != war_info['primary_attacker']]
        defenders_others = [d for d in defenders_list if d != war_info['primary_defender']]
        attackers = ", ".join([f"**{war_info['primary_attacker']}**"] + attackers_others) if war_info[
            'primary_attacker'] else ", ".join(attackers_list)
        defenders = ", ".join([f"**{war_info['primary_defender']}**"] + defenders_others) if war_info[
            'primary_defender'] else ", ".join(defenders_list)
        war_embed.add_field(name=f"The {war_info['name']}",
                            value=f"ID: {war_info['id']}\n"
                                  f"Attackers: {attackers}\n"
                                  f"Defenders: {defenders}\n"
                                  f"Casus Belli: {war_info['cb']}\n"
                                  f"Defensio Belli: {war_info['db'] or 'None'}\n"
                                  f"Turns: {war_info['turns']}\n"
                                  f"Deaths: {war_info['deaths']}")
        # send the embed with the appropriate buttons
        # if the user is in the war and is a primary, add the military alliance option and the peace option
        if (user_info['name'] == war_info['primary_attacker']) or (user_info['name'] == war_info['primary_defender']):
            # if the user is in a military alliance, enable that button
            alliance_check = await conn.fetchrow('''SELECT *
                                                    FROM cnc_alliances
                                                    WHERE $1 = ANY (members);''',
                                                 user_info['name'])
            if alliance_check:
                alliance_button = True
            else:
                alliance_button = False
            # if the war has no defensio belli option and the user is the primary defender, enable that button
            if user_info['name'] == war_info['primary_defender']:
                if not war_info['db']:
                    defensio_belli_button = True
                else:
                    defensio_belli_button = False
            else:
                defensio_belli_button = False
            # add the appropriate buttons, including the peace negotiation button
            war_options_view = WarOptionsView(interaction, conn, war_info,
                                              alliance_button, defensio_belli_button, user_info, war_embed)
            return await interaction.followup.send(embed=war_embed, view=war_options_view)
        # if the user is in the war and is not a primary, add the peace option
        elif (user_info['name'] == attackers_others) or (user_info['name'] == defenders_others):
            # CODE HERE
            return None
        # in any other case (unregistered/uninvolved user), return the embed as is, no buttons
        else:
            return await interaction.followup.send(embed=war_embed)

    # === Tech Commands === #

    @cnc.command(name="tech", description="Opens the technology and research menu.")
    @app_commands.describe(tech="The tech to search.")
    async def tech(self, interaction: discord.Interaction, tech: str):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # pull the tech data
        tech = await conn.fetchrow('''SELECT *
                                      FROM cnc_tech
                                      WHERE lower(name) = $1;''', tech.lower())
        # if the tech doesn't exist
        if tech is None:
            # return the error message
            return await interaction.followup.send("No such technology found.")
        # parse the prereqs
        prereqs_raw = str(tech['prereqs'])
        # replace the slash with "or". Slash indicates needing one or the other tech
        prereqs = prereqs_raw.replace("/", " or ")
        # replace the ; with "and". ; indicates needing both techs
        prereqs = prereqs.replace(";", " and ")
        # parse the effects
        effects_raw = str(tech['effect'])
        # replace the ; with a newline and bullet
        effects = "- " + effects_raw.replace(";", ".\n- ")
        # create tech embed
        tech_embed = discord.Embed(title=f"{tech['name']}", description=f"{tech['description']}")
        tech_embed.set_thumbnail(url=f"{tech['image']}")
        tech_embed.add_field(name="Effect", value=f"{effects}", inline=False)
        tech_embed.add_field(name="Prerequisites", value=f"{prereqs}")
        tech_embed.add_field(name="Exclusive with", value=f"{tech['exclusive']}")
        return await interaction.followup.send(embed=tech_embed)

    @cnc.command(name="view_tech_tree", description="Displays researched techs.")
    async def view_tech_tree(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # pull user's tech
        techs = await conn.fetchval('''SELECT tech
                                       FROM cnc_users
                                       WHERE user_id = $1;''', interaction.user.id)
        # map techs
        tech_map = Image.open(fr"{self.tech_directory}CNC Tech Tree.png").convert('RGBA')
        gear_icon = Image.open(fr"{self.tech_directory}CNC Gear Tech Icon.png").convert('RGBA')
        # pull tech info
        for tech in techs:
            tech_info = await conn.fetchrow('''SELECT *
                                               FROM cnc_tech
                                               WHERE name = $1;''', tech)
            gear_cords = tech_info['gear_cords']
            tech_map.paste(gear_icon, (int(gear_cords[0]), int(gear_cords[1])), mask=gear_icon)
        # save image
        # get the running loop, crucial to the map command running without the world enfding
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, tech_map.save, (fr"{self.tech_directory}CNC Tech Map Rendered.png"))

        await interaction.followup.send(file=discord.File(fr"{self.tech_directory}CNC Tech Map Rendered.png"))

    @cnc.command(name="research", description="Begins researching a specified tech.")
    @app_commands.describe(tech="The tech to research.")
    async def research(self, interaction: discord.Interaction, tech: str):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # pull user info
        user_id = interaction.user.id
        user_info = await user_db_info(user_id=user_id)
        # if the user does not exist
        if user_info is None:
            # return a message
            return await interaction.followup.send("You are not a registered member of the CNC system.")
        # check if that tech is an existing tech
        tech_info = await conn.fetchrow('''SELECT *
                                           FROM cnc_tech
                                           WHERE lower(name) = $1;''', tech.lower())
        # if it is not an existing tech
        if tech_info is None:
            # return denial
            return await interaction.followup.send("That is not a recognized tech.")
        # pull techs
        techs = user_info['tech']
        # check if the requested tech is already researched
        if tech.lower() in [t.lower() for t in techs]:
            # return denial
            return await interaction.followup.send("Your scientists have already researched that tech.")
        # check if a tech is already being researched
        researching_tech = await conn.fetchrow('''SELECT *
                                                  FROM cnc_researching
                                                  WHERE user_id = $1;''', user_id)
        if researching_tech is not None:
            # return denial
            return await interaction.followup.send("Your scientists are already researching another tech.")
        # if the tech is not yet unlocked and another tech is not already being researched, add the tech to the research queue
        # determine research time
        # set base research time as four turns
        research_time = 4
        # pull development score
        total_dev = await conn.fetchval('''SELECT AVG(development)
                                           FROM cnc_provinces
                                           WHERE owner_id = $1;''', user_id)
        # pull research time
        research_buff = user_info['research_time']
        # calculate total research time
        research_time += (total_dev // 10) + research_buff
        # if the government subtype is Technocratic, reduce time by one
        if user_info['govt_subtype'] == "Technocratic":
            research_time -= 1
        # if the government type is Equalism, reduce time by one
        if user_info['govt_type'] == "Equalism":
            research_time -= 1
        # ensure the research time is at least 4
        if research_time < 4:
            research_time = 4
        # add to researching database
        await conn.execute('''INSERT INTO cnc_researching
                              VALUES ($1, $2, $3);''',
                           user_id, tech_info['name'], research_time)
        # send confirmation message and research time
        return await interaction.followup.send(f"Your scientists will complete researching {tech_info['name']} "
                                               f"in {research_time} turns.\n"
                                               f"||Research Time = {total_dev // 10} (development) +"
                                               f" {research_buff} (national research time) + 4 (base research time)||")

    @cnc.command(name="researching", description="Displays which tech is being researched.")
    async def researching(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # check if the user exists
        user_id = interaction.user.id
        user_info = await user_db_info(user_id, self.bot.pool)
        # if the user doesn't exist
        if user_info is None:
            # return denial
            return await interaction.followup.send("You are not a registered member of the CNC system.")
        # pull researching information
        researching = await conn.fetchrow('''SELECT *
                                             FROM cnc_researching
                                             WHERE user_id = $1;''', user_id)
        # if there is no tech being researched currently
        if researching is None:
            # return message
            return await interaction.followup.send("No tech is being researched currently.")
        # if there is a tech being researched, send the info
        if researching is not None:
            # return info
            return await interaction.followup.send(f"Scientists are currently researching the {researching['tech']} "
                                                   f"tech. Research will be complete in {researching['turns']} turns.")

    @cnc.command(name="cancel_research", description="Cancels the tech currently being researched.")
    async def cancel_research(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # check if the user exist
        user_id = interaction.user.id
        user_info = await user_db_info(user_id, self.bot.pool)
        # if the user doesn't exist
        if user_info is None:
            # return denial
            return await interaction.followup.send("You are not a registered member of the CNC system.")
        # pull researching information
        researching = await conn.fetchrow('''SELECT *
                                             FROM cnc_researching
                                             WHERE user_id = $1;''', user_id)
        # if there is no tech being researched currently
        if researching is None:
            # return message
            return await interaction.followup.send("No tech is being researched currently.")
        # cancel the research currently underway
        if researching is not None:
            # send cancel to db
            await conn.execute('''DELETE
                                  FROM cnc_researching
                                  WHERE user_id = $1;''', user_id)
            return await interaction.followup.send(f"Scientists are no longer researching {researching['tech']}.")

    # === Government Commands ===

    @cnc.command(name="government", description="Opens the Government menu.")
    async def manage_government(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # pull userinfo
        user_info = await user_db_info(interaction.user.id, conn)
        # check for registration
        if user_info is None:
            return await interaction.followup.send("You are not a registered member of the CNC system.")
        # pull government info
        govt_info = await conn.fetchrow('''SELECT *
                                           FROM cnc_govts
                                           WHERE govt_type = $1
                                             AND govt_subtype = $2;''',
                                        user_info['govt_type'], user_info['govt_subtype'])
        # build embed, populate title with pretitle and nation name, set color to user color,
        # and set description to Discord user.
        govt_embed = discord.Embed(title=f"The {user_info['pretitle']} of {user_info['name']}",
                                   color=discord.Color(int(user_info["color"].lstrip('#'), 16), ),
                                   description=f"Registered nation of "
                                               f"{(self.bot.get_user(user_info['user_id'])).mention}.")
        # populate government type and subtype
        govt_embed.add_field(name="Government", value=f"{user_info['govt_subtype']} {user_info['govt_type']}",
                             inline=False)
        # populate basic info
        govt_embed.add_field(name="National Unrest", value=f"{user_info['unrest']}")
        govt_embed.add_field(name="Stability", value=f"{user_info['stability']}")
        govt_embed.add_field(name="Overextension Limit", value=f"{user_info['overextend_limit']}")
        # populate current authority levels
        govt_embed.add_field(name="Economic Authority",
                             value=f"{user_info['econ_auth']}")
        govt_embed.add_field(name="Military Authority",
                             value=user_info['mil_auth'])
        govt_embed.add_field(name="Political Authority",
                             value=user_info['pol_auth'])
        # populate base authority gains
        govt_embed.add_field(name="Base Economic Authority Gain", value=govt_info['econ_auth'])
        govt_embed.add_field(name="Base Military Authority Gain", value=govt_info['mil_auth'])
        govt_embed.add_field(name="Base Political Authority Gain", value=govt_info['pol_auth'])
        # unrest modifier
        govt_embed.add_field(name="Base Unrest Gain", value=f"{govt_info['unrest_mod']:.0%}")
        # manpower modifier
        govt_embed.add_field(name="Base Manpower Access", value=f"{govt_info['manpower']:.0%}")
        # development cost
        govt_embed.add_field(name="Base Development Cost", value=f"{govt_info['dev_cost']:.0%}")
        # base taxation
        govt_embed.add_field(name="Base Taxation", value=f"{govt_info['tax_level']:.0%}")
        # current tax level
        govt_embed.add_field(name="Current Taxation", value=f"{user_info['tax_level']:.0%}")
        # max tax level
        govt_embed.add_field(name="Maximum Taxation", value=f"{govt_info['tax_level'] + .2:.0%}")
        # public spending
        govt_embed.add_field(name="Public Spending", value=f"{user_info['public_spend']} Economic Authority")
        # military upkeep
        govt_embed.add_field(name="Military Upkeep", value=f"{user_info['mil_upkeep']} Military Authority")
        # establish government modification view
        govt_view = GovernmentModView(interaction.user, interaction, conn, govt_info, govt_embed)
        # send embed and view
        await interaction.followup.send(embed=govt_embed, view=govt_view)

    @cnc.command(name="reform_government", description="Opens the Government reform menu.")
    async def modify_government(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer()
        # establish connection
        conn = self.bot.pool
        # pull userinfo
        user_info = await user_db_info(interaction.user.id, conn)
        # check for registration
        if user_info is None:
            return await interaction.followup.send("You are not a registered member of the CNC system.")
        # create government embed
        # pull government info
        govt_info = await conn.fetchrow('''SELECT *
                                           FROM cnc_govts
                                           WHERE govt_type = $1
                                             AND govt_subtype = $2;''',
                                        user_info['govt_type'], user_info['govt_subtype'])
        # build embed, populate title with pretitle and nation name, set color to user color,
        # and set description to Discord user.
        govt_embed = discord.Embed(title=f"The {user_info['pretitle']} of {user_info['name']}",
                                   color=discord.Color(int(user_info["color"].lstrip('#'), 16), ),
                                   description=f"Registered nation of "
                                               f"{(self.bot.get_user(user_info['user_id'])).mention}.")
        # populate government type and subtype
        govt_embed.add_field(name="Government", value=f"{user_info['govt_subtype']} {user_info['govt_type']}",
                             inline=False)
        # populate basic info
        govt_embed.add_field(name="National Unrest", value=f"{user_info['unrest']}")
        govt_embed.add_field(name="Stability", value=f"{user_info['stability']}")
        govt_embed.add_field(name="Overextension Limit", value=f"{user_info['overextend_limit']}")
        # populate current authority levels
        govt_embed.add_field(name="Economic Authority",
                             value=f"{user_info['econ_auth']}")
        govt_embed.add_field(name="Military Authority",
                             value=user_info['mil_auth'])
        govt_embed.add_field(name="Political Authority",
                             value=user_info['pol_auth'])
        # populate base authority gains
        govt_embed.add_field(name="Base Economic Authority Gain", value=govt_info['econ_auth'])
        govt_embed.add_field(name="Base Military Authority Gain", value=govt_info['mil_auth'])
        govt_embed.add_field(name="Base Political Authority Gain", value=govt_info['pol_auth'])
        # unrest modifier
        govt_embed.add_field(name="Base Unrest Gain", value=f"{govt_info['unrest_mod']:.0%}")
        # manpower modifier
        govt_embed.add_field(name="Base Manpower Access", value=f"{govt_info['manpower']:.0%}")
        # development cost
        govt_embed.add_field(name="Base Development Cost", value=f"{govt_info['dev_cost']:.0%}")
        # base taxation
        govt_embed.add_field(name="Base Taxation", value=f"{govt_info['tax_level']:.0%}")
        # current tax level
        govt_embed.add_field(name="Current Taxation", value=f"{user_info['tax_level']:.0%}")
        # max tax level
        govt_embed.add_field(name="Maximum Taxation", value=f"{govt_info['tax_level'] + .2:.0%}")
        # public spending
        govt_embed.add_field(name="Public Spending", value=f"{user_info['public_spend']} Economic Authority")
        # military upkeep
        govt_embed.add_field(name="Military Upkeep", value=f"{user_info['mil_upkeep']} Military Authority")
        # create view
        await interaction.followup.send(embed=govt_embed,
                                        view=GovernmentReformMenu(interaction.user, interaction, conn, govt_embed))

    @cnc.command(name="designate_capital", description="Designates a province as the national capital.")
    @app_commands.describe(province_id="The province to be designated as the capital.")
    async def designate_capital(self, interaction: discord.Interaction, province_id: int):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        # pull userinfo
        user_info = await user_db_info(interaction.user.id, conn)
        # check for registration
        if user_info is None:
            return await interaction.followup.send("You are not a registered member of the CNC system.")
        # pull province info
        prov_info = await conn.fetchrow('''SELECT *
                                           FROM cnc_provinces
                                           WHERE id = $1;''', province_id)
        # check if province exists
        if prov_info is None:
            return await interaction.followup.send("That is not a valid province ID.")
        # check if user owns province
        if prov_info['owner_id'] != interaction.user.id:
            return await interaction.followup.send("You do not own that province.")
        # check if the user has sufficient Political authority
        if user_info['pol_auth'] < 7:
            return await interaction.followup.send("You do not have sufficient Political "
                                                   "authority to designate a new capital.")
        # check if the user is at war
        war_check = await conn.fetchrow('''SELECT *
                                           FROM cnc_wars
                                           WHERE $1 = ANY (array_cat(attackers, defenders));''', user_info['name'])
        if war_check is not None:
            return await interaction.followup.send("You cannot designate a new Capital while at war.")
        # otherwise, carry on
        # designate new capital and reduce pol_auth
        await conn.execute('''UPDATE cnc_users
                              SET capital  = $1,
                                  pol_auth = pol_auth - 7
                              WHERE user_id = $2;''',
                           province_id, interaction.user.id)
        # if this is the users first capital, reduce unrest by 5 points
        if user_info['capital'] is None:
            await conn.execute('''UPDATE cnc_users
                                  SET unrest = unrest - 5
                                  WHERE user_id = $1;''', interaction.user.id)
        # send confirmation
        return await interaction.followup.send(f"{prov_info['name']} is now the Capital of {user_info['name']}.")

    # === Moderator Commands ===

    @commands.command()
    @commands.is_owner()
    async def cnc_give_province(self, ctx, user: discord.Member, province_id: int):
        # establish connection
        conn = self.bot.pool
        # call user info
        user_info = await user_db_info(user.id, conn)
        # check if such a user exists
        if user_info is None:
            return await ctx.send("No such user.")
        # pull province info
        prov_info = await conn.fetchrow('''SELECT *
                                           FROM cnc_provinces
                                           WHERE id = $1;''', province_id)
        # check if province exists
        if prov_info is None:
            return await ctx.send("That is not a valid province ID.")
        # if someone owns the province, deny
        if prov_info['owner_id'] != 0:
            return await ctx.send("You cannot give a province that someone owns.")
        # otherwise, carry on
        try:
            await conn.execute('''UPDATE cnc_provinces
                                  SET owner_id    = $1,
                                      occupier_id = $1
                                  WHERE id = $2;''',
                               user.id, province_id)
            await map_color(province_id, user_info['color'], conn)
        except asyncpg.PostgresError as e:
            raise e
        return await ctx.send(f"{user_info['name']} granted ownership of {prov_info['name']} (ID: {province_id}).")

    @commands.command()
    @commands.is_owner()
    async def cnc_research_tech(self, ctx, user: discord.Member, tech: str):
        # establish connection
        conn = self.bot.pool
        # call user info
        user_info = await user_db_info(user.id, conn)
        # check if such a user exists
        if user_info is None:
            return await ctx.send("No such user.")
        # otherwise, carry on
        # search for tech
        tech_info = await conn.fetchrow('''SELECT *
                                           FROM cnc_tech
                                           WHERE lower(name) = $1;''', tech.lower())
        # if the tech name is wrong
        if tech_info is None:
            return await ctx.send("No such tech.")
        # otherwise, carry on
        techs = user_info['tech']
        # if the user already has the tech, return denial
        if tech.lower() in [t.lower() for t in techs]:
            return await ctx.send("That user already researched that tech.")
        # otherwise, carry on
        try:
            # add the tech to their list
            await conn.execute('''UPDATE cnc_users
                                  SET tech = tech || $1
                                  WHERE user_id = $2;''', [tech], user.id)
            # execute tech db call
            if tech_info['db_call'] != 'NULL':
                await conn.execute(tech_info['db_call'], user.id)
        except Exception as error:
            raise error
        # send confirmation
        return await ctx.send(f"{tech_info['name']} has been researched for {user_info['name']} ({user.display_name}).")

    @commands.command()
    @commands.is_owner()
    async def cnc_forget_tech(self, ctx, user: discord.Member, tech: str):
        # establish connection
        conn = self.bot.pool
        # call user info
        user_info = await user_db_info(user.id, conn)
        # check if such a user exists
        if user_info is None:
            return await ctx.send("No such user.")
        # otherwise, carry on
        # search for tech
        tech_info = await conn.fetchrow('''SELECT *
                                           FROM cnc_tech
                                           WHERE lower(name) = $1;''', tech.lower())
        # if the tech name is wrong
        if tech_info is None:
            return await ctx.send("No such tech.")
        # otherwise, carry on
        techs = user_info['tech']
        # if the user already has the tech, return denial
        if tech.lower() not in [t.lower() for t in techs]:
            return await ctx.send("That user has not yet researched that tech.")
        # otherwise, carry on
        # remove the tech from their list
        await conn.execute('''UPDATE cnc_users
                              SET tech = array_remove(tech, $1)
                              WHERE user_id = $2;''', tech, user.id)
        # execute tech db call, replacing the pluses with minuses and the minuses with pluses
        db_call = "".join("+" if c == "-" else "-" if c == "+" else c for c in tech_info['db_call'])
        await conn.execute(db_call, user.id)
        # send confirmation
        return await ctx.send(
            f"{tech_info['name']} has been forgotten for {user_info['name']} ({user.display_name}).")

    @commands.command()
    @commands.has_role(928889638888812586)
    async def cnc_give_authority(self, ctx, user: discord.Member, authority: str, amount: int):
        # establish connection
        conn = self.bot.pool
        # check for user
        user_info = user_db_info(user.id, conn)
        # set authority
        authority = authority.lower()
        if user_info is None:
            return await ctx.send("No such user registered.")
        # otherwise, carry on
        if authority not in ['economic', 'military', 'political']:
            return await ctx.send("That this not a valid authority name.")
        # commit authority
        if authority == "economic":
            await conn.execute('''UPDATE cnc_users
                                  SET econ_auth = econ_auth + $1
                                  WHERE user_id = $2;''',
                               amount, user.id)
        if authority == "military":
            await conn.execute('''UPDATE cnc_users
                                  SET mil_auth = mil_auth + $1
                                  WHERE user_id = $2;''',
                               amount, user.id)
        if authority == "political":
            await conn.execute('''UPDATE cnc_users
                                  SET pol_auth = pol_auth + $1
                                  WHERE user_id = $2;''',
                               amount, user.id)
        return await ctx.send(f"{amount} {authority} authority granted to {user.display_name}.")

    @commands.command()
    @commands.has_role(928889638888812586)
    async def cnc_blacklist(self, ctx, user: discord.Member):
        # establish connection
        conn = self.bot.pool
        # pull userinfo
        user_info = user_db_info(user.id, conn)
        # check for user
        if user_info is None:
            return await ctx.send("No such user registered.")
        # otherwise, blacklist
        await conn.execute('''UPDATE cnc_users
                              SET blacklisted = True
                              WHERE user_id = $1;''',
                           user.id)
        return await ctx.send(f"{user.display_name} has been blacklisted.")

    @commands.command()
    @commands.has_role(928889638888812586)
    async def cnc_whitelist(self, ctx, user: discord.Member):
        # establish connection
        conn = self.bot.pool
        # pull userinfo
        user_info = user_db_info(user.id, conn)
        # check for user
        if user_info is None:
            return await ctx.send("No such user registered.")
        # otherwise, blacklist
        await conn.execute('''UPDATE cnc_users
                              SET blacklisted = FALSE
                              WHERE user_id = $1;''',
                           user.id)
        return await ctx.send(f"{user.display_name} has been whitelisted.")

    # === Administrator Commands ===
    @commands.command()
    @commands.is_owner()
    async def cnc_reset_map(self, ctx):
        map_image = Image.open(fr"{self.map_directory}wargame_blank_save.png").convert("RGBA")
        map_image.save(fr"{self.map_directory}wargame_provinces.png")
        await ctx.send("Map reset.")

    @commands.command()
    @commands.is_owner()
    async def cnc_map_check(self, ctx):
        async with ctx.typing():
            map = Image.open(fr"{self.map_directory}wargame_blank_save.png").convert("RGBA")
            map.save(fr"{self.map_directory}wargame_provinces.png")
            conn = self.bot.pool
            users = await conn.fetch('''SELECT user_id, color
                                        FROM cnc_users;''')
            for u in users:
                color = u['color']
                owned_provinces = await conn.fetch('''SELECT *
                                                      FROM cnc_provinces
                                                      WHERE owner_id = $1;''', u['user_id'])
                for p in owned_provinces:
                    p_id = p['id']
                    if p['occupier_id'] == u['user_id']:
                        await map_color(p_id, color, conn)
                        await ctx.send(f"{p['name']} colored.")
                    elif p['occupier_id'] == 0:
                        await self.occupy_color(p_id, '#000000', color)
                    elif p['occupier_id'] != u['user_id']:
                        occupier_color = await conn.fetchrow('''SELECT color
                                                                FROM cnc_users
                                                                WHERE user_id = $1;''',
                                                             p['occupier_id'])
                        await self.occupy_color(p_id, occupier_color, color)
            return await ctx.send("All provinces checked and colored.")

    @commands.command()
    @commands.is_owner()
    async def cnc_permanent_delete_user(self, ctx, user: discord.Member):
        # sent a confirmation message
        delete_confirm = await ctx.send(f"Are you certain you would like to delete {user.name} "
                                        f"from the Command and Conquest System?")

        # wait for a confirmation message
        def confirmation_check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji)

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30, check=confirmation_check)
            if str(reaction.emoji) != "\U00002705":
                return await ctx.send("Must confirm deletion with: \U00002705")
        except asyncio.TimeoutError:
            return await delete_confirm.edit(content=f"Permanent deletion of {user.name} "
                                                     f"from the Command and Conquest System aborted.")
        conn = self.bot.pool
        usercheck = await conn.fetchrow('''SELECT *
                                           FROM cnc_users
                                           WHERE user_id = $1;''', user.id)
        if usercheck is None:
            return await ctx.send("No such user in the CNC system.")
        try:
            await conn.execute('''DELETE
                                  FROM cnc_users
                                  WHERE user_id = $1;''', user.id)
            await conn.execute('''DELETE
                                  FROM cnc_armies
                                  WHERE owner_id = $1;''', user.id)
            await conn.execute('''UPDATE cnc_provinces
                                  SET owner_id    = 0,
                                      occupier_id = 0,
                                      development = floor((random() * 9) + 1),
                                      citizens    = floor((random() * 10000) + 1000),
                                      structures  = text[],
                                      fort_level  = 0
                                  WHERE owner_id = $1
                                    AND occupier_id = $1;''', user.id)
            await conn.execute('''DELETE
                                  FROM cnc_researching
                                  WHERE user_id = $1;''', user.id)
            await delete_confirm.delete()
        except asyncpg.PostgresError as error:
            raise error
        return await ctx.send(f"Permanent deletion of {user.name} "
                              "from the Command and Conquest System completed.")

    @commands.command()
    @commands.is_owner()
    async def cnc_roll_development(self, ctx):
        # establish connection
        conn = self.bot.pool
        # pull terrain data
        terrain_rolls = await conn.fetch('''SELECT *
                                            FROM cnc_terrains
                                            WHERE base_development IS NOT NULL;''')
        # create terrain dict
        terrain_info = {}
        for t in terrain_rolls:
            terrain_info.update({t['id']: t['base_development']})
        # pull provinces
        all_provinces = await conn.fetch('''SELECT *
                                            FROM cnc_provinces;''')
        # for every province, set the development = (bd + 1d6) + 1d2 (river) + 1d3 (coast)
        total_p = 0
        for p in all_provinces:
            # define the bd as per the terrain
            bd = terrain_info[p['terrain']]
            # add 1d2 if river
            if p['river']:
                bd += randrange(1, 2)
            # add 1d3 if coastal
            if p['coast']:
                bd += randrange(1, 3)
            # generate number
            rng = randrange(1, 6)
            total_dev = bd + rng
            await conn.execute('''UPDATE cnc_provinces
                                  SET development = $1
                                  WHERE id = $2;''', total_dev, p['id'])
            total_p += 1
        return await ctx.send(f"{total_p} provinces have been set.")

    @commands.command()
    @commands.is_owner()
    async def cnc_populate_world(self, ctx):
        # establish connection
        conn = self.bot.pool
        # set population = base dev * a random number between 500 and 1500
        async with ctx.typing():
            await conn.execute('''UPDATE cnc_provinces
                                  SET citizens = development * (RANDOM() * (1500 - 500) + 500);''')
        return await ctx.send("World populated.")


async def setup(bot: Shard):
    # define the cog and add the cog
    cog = CNC(bot)
    await bot.add_cog(cog)