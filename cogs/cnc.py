from random import randrange, randint
import asyncpg
from discord import app_commands, Interaction
from ShardBot import Shard
import discord
from discord.ext import commands, tasks
import asyncio
from PIL import Image, ImageColor, ImageDraw
from base64 import b64encode
import requests
from discord.ui import View
import math
from customchecks import SilentFail


def plus_minus(number: int) -> str:
    """Adds a plus and minus to a number, turning it into a string."""
    if not isinstance(number, int):
        raise TypeError
    if number >= 0:
        return str(f"+{number}")
    elif number < 0:
        return str(f"-{number}")

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
        troop_count = await conn.fetchrow('''SELECT SUM(troops) FROM cnc_armies WHERE location = $1;''',
                                          prov_info['id'])
        # parse out troop count
        if troop_count['sum'] is None:
            troop_count = 0
        else:
            troop_count = f"{troop_count['sum']:,}"
        # parse structures
        if prov_info['structures'] is None:
            structures = "None"
        elif not prov_info['structures']:
            structures = "None"
        else:
            structures = ",".join(p for p in prov_info['structures'])
        army_list = await conn.fetchrow('''SELECT COUNT(*) FROM cnc_armies WHERE location = $1''', prov_info['id'])
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
                                                             f"in {army_list['count']} armies.")
        prov_embed.add_field(name="Terrain", value=f"{await terrain_name(prov_info['terrain'], conn)}" + river)
        prov_embed.add_field(name="Trade Good", value=f"{prov_info['trade_good']}")
        prov_embed.add_field(name="Citizens", value=f"{prov_info['citizens']:,}")
        prov_embed.add_field(name="Production\n(last turn)", value=f"{prov_info['production']:,.3}")
        prov_embed.add_field(name="Development", value=f"{prov_info['development']}")
        prov_embed.add_field(name="Structures", value=f"{structures}")
        return prov_embed
        
async def user_db_info(user_id: int, conn: asyncpg.Pool) -> asyncpg.Record:
        """Pulls user info from the database using Discord user ID."""
        # pull the user data
        user_info = await conn.fetchrow('''SELECT * FROM cnc_users WHERE user_id = $1;''', user_id)
        return user_info

async def terrain_name(terrain_id: int, conn: asyncpg.Pool) -> str:
        # make terrain db call
        terrain_name = await conn.fetchrow('''SELECT name FROM cnc_terrains WHERE id = $1;''', terrain_id)
        # return name string
        return str(terrain_name['name'])

