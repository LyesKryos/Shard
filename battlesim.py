import traceback
import random
import asyncpg
import math
import asyncio
from PIL import Image, ImageColor, ImageDraw

import discord.ext.commands


class calculations:

    def __init__(self, attacking_army: int, target: int,
                 stationed: int, ctx: discord.ext.commands.Context, debug: bool = None):
        # define winner, attacking and defending forces, their casualties, the target and the stationed province, & ctx
        self.winner = None
        self.attacking_army = attacking_army
        self.defending_army = 0
        self.attacking_casualties = 0
        self.defending_casualties = 0
        self.target = target
        self.stationed = stationed
        self.ctx = ctx
        # if the debug mode is initiated
        self.debug = debug
        self.map_directory = r"/root/Documents/Shard/CNC/Map Files/Maps/"
        self.province_directory = r"/root/Documents/Shard/CNC/Map Files/Province Layers/"
        # creates connection pool
        try:
            self.pool: asyncpg.pool = ctx.bot.pool
        except Exception:
            ctx.bot.logger.warning(traceback.format_exc())

    def map_color(self, province, province_cord, hexcode, release: bool = False):
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
                        prov.putpixel((x, y), color)
        # if this is a release, change every color to neutral grey
        if release is True:
            color = ImageColor.getrgb("#808080")
            for x in range(0, prov.size[0]):
                for y in range(0, prov.size[1]):
                    data = prov.getpixel((x, y))
                    if data != color:
                        if data != (0, 0, 0, 0):
                            prov.putpixel((x, y), color)
        # convert, paste, and save the image
        prov = prov.convert("RGBA")
        map.paste(prov, box=cord, mask=prov)
        map.save(fr"{self.map_directory}wargame_provinces.png")

    def occupy_color(self, province, province_cord, occupy_color, owner_color):
        # get province information
        province_cord = ((int(province_cord[0])), (int(province_cord[1])))
        # get colors
        try:
            occupyer = ImageColor.getrgb(occupy_color)
            owner = ImageColor.getrgb(owner_color)
        except ValueError:
            return ValueError("Hex code issue")
        # open map, create draw object, and obtain province information
        map = Image.open(fr"{self.map_directory}/Maps/wargame_provinces.png").convert("RGBA")
        prov = Image.open(fr"{self.map_directory}/Province Layers/{province}.png").convert("RGBA")
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
                if pixel == (0, 0, 0, 0):
                    not_colored.append((x, y))
                else:
                    prov.putpixel((x, y), owner)
        # draw lines every 20 pixels with the occupier color
        for x in range(0, 1000, space):
            prov_draw.line([x, 0, x - width, height], width=5, fill=occupyer)
        # for every pixel in the non-colored list, remove that pixel
        for pix in not_colored:
            prov.putpixel(pix, (0, 0, 0, 0))
        map.paste(prov, box=cord, mask=prov)
        map.save(fr"{self.map_directory}/Maps/wargame_provinces.png")

    def casualties_roll(self, mod: int, roll: int) -> int:
        max_cas = 0
        if mod == 0:
            max_cas = (roll / 10) - 0.05
        elif mod == 0.05:
            max_cas = 0.1 + ((roll - 1) / 10)
        elif mod == 0.1:
            max_cas = 0.25 + ((roll - 1) / 10)
        elif mod == 0.5:
            max_cas = round(0.6 + ((roll - 1) / 20), 2)
        return max_cas

    async def combat(self):
        """Initiates the combat sequence and sends results."""
        # establishes connection
        conn = self.pool
        # gets running loop
        loop = asyncio.get_running_loop()
        # defines author
        author = self.ctx.author
        # fetches user info
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', author.id)
        # ensures user existance
        if userinfo is None:
            await self.ctx.send("You are not registered.")
            return
        # fetches target and stationed information
        target_info = await conn.fetchrow('''SELECT * FROM provinces  WHERE id = $1;''', self.target)
        # checks existance
        if target_info is None:
            await self.ctx.send(f"Location ID `{self.target}` is not a valid ID.")
            return
        stationed_info = await conn.fetchrow('''SELECT * FROM provinces  WHERE id = $1;''',
                                             self.stationed)
        if stationed_info is None:
            await self.ctx.send(f"Location ID `{self.stationed}` is not a valid ID.")
            return
        # checks to make sure the user has enough moves
        if userinfo['moves'] <= 0:
            await self.ctx.send(f"{userinfo['username']} does not have any movement points left!")
            return
        # if the occupier of the attacking province is not the author
        if stationed_info['occupier_id'] != author.id:
            await self.ctx.send(f"{userinfo['username']} does not occupy Province #{self.stationed}!")
            return
        # if the occupier of the defending province is the author
        if target_info['occupier_id'] == author.id:
            await self.ctx.send(f"You cannot attack a province you already own or occupy!")
            return
        # if the self.attacking_army argument is left blank, attack with all troops
        if self.attacking_army is None:
            self.attacking_army = stationed_info['troops']
        # define defending army
        self.defending_army = target_info['troops']
        # if the self.attacking_army argument is 0 troops
        if self.attacking_army == 0:
            await self.ctx.send("Stop wasting my time, will ya? You can't attack with no army.")
            return
        # fetch the target owner's info
        if target_info['owner_id'] != 0 and target_info['occupier_id'] != 0:
            defender_info = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''',
                                                target_info['occupier_id'])
            if defender_info is None:
                raise Exception("defender_info fetching broken")
            # if the province is occupied and the attacker is the owner, check for a valid conflict
            if target_info['owner_id'] != target_info['occupier_id'] and target_info['owner_id'] == author.id:
                war = await conn.fetchrow('''SELECT * FROM interactions 
                WHERE (sender = $1 AND recipient = $2) OR (sender = $2 AND recipient = $1) 
                AND active = True AND type = 'war';''',
                                          userinfo['username'], defender_info['username'])
                if war is None:
                    await self.ctx.send("You cannot attack a province occupied by a nation you are not at war with or"
                                        "owned by a nation you are not at war with.")
                    return
            else:
                war = await conn.fetchrow('''SELECT * FROM interactions 
                                WHERE (sender = $1 AND recipient = $2) OR (sender = $2 AND recipient = $1) 
                                AND active = True AND type = 'war';''',
                                          userinfo['username'], defender_info['username'])
                if war is None:
                    await self.ctx.send("You cannot attack a province owned by a nation you are not at war with or"
                                        "owned by a nation you are not at war with.")
                    return
        # ensures bordering and coast
        if (not target_info['coast']) or (not stationed_info['coast']):
            if self.stationed not in target_info['bordering']:
                await self.ctx.send(f"Province #{self.stationed} does not border province #{self.target}!")
                return
        # ensures sufficient troops reside in province
        if stationed_info['troops'] < self.attacking_army:
            await self.ctx.send(f"Province #{self.stationed} does not contain {self.attacking_army} troops!")
            return
        # calculates crossing fee if the provinces do not border
        if (target_info['coast'] is True) and (stationed_info['coast'] is True) and (
                self.stationed not in target_info['bordering']):
            # checks for the technology
            if "Sailing" not in userinfo['researched']:
                await self.ctx.send("Water crossing requires the Sailing technology.")
                return
            # checks for sufficient resources
            crossingfee = math.ceil(self.attacking_army * .50)
            if userinfo['focus'] == 'm':
                crossingfee = math.ceil(self.attacking_army * .40)
            if crossingfee > userinfo['resources']:
                await self.ctx.send(
                    f"{userinfo['username']} does not have enough resources to cross with "
                    f"{self.attacking_army} troops!\n"
                    f"**Resources Required:** \u03FE{math.ceil(self.attacking_army * .05)}")
                return
            if stationed_info['port'] is True:
                crossingfee *= .5
                math.ceil(crossingfee)
        else:
            crossingfee = 0
        # if there are no troops in the target province
        if target_info['troops'] == 0:
            # execute all data changes
            await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                               (target_info['troops'] + self.attacking_army), self.target)
            await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                               (stationed_info['troops'] - self.attacking_army), self.stationed)
            if target_info['owner_id'] == 0:
                await conn.execute('''UPDATE provinces  SET owner_id = $1, owner = $2, occupier = $2, occupier_id = $1
                 WHERE id = $3;''', author.id, userinfo['username'], self.target)
                await conn.execute(
                    '''UPDATE cncusers SET moves = $1, resources = $2 WHERE user_id = $3;''',
                    (userinfo['moves'] - 1), (userinfo['resources'] - crossingfee), author.id)
                owner = "the natives"
                await self.ctx.send(
                    f"Province #{self.target} is undefended! It has been overrun by {userinfo['username']} with {self.attacking_army}"
                    f" troops, seizing the province from {owner}!")
                await loop.run_in_executor(None, self.map_color, self.target, target_info['cord'][0:2],
                                           userinfo['usercolor'])
            # if there is an owner, all relevant information updated
            elif target_info['owner_id'] != 0:
                await conn.execute('''UPDATE provinces SET occupier_id = $1, occupier = $2 WHERE id = $3;''', author.id,
                                   userinfo['username'], self.target)
                await conn.execute(
                    '''UPDATE cncusers SET moves = $1, resources = $2 WHERE user_id = $3;''',
                    (userinfo['moves'] - 1), (userinfo['resources'] - crossingfee), author.id)
                owner = target_info['occupier']
                if target_info['owner_id'] == author.id:
                    await loop.run_in_executor(None, self.map_color, self.target, target_info['cord'][0:2],
                                               userinfo['usercolor'])
                else:
                    await loop.run_in_executor(None, self.occupy_color, self.target, target_info['cord'][0:2],
                                               userinfo['usercolor'], defender_info['usercolor'])
                await self.ctx.send(
                    f"Province #{self.target} is undefended! It has been overrun by {userinfo['username']} with {self.attacking_army}"
                    f" troops, seizing the province from {owner}!")
            return
        # if there are any stationed troops
        else:
            # define initial armies
            attacking_troops = self.attacking_army
            defending_troops = self.defending_army
            # defines rolls, weights them, and picks one
            rolls = [1, 2, 3, 4, 5]
            round_roll = random.choices(rolls, weights=[10, 20, 50, 20, 10], k=1)
            round_roll = round_roll[0]
            round_count = 1
            # define terrain round modifiers and casualty modifiers
            terrain_objects_mod = 0
            if target_info['river']:
                round_roll += 1
                terrain_objects_mod += .1
            if target_info['city']:
                round_roll += 2
                terrain_objects_mod += .2
            if target_info['fort']:
                round_roll += 3
                terrain_objects_mod += .3
            # fetch upkeep modifiers
            defender_upkeep_mod = 1
            if target_info['occupier_id'] != 0:
                if defender_info['military_upkeep'] < 10:
                    defender_upkeep_mod -= (10 - defender_info['military_upkeep']) * .1
                elif defender_info['military_upkeep'] > 15:
                    defender_upkeep_mod += (defender_info['military_upkeep']-15) * .1
            attacker_upkeep_mod = 1
            if userinfo['military_upkeep'] < 10:
                attacker_upkeep_mod -= (10 - userinfo['military_upkeep']) * .1
            elif userinfo['military_upkeep'] < 15:
                attacker_upkeep_mod += (userinfo['military_upkeep']-15) * .1
            # define round wins
            attacker_wins = 0
            defender_wins = 0
            # fetches the terrain and the defender's terrain roll modifier
            target_info = await conn.fetchrow('''SELECT * FROM provinces WHERE id = $1;''', self.target)
            terrain_info = await conn.fetchrow('''SELECT * FROM terrains WHERE id = $1;''', target_info['terrain'])
            terrain_mod = terrain_info['roll']
            # fetches the army attack level for the attacker and army defense level for the defender
            attacker_mods = await conn.fetchrow('''SELECT * FROM cnc_modifiers WHERE user_id = $1;''',
                                                self.ctx.author.id)
            defender_mods = await conn.fetchrow('''SELECT * FROM cnc_modifiers WHERE user_id = $1;''',
                                                target_info['occupier_id'])
            if defender_mods is None:
                defence_level = 0
            else:
                defence_level = defender_mods['defence_level']
            # while there are rounds to be fought
            while round_count <= round_roll:
                # calculates army difference if the attacking army is bigger
                if self.attacking_army > self.defending_army:
                    size_modifier = math.floor((self.attacking_army * 0.25) / self.defending_army)
                # calculates army difference if the defending army is bigger
                else:
                    size_modifier = -math.floor((self.defending_army * 0.25) / self.attacking_army)
                # calculates the d6 + level + modifier for both attacker and defender
                attack_roll = random.randint(1, 6)
                modded_attack_roll = (attack_roll + attacker_mods['attack_level'] + size_modifier) * attacker_upkeep_mod
                defense_roll = random.randint(1, 6)
                modded_defense_roll = (defense_roll + defence_level + terrain_mod) * defender_upkeep_mod
                # calculate casualties
                attack_cas = self.casualties_roll(terrain_info['modifier'], defense_roll)
                defense_cas = self.casualties_roll(terrain_info['modifier'], attack_roll)
                # if the attacker's roll is bigger
                if modded_attack_roll > modded_defense_roll:
                    attacker_wins += 1
                # if the defender's roll is bigger
                else:
                    defender_wins += 1
                # calculate casualties
                attacking_cas = random.uniform((self.defending_army * (attack_cas + terrain_objects_mod))
                                               * 0.25,
                                               float(self.defending_army * (attack_cas +
                                                                            terrain_objects_mod)))
                self.attacking_casualties += int(attacking_cas)
                defending_cas = random.uniform((self.attacking_army * defense_cas) * 0.25,
                                               float(self.attacking_army * defense_cas))
                self.defending_casualties += int(defending_cas)
                # if either army takes more than 80% casualties, annihilate
                if self.attacking_army * .8 <= attacking_cas:
                    self.attacking_army = 0
                if self.defending_army * .8 <= defending_cas:
                    self.defending_army = 0
                # subtract casualties
                self.attacking_army -= attacking_cas
                self.defending_army -= defending_cas
                # if either army is reduced to 0, the other army wins
                if self.attacking_army <= 0:
                    defender_wins += 100
                    self.attacking_casualties = attacking_troops
                    self.attacking_army = 0
                    break
                if self.defending_army <= 0:
                    attacker_wins += 100
                    self.defending_casualties = defending_troops
                    self.defending_army = 0
                    break
                # add to round count
                round_count += 1
            # define winner, defender favored, and round army numbers
            self.attacking_army = round(self.attacking_army)
            self.defending_army = round(self.defending_army)
            if attacker_wins > defender_wins:
                self.winner = "attacker"
            else:
                self.winner = "defender"
            # if the defenders are victorious, no move
            if self.winner == "defender":
                victor = "The defenders are victorious!"
            # if the attackers win the battle roll, retreat
            else:
                victor = "The attackers are victorious!"
            # create battleembed object
            battleembed = discord.Embed(title=f"Battle of {target_info['name']} (Province #{self.target})",
                                        description=f"Attack from Province #{self.target} by {userinfo['username']} "
                                                    f"on Province #{self.target} with {attacking_troops} troops.",
                                        color=discord.Color.red())
            battleembed.add_field(name="Attacking Force", value=str(attacking_troops))
            battleembed.add_field(name="Defending Force", value=str(defending_troops))
            battleembed.add_field(name="Terrain", value=terrain_info['name'])
            battleembed.add_field(name="Outcome", value=victor, inline=False)
            if self.debug is True:
                battleembed.add_field(name="Rounds",
                                      value=f"{round_roll} [{attacker_wins}, {defender_wins}]", inline=False)
            battleembed.add_field(name="Attacking Casualties", value=str(self.attacking_casualties))
            battleembed.add_field(name="Defending Casualties", value=str(self.defending_casualties))
            battleembed.add_field(name="Crossing Fee", value=str(crossingfee), inline=False)
            battleembed.add_field(name="Remaining Attacking Force", value=str(self.attacking_army))
            battleembed.add_field(name="Remaining Defending Force", value=str(self.defending_army))
            battleembed.set_thumbnail(url="https://i.ibb.co/gTpHmgq/Command-Conquest-symbol.png")
            await conn.execute('''UPDATE cnc_data SET data_value = data_value + $1 WHERE data_name = 'deaths';''',
                               self.attacking_casualties + self.defending_casualties)
            if self.winner == "attacker":
                # if the natives own the province
                if target_info['occupier_id'] == 0:
                    # updates the target province info
                    await conn.execute(
                        '''UPDATE provinces SET troops = $1, owner_id = $2, owner = $3, occupier_id = $2, occupier = $3
                         WHERE id = $4;''',
                        self.attacking_army, author.id, userinfo['username'], self.target)
                    # updates the userinfo
                    await conn.execute(
                        '''UPDATE cncusers SET moves = $1, resources = $2 WHERE user_id = $3;''',
                        (userinfo['moves'] - 1), (userinfo['resources'] - crossingfee),
                        author.id)
                    # updates the stationed province info
                    await conn.execute('''UPDATE provinces SET troops = $1 WHERE id = $2;''',
                                       (stationed_info['troops'] - self.attacking_army), self.stationed)
                    # sets the footer and sends the embed object
                    battleembed.set_footer(
                        text=f"The natives have lost control of province #{self.target}!"
                             f" All {target_info['troops']} troops have "
                             f"been killed or captured!")
                    await self.ctx.send(embed=battleembed)
                    await loop.run_in_executor(None, self.map_color, self.target, target_info['cord'][0:2],
                                               userinfo['usercolor'])
                    return
                # fetches potential retreat options for the defender
                defender_occupied = await conn.fetch('''SELECT * FROM provinces WHERE occupier_id = $1;''',
                                                     defender_info['user_id'])
                defenderprovs = set(prov['id'] for prov in defender_occupied)
                targetborder = set(p for p in target_info['bordering'])
                retreatoptions = list(defenderprovs.intersection(targetborder))
                if (len(retreatoptions) == 0) and (target_info['coast'] is False):
                    # if the retreat options are none and the defending land is not a coastline
                    # all troops will be destroyed and the attacker takes control of the province
                    # updates all troop and province information and sends the embed
                    await conn.execute(
                        '''UPDATE cncusers SET resources = $1 WHERE user_id = $2;''',
                        (userinfo['resources'] - crossingfee), author.id)
                    await conn.execute(
                        '''UPDATE provinces  SET troops = $1, occupier_id = $2, occupier = $3 WHERE id = $4;''',
                        self.attacking_army, author.id, userinfo['username'], self.target)
                    await conn.execute(
                        '''UPDATE cncusers SET moves = $1, resources = $2 WHERE user_id = $3;''',
                        (userinfo['moves'] - 1), (userinfo['resources'] - crossingfee),
                        author.id)
                    await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                       (stationed_info['troops'] - self.attacking_army), self.stationed)
                    battleembed.set_footer(
                        text=f"{defender_info['username']} has lost control of province #{self.target}!"
                             f" With nowhere to retreat, all {target_info['troops']} troops have "
                             f"been killed!")
                    # if the province is the capital province, add 50 national unrest
                    if userinfo['capital'] == self.target:
                        await conn.execute('''UPDATE cncusers SET national_unrest = $1 WHERE username = $2;''',
                                           userinfo['national_unrest'] + 50, userinfo['username'])
                    await self.ctx.send(embed=battleembed)
                    if target_info['owner_id'] == author.id:
                        await loop.run_in_executor(None, self.map_color, self.target, target_info['cord'][0:2],
                                                   userinfo['usercolor'])
                    else:
                        await loop.run_in_executor(None, self.occupy_color, self.target, target_info['cord'][0:2],
                                                   userinfo['usercolor'], defender_info['usercolor'])
                    return
                if (len(retreatoptions) == 0) and (target_info['coast'] is True):
                    # if the target is a coastline and there are no retreat options by land, the army will be
                    # returned to the defender's stockpile
                    # gets the list of all owned provinces  for both parties
                    # updates all relevant information and sends the embed
                    await conn.execute(
                        '''UPDATE cncusers SET undeployed = $1 WHERE user_id = $2;''',
                        (defender_info['undeployed'] + self.defending_army),
                        defender_info['user_id'])
                    await conn.execute(
                        '''UPDATE provinces  SET troops = $1, occupier_id = $2, occupier = $3 WHERE id = $4;''',
                        self.attacking_army, author.id, userinfo['username'], self.target)
                    await conn.execute(
                        '''UPDATE cncusers SET moves = $1, resources = $2 WHERE user_id = $3;''',
                        (userinfo['moves'] - 1), (userinfo['resources'] - crossingfee),
                        author.id)
                    await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                       (stationed_info['troops'] - self.attacking_army), self.stationed)
                    await conn.execute(
                        '''UPDATE cnc_data SET data_value = data_value + $1 WHERE data_name = 'deaths';''',
                        self.attacking_casualties + self.defending_casualties)
                    battleembed.set_footer(
                        text=f"{defender_info['username']} has lost control of province #{self.target}!"
                             f" With nowhere to retreat, all {self.defending_army} troops have "
                             f"returned to the stockpile!")
                    # if the province is the capital province, add 50 national unrest
                    if userinfo['capital'] == self.target:
                        await conn.execute('''UPDATE cncusers SET national_unrest = $1 WHERE username = $2;''',
                                           userinfo['national_unrest'] + 50, userinfo['username'])
                    await self.ctx.send(embed=battleembed)
                    if target_info['owner_id'] == author.id:
                        await loop.run_in_executor(None, self.map_color, self.target, target_info['cord'][0:2],
                                                   userinfo['usercolor'])
                    else:
                        await loop.run_in_executor(None, self.occupy_color, self.target, target_info['cord'][0:2],
                                                   userinfo['usercolor'], defender_info['usercolor'])
                    return
                else:
                    # if there are retreat options, one will be randomly selected and all remaining troops will
                    # retreat there
                    retreatprovince = random.choice(retreatoptions)
                    # updates all relevant information and sends the embed
                    await conn.execute('''UPDATE provinces  SET troops = troops + $1 WHERE id = $2;''',
                                       self.defending_army, retreatprovince)
                    await conn.execute(
                        '''UPDATE cncusers SET resources = $1 WHERE user_id = $2;''',
                        (userinfo['resources'] - crossingfee), author.id)
                    await conn.execute(
                        '''UPDATE provinces  SET troops = $1, occupier_id = $2, occupier     = $3 WHERE id = $4;''',
                        self.attacking_army, author.id, userinfo['username'], self.target)
                    await conn.execute(
                        '''UPDATE cncusers SET moves = $1, resources = $2 WHERE user_id = $3;''',
                        (userinfo['moves'] - 1), (userinfo['resources'] - crossingfee), author.id)
                    await conn.execute('''UPDATE provinces  SET troops = $1 WHERE id = $2;''',
                                       (stationed_info['troops'] - self.attacking_army), self.stationed)
                    await conn.execute(
                        '''UPDATE cnc_data SET data_value = data_value + $1 WHERE data_name = 'deaths';''',
                        self.attacking_casualties + self.defending_casualties)
                    battleembed.set_footer(
                        text=f"{defender_info['username']} has lost control of province #{self.target}!"
                             f" Their {self.defending_army} troops have retreated to "
                             f"province #{retreatprovince}!")
                    # if the province is the capital province, add 50 national unrest
                    if userinfo['capital'] == self.target:
                        await conn.execute('''UPDATE cncusers SET national_unrest = $1 WHERE username = $2;''',
                                           userinfo['national_unrest'] + 50, userinfo['username'])
                    await self.ctx.send(embed=battleembed)
                    if target_info['owner_id'] == author.id:
                        await loop.run_in_executor(None, self.map_color, self.target, target_info['cord'][0:2],
                                                   userinfo['usercolor'])
                    else:
                        await loop.run_in_executor(None, self.occupy_color, self.target, target_info['cord'][0:2],
                                                   userinfo['usercolor'], defender_info['usercolor'])
                    return
            # if the attacker is not victorious, no provinces change hands
            else:
                if target_info['owner_id'] == 0 or target_info['occupier_id'] == 0:
                    # updates the relevant information and sends the embed
                    await conn.execute(
                        '''UPDATE cncusers SET resources = $1 WHERE user_id = $2;''',
                        (userinfo['resources'] - crossingfee), author.id)
                    await conn.execute('''UPDATE provinces  SET troops = troops - $1 WHERE id = $2;''',
                                       self.attacking_casualties, self.stationed)
                    await conn.execute('''UPDATE provinces  SET troops = troops - $1 WHERE id = $2;''',
                                       self.defending_casualties, self.target)
                    await conn.execute(
                        '''UPDATE cnc_data SET data_value = data_value + $1 WHERE data_name = 'deaths';''',
                        self.attacking_casualties + self.defending_casualties)
                    battleembed.set_footer(
                        text=f"The natives have successfully defended province #{self.target}!")
                    await self.ctx.send(embed=battleembed)
                    return
                # updates the relevant information and sends the embed
                await conn.execute(
                    '''UPDATE cncusers SET resources = $1 WHERE user_id = $2;''',
                    (userinfo['resources'] - crossingfee), author.id)
                await conn.execute('''UPDATE provinces  SET troops = troops - $1 WHERE id = $2;''',
                                   self.attacking_casualties, self.stationed)
                await conn.execute('''UPDATE provinces  SET troops = troops - $1 WHERE id = $2;''',
                                   self.defending_casualties, self.target)
                await conn.execute(
                    '''UPDATE cnc_data SET data_value = data_value + $1 WHERE data_name = 'deaths';''',
                    self.attacking_casualties + self.defending_casualties)
                battleembed.set_footer(
                    text=f"{defender_info['username']} has successfully defended province #{self.target}!")
                await self.ctx.send(embed=battleembed)
                return