async def map_color(province: int, hexcode: str, conn: asyncpg.Pool):
    map_directory = r"/root/Shard/CNC/Map Files/Maps/"
    province_directory = r"/root/Shard/CNC/Map Files/Province Layers/"
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
        req_tech = await conn.fetchrow('''SELECT * FROM cnc_tech WHERE effect = $1;''',
                                       f"Unlocks {structure} structure.")
        # if the user does not have the required tech
        if req_tech['name'] not in user_info['tech']:
            return await interaction.response.send_message(content=f"The **{req_tech['name']}** tech must be "
                                                                   f"researched before constructing a {structure}.")
        # check if the user has enough authority of that type to expend
        structure_info = await conn.fetchrow('''SELECT * FROM cnc_structures WHERE name = $1;''', structure)
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
            provs_with_cities = await conn.fetchrow('''SELECT * FROM cnc_provinces 
                    WHERE owner_id = $1 AND 'City' = ANY(structures)''', interaction.user.id)
            if provs_with_cities is not None:
                return await interaction.response.send_message(content=f"Free Cities can construct only one City. "
                                                       f"{user_info['name']} maintains City {provs_with_cities['name']}"
                                                       f" (ID: {provs_with_cities['id']}).")
        # if all checks are met, construct and bill cost
        try:
            await conn.execute('''UPDATE cnc_provinces SET structures = structures || $1 WHERE id = $2;''',
                               [structure], prov_info['id'])
            if structure_info['authority'] == "Military":
                await conn.execute('''UPDATE cnc_users SET mil_auth = mil_auth - $1 WHERE user_id = $2;''',
                                   structure_info['cost'], interaction.user.id)
            elif structure_info['authority'] == "Economic":
                await conn.execute('''UPDATE cnc_users SET econ_auth = econ_auth - $1 WHERE user_id = $2;''',
                                   structure_info['cost'], interaction.user.id)
            if structure == "Fort":
                await conn.execute('''UPDATE cnc_provinces SET fort_level = $1 WHERE id = $2;''',
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
                                                                               self.user_info,self.pool))

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

    # define callback
    async def callback(self, interaction: discord.Interaction):
        structure = self.values[0]
        prov_info = self.prov_info
        province_id = prov_info['id']
        conn = self.pool
        # otherwise cary on
        # remove the structure from the province
        await conn.execute('''UPDATE cnc_provinces SET structures = array_remove(structures, $1) WHERE id = $2;''',
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
        govt_info = await conn.fetchrow('''SELECT * FROM cnc_govts WHERE govt_type = $1 AND govt_subtype = $2;''',
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
        await conn.execute('''UPDATE cnc_users SET econ_auth = econ_auth - $1 WHERE user_id = $2;''',
                           int(boost_cost), interaction.user.id)
        await conn.execute('''UPDATE cnc_provinces SET development = development + 1 WHERE id = $1;''',
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
        govt_info = await conn.fetchrow('''SELECT * FROM cnc_govts WHERE govt_type = $1 AND govt_subtype = $2;''',
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
        await conn.execute('''UPDATE cnc_users SET pol_auth = pol_auth - $1 WHERE user_id = $2;''',
                           int(boost_cost), interaction.user.id)
        await conn.execute('''UPDATE cnc_provinces SET development = development + 1 WHERE id = $1;''',
                           province_id)
        # define and reset to owned province
        await interaction.response.edit_message(content=None,
                                                view=self.prov_owned_view,
                                                embed= await create_prov_embed(prov_info, conn))
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
        govt_info = await conn.fetchrow('''SELECT * FROM cnc_govts WHERE govt_type = $1 AND govt_subtype = $2;''',
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
        await conn.execute('''UPDATE cnc_users SET mil_auth = mil_auth - $1 WHERE user_id = $2;''',
                           int(boost_cost), interaction.user.id)
        await conn.execute('''UPDATE cnc_provinces SET development = development + 1 WHERE id = $1;''',
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
        await conn.execute('''UPDATE cnc_provinces SET development = development - 1 WHERE id = $1;''',
                           province_id)
        await conn.execute('''UPDATE cnc_users SET econ_auth = econ_auth + $1 WHERE user_id = $2;''',
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
        await conn.execute('''UPDATE cnc_provinces SET development = development - 1 WHERE id = $1;''',
                           province_id)
        await conn.execute('''UPDATE cnc_users SET pol_auth = pol_auth + $1 WHERE user_id = $2;''',
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
        await conn.execute('''UPDATE cnc_provinces SET development = development - 1 WHERE id = $1;''',
                           province_id)
        await conn.execute('''UPDATE cnc_users SET mil_auth = mil_auth + $1 WHERE user_id = $2;''',
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
        await conn.execute('''UPDATE cnc_users SET unrest = unrest + 1 WHERE user_id = $1;''',
                           interaction.user.id)
        await conn.execute('''UPDATE cnc_provinces SET owner_id = 0, occupier_id = 0, 
                   development = floor((random()*9)+1), citizens = floor((random()*10000)+1000), structures = '{}',
                   fort_level = 0 WHERE id = $1;''', province_id)
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
        war_check = await conn.fetchrow('''SELECT * FROM cnc_wars WHERE $1 = ANY(members);''', user_info['name'])
        if war_check is not None:
            return await interaction.response.send_message("You cannot abandon provinces while at war.")
        # check to make sure that the user will have > 1 province after
        prov_owned_count = await conn.fetchrow('''SELECT count(id) FROM cnc_provinces WHERE owner_id = $1;''',
                                               interaction.user.id)
        if prov_owned_count['count'] - 1 < 1:
            return await interaction.response.send_message("You cannot abandon your last province.")
        # otherwise, carry on
        abandon_province_view = AbandonConfirm(interaction.user, prov_info, user_info, conn)
        abandon_province_view.interaction = interaction
        await interaction.response.edit_message(view=abandon_province_view, embed=None, content="**Confirm below.**")

class UnownedProvince(View):

    def __init__(self, author: discord.User, province_db: asyncpg.Record, user_info: asyncpg.Record, pool: asyncpg.Pool):
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
        prov_owned_count = await conn.fetchrow('''SELECT count(id) FROM cnc_provinces WHERE owner_id = $1;''',
                                              user_id)
        if prov_owned_count['count'] < 15:
            return await interaction.response.send_message("You cannot colonize until you own at least 15 provinces.")
        # check if the province is on the coast or bordering a province owned by the nation
        bordering_check = await conn.fetch('''SELECT * FROM cnc_provinces 
        WHERE $1 = ANY(bordering) and owner_id = $2;''', province_id, user_id)
        if (not bordering_check) and (prov_info['coast'] is False):
            return await interaction.response.send_message("You cannot cannot colonize a province that you do not "
                                                           "border or that is not a costal province.")
        # calculate cost
        cost = 1
        # cost of colonization = (5 + provinces count) - 25, minimum 1, maximum 10
        cost += (5 + prov_owned_count['count']) - 25
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
        if prov_owned_count['count'] > user_info['overextend_limit']:
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
        await conn.execute('''UPDATE cnc_users SET econ_auth = econ_auth - $1, mil_auth = mil_auth - $1, 
        pol_auth = pol_auth - $1 WHERE user_id = $2;''', cost, interaction.user.id)
        await conn.execute('''UPDATE cnc_provinces SET owner_id = $1, occupier_id = $1, development = $3 
        WHERE id = $2;''', interaction.user.id, province_id, dev)
        await map_color(province_id, user_info['color'])
        await interaction.response.edit_message(content=None,
                                                view=prov_owned_view,
                                                embed=await create_prov_embed(prov_info, conn))
        return await interaction.followup.send(f"{prov_info['name']} (ID: {province_id}) "
                                                       f"has been successfully colonized.")

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

    @discord.ui.button(label="Authority", style=discord.ButtonStyle.blurple)
    async def authority(self, interaction: discord.Interaction, button: discord.Button):
        # defer interaction
        await interaction.response.defer()
        # clear emebed
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
        troops = await conn.fetchrow('''SELECT SUM(troops) FROM cnc_armies WHERE owner_id = $1;''', user_id)
        armies = await conn.fetchrow('''SELECT COUNT(*) FROM cnc_armies WHERE owner_id = $1;''', user_id)
        generals = await conn.fetchrow('''SELECT COUNT(*) FROM cnc_generals WHERE owner_id = $1;''', user_id)
        total_manpower = await conn.fetchrow('''SELECT SUM(citizens) FROM cnc_provinces WHERE owner_id = $1;''',
                                             user_id)
        # populate troops and armies
        self.doss_embed.add_field(name="=======================MILITARY======================",
                             value="Information about your nation's military.", inline=False)
        self.doss_embed.add_field(name="Troops", value=f"{troops['sum']:,}")
        self.doss_embed.add_field(name="Armies", value=f"{armies['count']}")
        self.doss_embed.add_field(name="Generals", value=f"{generals['count']}")
        # populate manpower
        self.doss_embed.add_field(name="Manpower \n(Manpower Access)", value=f"{self.user_info['manpower']:,} "
                                                                        f"({self.user_info['manpower_access']}%)")
        self.doss_embed.add_field(name="Manpower Regen",
                             value=f"{math.floor(total_manpower['sum'] * (self.user_info['manpower_regen'] / 100)):,} "
                                   f"({self.user_info['manpower_regen']}%)")
        self.doss_embed.add_field(name="Total Manpower", value=f"{total_manpower['sum']:,}")
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
        self.doss_embed.add_field(name="Taxation Level", value=f"{self.user_info['tax_level']}%")
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
        # populate unrest, stability, overextension
        self.doss_embed.add_field(name="=====================GOVERNMENT===================",
                             value="Information about your nation's government.", inline=False)
        self.doss_embed.add_field(name="National Unrest", value=f"{self.user_info['unrest']}")
        self.doss_embed.add_field(name="Stability", value=f"{self.user_info['stability']}")
        self.doss_embed.add_field(name="Overextension Limit", value=f"{self.user_info['overextend_limit']}")
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
        alliances = await conn.fetch('''SELECT * FROM cnc_alliances WHERE $1 = ANY(members);''',
                                     self.user_info['name'])
        wars = await conn.fetch('''SELECT * FROM cnc_wars WHERE $1 = ANY(members);''',
                                self.user_info['name'])
        trade_pacts = await conn.fetch('''SELECT * FROM cnc_trade_pacts WHERE $1 = ANY(members);''',
                                       self.user_info['name'])
        military_access = await conn.fetch('''SELECT * FROM cnc_military_access WHERE $1 = ANY(members);''',
                                           self.user_info['name'])

        def parse_relations(relations):
            if not relations:
                output = "None"
                return str(output)
            else:
                output = ""
                for relation in relations:
                    buffer_output = ", ".join([r for r in relation['members'] if r != self.user_info['name']])
                    output += buffer_output
                return str(output)

        allies = parse_relations(alliances)
        wars = parse_relations(wars)
        trade_pacts = parse_relations(trade_pacts)
        military_access = parse_relations(military_access)
        # populate relations
        self.doss_embed.add_field(name="=====================RELATIONS=====================",
                             value="Information about your nation's diplomatic relationships.", inline=False)
        self.doss_embed.add_field(name="Allies", value=f"{allies}")
        self.doss_embed.add_field(name="Wars", value=f"{wars}")
        self.doss_embed.add_field(name="Trade Pacts", value=f"{trade_pacts}")
        self.doss_embed.add_field(name="Military Access", value=f"{military_access}")
        # update
        await interaction.edit_original_response(embed=self.doss_embed)

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

    @ discord.ui.button(label="Boost Stability", style=discord.ButtonStyle.blurple, emoji="\U00002696")
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
        await conn.execute('''UPDATE cnc_users SET stability_limit = stability_limit - 1 WHERE user_id = $1;''',
                           interaction.user.id)
        # pay pol auth
        await conn.execute('''UPDATE cnc_users SET pol_auth = pol_auth - 1 WHERE user_id = $1;''',
                           interaction.user.id)
        await conn.execute('''UPDATE cnc_users SET stability = stability + $1 WHERE user_id = $2;''',
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
            await conn.execute('''UPDATE cnc_users SET tax_level = tax_level - .01 WHERE user_id = $1;''',
                               self.author.id)
            # send confirmation
            await interaction.followup.send(f"Your tax rate is now {self.user_info['tax_level']-.01:.0%}!")
            # update embed
            self.govt_embed.set_field_at(-4, name="Current Tax Level", value=f"{self.user_info['tax_level']-.01:.0%}")
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
            await conn.execute('''UPDATE cnc_users SET tax_level = tax_level + .01 WHERE user_id = $1;''',
                               self.author.id)
            # send confirmation
            await interaction.followup.send(f"Your tax rate is now {self.user_info['tax_level']+.01:.0%}!")
            # update embed
            self.govt_embed.set_field_at(-4, name="Current Tax Level", value=f"{self.user_info['tax_level']+.01:.0%}")
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
            await conn.execute('''UPDATE cnc_users SET public_spend = public_spend - 1 WHERE user_id = $1;''',
                               self.author.id)
            # update embed
            self.govt_embed.set_field_at(-2, name="Public Spending",
                                         value=f"{self.user_info['public_spend']-1} Economic Authority")
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
            await conn.execute('''UPDATE cnc_users SET public_spend = public_spend + 1 WHERE user_id = $1;''',
                               self.author.id)
            # update embed
            self.govt_embed.set_field_at(-2, name="Public Spending",
                                         value=f"{self.user_info['public_spend']+1} Economic Authority")
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
            await conn.execute('''UPDATE cnc_users SET mil_upkeep = mil_upkeep - 1 WHERE user_id = $1;''',
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
            await conn.execute('''UPDATE cnc_users SET mil_upkeep = mil_upkeep + 1 WHERE user_id = $1;''',
                               self.author.id)
            # update embed
            self.govt_embed.set_field_at(-1, name="Military Upkeep",
                                         value=f"{self.user_info['mil_upkeep'] + 1} Military Authority")
            # enable decrease button
            self.decrease.disabled = False
            # update embed
            await interaction.edit_original_response(embed=self.govt_embed, view=self)


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
        user_data = await conn.fetchrow('''SELECT * FROM cnc_users WHERE user_id = $1;''', interaction.user.id)
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
            check_color_taken = await conn.fetchrow('''SELECT * FROM cnc_users WHERE color = $1;''', color)
            if check_color_taken is not None:
                return await interaction.followup.send("That color is already taken. "
                                                       "Please register with a different color.")
            # pull all colors
            pull_all_colors = await conn.fetch('''SELECT name, color FROM cnc_users;''')
            # check each color
            for c in pull_all_colors:
                color_check = c['color']
                if self.color_difference(c['color'], color_check) > 50:
                    return await interaction.followup.send(f"Your selected color, {color}, is too similar to an "
                                                           f"existing color, registered to {c['name']} ({c['color']}).")

            if color in self.banned_colors:
                return await interaction.followup.send("That color is a restricted color. "
                                                       "Please register with a different color.")
            for c in self.banned_colors:
                if self.color_difference(c, color) > 25:
                    return await interaction.followup.send(f"That color is too similar to a banned color, {c}.")
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

    @cnc.command(name="change_color", description="Changes your nation's color on the map.")
    @app_commands.checks.cooldown(1, 30)
    @app_commands.describe(color="The hex code of your new map color. Include the '#'.")
    async def recolor(self, interaction: discord.Interaction, color: str):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # deny access if in DMs
        if not interaction.guild:
            return commands.NoPrivateMessage
        # establish connection
        conn = self.bot.pool
        # pull userinfo
        user_info = await user_db_info(interaction.user.id)
        # check for registration
        if user_info is None:
            return await interaction.followup.send("You are not a registered member of the CNC system.")
        # check if the color is taken, banned, or even a color
        check_color_taken = await conn.fetchrow('''SELECT * FROM cnc_users WHERE color = $1;''', color)
        if check_color_taken is not None:
            return await interaction.followup.send("That color is already taken. "
                                                   "Please select a different color.")
        # pull all colors
        pull_all_colors = await conn.fetch('''SELECT name, color FROM cnc_users;''')
        # check each color
        for c in pull_all_colors:
            color_check = c['color']
            if self.color_difference(color_check, color) < 50:
                return await interaction.followup.send(f"Your selected color, {color}, is too similar to an "
                                                       f"existing color, registered to {c['name']} ({c['color']}).")

        if color in self.banned_colors:
            return await interaction.followup.send("That color is a restricted color. "
                                                   "Please select a different color.")
        for c in self.banned_colors:
            if self.color_difference(c, color) < 50:
                return await interaction.followup.send(f"That color is too similar to a banned color, {c}.")
        # try and get the color from the hex code
        try:
            ImageColor.getrgb(color)
        except ValueError:
            # if the color isn't a real hex code, return that they need to get the right hex code
            return await interaction.followup.send(
                "That doesn't appear to be a valid hex color code. Include the `#` symbol.")
        # if the color is valid, update the database
        await conn.execute('''UPDATE cnc_users SET color = $1 WHERE user_id = $2;''', color, interaction.user.id)
        # get all provinces
        all_provinces = await conn.fetch('''SELECT * FROM cnc_provinces WHERE owner_id = $1;''', interaction.user.id)
        for p in all_provinces:
            p_id = p['id']
            if p['occupier_id'] == user_info['user_id']:
                await self.map_color(p_id, color, False)
            elif p['occupier_id'] == 0:
                await self.occupy_color(p_id, '#000000', color)
            elif p['occupier_id'] != user_info['user_id']:
                occupier_color = await conn.fetchrow('''SELECT color FROM cnc_users WHERE user_id = $1;''',
                                                     p['occupier_id'])
                await self.occupy_color(p_id, occupier_color, color)
        return await interaction.followup.send(f"Color successfully changed to {color}!")

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
        elif user is not None:
            user_info = await user_db_info(user.id, self.bot.pool)
            if user_info is None:
                return await interaction.followup.send(f"That user is not a registered player of the CNC system.",
                                                       ephemeral=True)
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
        alliances = await conn.fetch('''SELECT * FROM cnc_alliances WHERE $1 = ANY(members);''',
                                     user_info['name'])
        wars = await conn.fetch('''SELECT * FROM cnc_wars WHERE $1 = ANY(members);''',
                                user_info['name'])
        trade_pacts = await conn.fetch('''SELECT * FROM cnc_trade_pacts WHERE $1 = ANY(members);''',
                                       user_info['name'])
        military_access = await conn.fetch('''SELECT * FROM cnc_military_access 
        WHERE $1 = ANY(members);''', user_info['name'])

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
        user_embed.add_field(name="Trade Pacts", value=f"{trade_pacts}")
        user_embed.add_field(name="Military Access", value=f"{military_access}")
        # send the embed
        return await interaction.followup.send(embed=user_embed)

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
                                                     embed= await create_prov_embed(prov_info, conn))

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
        army_info = await conn.fetchrow('''SELECT * FROM cnc_armies WHERE army_id = $1;''', army_id)
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
            general_info = await conn.fetchrow('''SELECT * FROM cnc_generals WHERE general_id = $1;''', general)
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
        army_info = await conn.fetch('''SELECT * FROM cnc_armies WHERE owner_id = $1;''', interaction.user.id)
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

    # === Tech Commands === #

    @cnc.command(name="technology", description="Opens the technology menu.")
    async def technology(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer(thinking=True)
        # establish connection
        conn = self.bot.pool
        #

    @cnc.command(name="tech", description="Opens the technology and research menu.")
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
            tech_map.paste(gear_icon, (int(gear_cords[0]), int(gear_cords[1])) , mask=gear_icon)
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
            return await interaction.followup.send("Your scientists have already researched that tech.")
        # check if a tech is already being researched
        researching_tech = await conn.fetchrow('''SELECT * FROM cnc_researching WHERE user_id = $1;''', user_id)
        if researching_tech is not None:
            # return denial
            return await interaction.followup.send("Your scientists are already researching another tech.")
        # if the tech is not yet unlocked and another tech is not already being researched, add the tech to the research queue
        # determine research time
        # set base research time as four turns
        research_time = 4
        # pull development score
        total_dev = await conn.fetchrow('''SELECT AVG(development) FROM cnc_provinces WHERE owner_id = $1;''', user_id)
        total_dev = total_dev['avg']
        # pull research time
        research_buff = user_info['research_time']
        # calculate total research time
        research_time += (total_dev//10) + research_buff
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
        await conn.execute('''INSERT INTO cnc_researching VALUES($1,$2,$3);''',
                           user_id, tech_info['name'], research_time)
        # send confirmation message and research time
        return await interaction.followup.send(f"Your scientists will complete researching {tech_info['name']} "
                                               f"in {research_time} turns.\n"
                                        f"||Research Time = {total_dev//10} (development) +"
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
        govt_info = await conn.fetchrow('''SELECT * FROM cnc_govts WHERE govt_type = $1 AND govt_subtype = $2;''',
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
        govt_embed.add_field(name="Maximum Taxation", value=f"{govt_info['tax_level']+.2:.0%}")
        # public spending
        govt_embed.add_field(name="Public Spending", value=f"{user_info['public_spend']} Economic Authority")
        # military upkeep
        govt_embed.add_field(name="Military Upkeep", value=f"{user_info['mil_upkeep']} Military Authority")
        # establish government modification view
        govt_view = GovernmentModView(interaction.user, interaction, conn, govt_info, govt_embed)
        # send embed and view
        await interaction.followup.send(embed=govt_embed, view=govt_view)

    @cnc.command(name="change_government", description="Opens the Government modification menu.")
    async def modify_government(self, interaction: discord.Interaction):
        # defer interaction
        await interaction.response.defer()
        # establish connection
        conn = self.pool
        # pull userinfo
        user_info = await user_db_info(interaction.user.id, conn)
        # check for registration
        if user_info is None:
            return await interaction.followup.send("You are not a registered member of the CNC system.")
        # define special notes for government types
        monarchy_note = "Capital Province Fort gains two Defense Levels."
        republic_note = "Cost of Diplomatic Relations reduced by two."
        democracy_note = "Cost of Government Modification decreased by two."
        equalism_note = "Technology takes one less turn to research, enemies can declare war for free."
        anarchy_note = "Civil War chance reduced by 100%, Revolution chance increased by 25%."
        # create government embed
        # pull government info
        govt_info = await conn.fetchrow('''SELECT * FROM cnc_govts WHERE govt_type = $1 AND govt_subtype = $2;''',
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
        govt_embed.add_field(name="Economic Authority            Military Authority            Political Authority",
                             value=f"{user_info['econ_auth']}            {user_info['mil_auth']}            {user_info['pol_auth']}", inline=False)
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
        #

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
        prov_info = await conn.fetchrow('''SELECT * FROM cnc_provinces WHERE id = $1;''', province_id)
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
        war_check = await conn.fetchrow('''SELECT * FROM cnc_wars WHERE $1 = ANY(members);''', user_info['name'])
        if war_check is not None:
            return await interaction.followup.send("You cannot designate a new Capital while at war.")
        # otherwise, carry on
        # designate new capital and reduce pol_auth
        await conn.execute('''UPDATE cnc_users SET capital = $1, pol_auth = pol_auth - 7 WHERE user_id = $2;''',
                           province_id, interaction.user.id)
        # if this is the users first capital, reduce unrest by 5 points
        if user_info['capital'] is None:
            await conn.execute('''UPDATE cnc_users SET unrest = unrest - 5 WHERE user_id = $1;''', interaction.user.id)
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
        prov_info = await conn.fetchrow('''SELECT * FROM cnc_provinces WHERE id = $1;''', province_id)
        # check if province exists
        if prov_info is None:
            return await ctx.send("That is not a valid province ID.")
        # if someone owns the province, deny
        if prov_info['owner_id'] != 0:
            return await ctx.send("You cannot give a province that someone owns.")
        # otherwise, carry on
        try:
            await conn.execute('''UPDATE cnc_provinces SET owner_id = $1, occupier_id = $1 WHERE id = $2;''',
                               user.id, province_id)
            await self.map_color(province_id, user_info['color'])
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
        tech_info = await conn.fetchrow('''SELECT * FROM cnc_tech WHERE lower(name) = $1;''', tech.lower())
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
            await conn.execute('''UPDATE cnc_users SET tech = tech || $1 WHERE user_id = $2;''', [tech], user.id)
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
        tech_info = await conn.fetchrow('''SELECT * FROM cnc_tech WHERE lower(name) = $1;''', tech.lower())
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
        await conn.execute('''UPDATE cnc_users SET tech = array_remove(tech, $1) WHERE user_id = $2;''', tech, user.id)
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
            await conn.execute('''UPDATE cnc_users SET econ_auth = econ_auth + $1 WHERE user_id = $2;''',
                               amount, user.id)
        if authority == "military":
            await conn.execute('''UPDATE cnc_users SET mil_auth = mil_auth + $1 WHERE user_id = $2;''',
                               amount, user.id)
        if authority == "political":
            await conn.execute('''UPDATE cnc_users SET pol_auth = pol_auth + $1 WHERE user_id = $2;''',
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
        await conn.execute('''UPDATE cnc_users SET blacklisted = True WHERE user_id = $1;''',
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
        await conn.execute('''UPDATE cnc_users SET blacklisted = FALSE WHERE user_id = $1;''',
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
            users = await conn.fetch('''SELECT user_id, color FROM cnc_users;''')
            for u in users:
                color = u['color']
                owned_provinces = await conn.fetch('''SELECT * FROM cnc_provinces WHERE owner_id = $1;''', u['user_id'])
                for p in owned_provinces:
                    p_id = p['id']
                    if p['occupier_id'] == u['user_id']:
                        await self.map_color(p_id, color, False)
                        await ctx.send(f"{p['name']} colored.")
                    elif p['occupier_id'] == 0:
                        await self.occupy_color(p_id, '#000000', color)
                    elif p['occupier_id'] != u['user_id']:
                        occupier_color = await conn.fetchrow('''SELECT color FROM cnc_users WHERE user_id = $1;''',
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
        usercheck = await conn.fetchrow('''SELECT * FROM cnc_users WHERE user_id = $1;''', user.id)
        if usercheck is None:
            return await ctx.send("No such user in the CNC system.")
        try:
            await conn.execute('''DELETE FROM cnc_users WHERE user_id = $1;''', user.id)
            await conn.execute('''DELETE FROM cnc_armies WHERE owner_id = $1;''', user.id)
            await conn.execute('''UPDATE cnc_provinces SET owner_id = 0, occupier_id = 0, 
            development = floor((random()*9)+1), citizens = floor((random()*10000)+1000), structures = text[],
            fort_level = 0 WHERE owner_id = $1 AND occupier_id = $1;''', user.id)
            await conn.execute('''DELETE FROM cnc_researching WHERE user_id = $1;''', user.id)
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
        terrain_rolls = await conn.fetch('''SELECT * FROM cnc_terrains WHERE base_development IS NOT NULL;''')
        # create terrain dict
        terrain_info = {}
        for t in terrain_rolls:
            terrain_info.update({t['id']: t['base_development']})
        # pull provinces
        all_provinces = await conn.fetch('''SELECT * FROM cnc_provinces;''')
        # for every province, set the development = (bd + 1d6) + 1d2 (river) + 1d3 (coast)
        total_p = 0
        for p in all_provinces:
            # define the bd as per the terrain
            bd = terrain_info[p['terrain']]
            # add 1d2 if river
            if p['river']:
                bd += randrange(1,2)
            # add 1d3 if coastal
            if p['coast']:
                bd += randrange(1,3)
            # generate number
            rng = randrange(1,6)
            total_dev = bd + rng
            await conn.execute('''UPDATE cnc_provinces SET development = $1 WHERE id = $2;''', total_dev, p['id'])
            total_p += 1
        return await ctx.send(f"{total_p} provinces have been set.")

    @commands.command()
    @commands.is_owner()
    async def cnc_populate_world(self, ctx):
        # establish connection
        conn = self.bot.pool
        # set population = base dev * a random number between 500 and 1500
        async with ctx.typing():
            await conn.execute('''UPDATE cnc_provinces SET citizens = development * (RANDOM()*(1500-500)+500);''')
        return await ctx.send("World populated.")

async def setup(bot: Shard):
    # define the cog and add the cog
    cog = CNC(bot)
    await bot.add_cog(cog)
