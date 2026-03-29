import asyncpg
import discord
from PIL import ImageColor, Image, ImageDraw
from random import randint, choice
from math import floor
import logging

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
    return map.save(fr"{map_directory}wargame_provinces.png")

async def occupy_color(province: int, occupy_color: str, owner_color: str, conn: asyncpg.Pool):
    map_directory = r"/root/Shard/CNC/Map Files/Maps/"
    province_directory = r"/root/Shard/CNC/Map Files/Province Layers/"
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
    map = Image.open(fr"{map_directory}wargame_provinces.png").convert("RGBA")
    prov = Image.open(fr"{province_directory}{province}.png").convert("RGBA")
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
    return map.save(fr"{map_directory}wargame_provinces.png")


class Turn:

    def __init__(self, conn: asyncpg.Pool, bot: discord.Client):
        self.conn = conn
        self.user_dm_notifications = {}
        self.turn = 0
        self.bot = bot

    async def run_turn(self) -> dict:
        # run the user updates
        await self._user_updates()
        # run the market update
        await self._trade_market_updates()
        # run the timer updates
        await self._timer_updates()
        # update turn
        self.turn = await self.conn.fetchval('''SELECT number FROM cnc_data WHERE name = 'Turn';''')
        # return the dm notifications
        return self.user_dm_notifications


    async def _user_updates(self):
        # define the connection
        conn = self.conn
        # get a list of all users
        user_list = await conn.fetch('''SELECT * FROM cnc_users;''')

        # pull all terrains and store
        terrains_raw = await conn.fetch('''SELECT * FROM cnc_terrains;''')
        terrain_mods = {}
        for terrain in terrains_raw:
            terrain_mods[terrain['id']] = terrain['modifier']

        # pull all trade goods and store
        trade_good_values_raw = await conn.fetch('''SELECT *
                                                  FROM cnc_trade_goods;''')
        trade_good_values = {}
        for tg in trade_good_values_raw:
            trade_good_values[tg['name']] = tg['market_value']

        # for each user, get a list of the provinces and update them as a batch
        for user in user_list:
            # define DM notification
            dm_notification = ""
            # define the users full production
            trade_good_production = 0
            # define base production access
            trade_good_production_access = 0.05
            # define total structure number
            structure_count = 0
            # total manpower count
            manpower_count = 0
            # total national unrest
            total_national_unrest = 0
            # taxation effectiveness boost
            tax_effect_boost = 0
            # get military alliances
            military_alliances = await conn.fetchval('''SELECT cardinality(members) FROM cnc_alliances 
                                                        WHERE $1 = ANY(members);''', user['name'])
            # protect against none
            if military_alliances is None:
                military_alliances = 0
            # get peace treaties
            peace_treaties = await conn.fetch('''SELECT * FROM cnc_peace_treaties WHERE primary_target = $1;''',
                                              user['name'])
            # get active wars
            wars = await conn.fetch('''SELECT * FROM cnc_wars WHERE ($1 = ANY(attackers) OR $1 = ANY(defenders)) 
                                                                AND active = True;''', user['name'])
            # get active diplomatic relations
            diplomatic_relations = await conn.fetchval('''SELECT count(id) FROM cnc_drs WHERE $1 = ANY(members);''',
                                                       user['name'])
            # get government subtype
            govt_subtype = await conn.fetchrow('''SELECT * FROM cnc_govts WHERE govt_subtype = $1;''',
                                               user['govt_subtype'])

            # === PROVINCE UPDATING ===
            # pull all their owned & occupied provinces
            controlled_provs = await conn.fetch('''SELECT * FROM cnc_provinces 
                                                   WHERE owner_id = $1 AND occupier_id = $1;''', user['user_id'])
            # for each of those provinces
            for prov in controlled_provs:
                # add all structures
                structure_count += len(prov['structures'])
                # add all manpower
                manpower_count += prov['citizens']
                # if there is a Fishery, increase taxation effectiveness
                if 'Fishery' in prov['structures']:
                    tax_effect_boost += 1

                # === CITIZEN GROWTH ===
                citizen_growth = ((prov['development']/100) * prov['citizens']) * (1 - terrain_mods[prov['terrain']])
                # boost for city
                if "City" in prov['structures']:
                    citizen_growth *= 1.05
                    tax_effect_boost += 2
                # boost for farm
                if "Farm" in prov['structures']:
                    # base defined as 5%, which is farm effect (default 1) + 0.05 here
                    citizen_growth *= user['farm_effect'] + 0.05
                # boost for capital
                if user['capital'] == prov['id']:
                    citizen_growth *= 1.10
                # boost for free city
                if user['govt_subtype'] == "Free City":
                    citizen_growth *= 1.25
                # debuff for unrest
                if user['unrest'] > 0:
                    # exponentially increasing as unrest rises to a max of about 30% growth reduction
                    citizen_growth *= 1-((user['unrest']*0.1)**1.45)/100
                # debuff for stability
                if user['stability'] < 100:
                    # exponentially decreasing as stability falls
                    citizen_growth *= 0.3+((user['stability']*1.5)/100)
                # update citizenry
                await conn.execute('''UPDATE cnc_provinces SET citizens = citizens + $1 WHERE id = $2;''',
                                   round(citizen_growth*.3), prov['id'])
                # cap if necessary
                await conn.execute('''UPDATE cnc_provinces SET citizens = $1 WHERE citizens > $1 AND id = $2;''',
                                   prov['development'] * 1592 * (1.25 if "City" in prov['structures'] else 1),
                                   prov['id'])

                # === PRODUCTION ===
                # define citizen production
                citizen_production = prov['citizens'] / 3872
                # define trade good value
                trade_good_value = trade_good_values[prov['trade_good']]
                # add the total trade good value booster provided by some techs
                if prov['trade_good'] not in ['Gold', 'Silver', 'Precious Stones', 'Spices', 'Chocolate']:
                    trade_good_value += user['trade_good_value']
                # get the user's trade good value, catching for if that doesn't exist
                try:
                    user_trade_good_value_boost = user[f'{prov["trade_good"].lower().replace(" ", "_")}_value']
                    trade_good_value += user_trade_good_value_boost
                except KeyError:
                    pass
                # if there is a manufactory (but not a quarry, as they exclude each other)
                if "Manufactory" in prov['structures'] and not "Quarry" in prov['structures']:
                    # increase production by 7%
                    citizen_production *= 1.07
                # if there is a quarry
                if "Quarry" in prov['structures']:
                    # increase production by 10%
                    citizen_production *= 1.10
                # if there is a trade post
                if "Trading Post" in prov['structures']:
                    # increase the value of the trade good by 1
                    trade_good_value += 1
                # if there is a port (but not a trading post, as they exclude each other)
                if "Port" in prov['structures'] and "Trading Post" not in prov['structures']:
                    # increase the value of the trade good by .5
                    trade_good_value += 0.5
                # if the user's government type is Wuxing
                if user['govt_subtype'] == "Wuxing":
                    # increase production by 75%
                    citizen_production *= 1.75
                # if the user's government type is Parish
                if user['govt_subtype'] == "Parish":
                    # increase production by 50%
                    citizen_production *= 1.50
                # debuff citizen production based on unrest
                if user['unrest'] > 0:
                    # exponentially decreasing as unrest rises to a max of about 35% production reduction
                    citizen_production *= 1-((user['unrest']*0.1)**1.55)/100
                # add to the overall production
                trade_good_production += citizen_production * trade_good_value
                # update the production from this province
                await conn.execute('''UPDATE cnc_provinces SET production = $1 WHERE id = $2;''',
                                   round(citizen_production), prov['id'])

                # === NATIONAL UNREST ===
                # define province's national unrest contribution
                prov_nat_unrest = 0
                # for every level of taxation above 8%, exponentially increase
                if user['tax_level']/100 > .08:
                    # if the user is Unitary
                    if user['govt_subtype'] == "Unitary":
                        # exponentially increase as taxation rises to a max of 40 national unrest reduced by 10%
                        prov_nat_unrest += ((user['tax_level'] * 1.05) ** 1.2) * 0.9
                    # otherwise, normal
                    else:
                        # exponentially increase as taxation rises to a max of 40 national unrest
                        prov_nat_unrest += (user['tax_level'] * 1.05) ** 1.2
                # for every province owned beyond the overextension limit, add exponentially increasing unrest
                if len(controlled_provs) > user['overextend_limit']:
                    # exponentially increase as the number of provinces owned rises
                    overextended = len(controlled_provs) - user['overextend_limit']
                    prov_nat_unrest += (overextended**1.55)-overextended
                # if this province has a temple
                if "Temple" in prov['structures']:
                    # reduce by 25%
                    prov_nat_unrest *= 0.75
                # add national unrest
                total_national_unrest += prov_nat_unrest

            # === TRADE VALUE ===
            # get a count of all user's trade pacts
            trade_pact_count = await conn.fetchval('''SELECT count(id) FROM cnc_trade_pacts 
                                                      WHERE $1 = ANY(members)''', user['name'])
            # for each trade pact, increase the trade access amount by 5%
            trade_good_production_access += 0.05 * trade_pact_count
            # get a count of all the embargoes issued against this user
            embargo_count = await conn.fetchval('''SELECT count(id) FROM cnc_embargoes 
                                                   WHERE target = $1;''', user['name'])
            # for each embargo, decrease the trade good production access exponentially up to a max of 35% reduction
            trade_good_production_access -= min((embargo_count * 0.05) ** 1.6, 0.35)
            # calculate total trade value for this nation, protecting against negative values
            trade_value = max(trade_good_production * trade_good_production_access, 0)

            # === MANPOWER ===
            # peace treaty enforced manpower reduction
            treaty_enforced_manpower_reduction = 1 - sum([pt['manpower_reduction'] for pt in peace_treaties])
            # enforce manpower cap
            manpower_cap = (round((user['manpower_access']/100) * manpower_count) *
                            treaty_enforced_manpower_reduction if treaty_enforced_manpower_reduction != 0 else 1)
            # update manpower set on manpower regen rate
            await conn.execute('''UPDATE cnc_users SET manpower = manpower + $2 WHERE user_id = $1;''',
                               user['user_id'], round(manpower_cap * (user['manpower_regen'] / 100)))
            # enforce manpower cap
            await conn.execute('''UPDATE cnc_users SET manpower = $2 WHERE user_id = $1 AND manpower > $2;''',
                               user['user_id'], manpower_cap)

            # === UNREST/STABILITY FACTORING ===
            average_national_unrest = total_national_unrest / len(controlled_provs)
            # reduce by 5 if the user has a capital
            if user['capital']:
                average_national_unrest -= 5
            # modify by the tech national unrest gain
            average_national_unrest *= user['nat_unrest_gain']
            # by the government type unrest gain
            average_national_unrest *= govt_subtype['unrest_mod']
            # if the user is a great power, reduce their national unrest by 5%
            if user['gp']:
                average_national_unrest *= .95
            # update user unrest
            await conn.execute('''UPDATE cnc_users SET unrest = $2 WHERE user_id = $1;''',
                               user['user_id'], average_national_unrest)

            # stability losses
            econ_stab_loss = ((user['last_econ_auth_gain']*3)-9) if user['last_econ_auth_gain'] < 3 else 0
            pol_stab_loss = ((user['last_pol_auth_gain']*2)-10) if user['last_pol_auth_gain'] < 5 else 0
            mil_stab_loss = ((user['last_mil_auth_gain']*2)-8) if user['last_mil_auth_gain'] > 4 else 0
            # stability gain from "strong army"
            manpower_usage_count = await conn.fetchval('''SELECT SUM(troops)::INT FROM cnc_armies 
                                                          WHERE owner_id = $1;''', user['user_id'])
            # protect against null
            manpower_usage_count = 0 if manpower_usage_count is None else manpower_usage_count
            # calculate stability gain from "strong army"
            strong_army_stab = round((manpower_usage_count/manpower_cap) * 10)
            # stability gain from "military alliances"
            military_alliance_stab = (1+(1*military_alliances)) if military_alliances > 0 else 0
            # total stability
            total_stability = sum([econ_stab_loss, pol_stab_loss, mil_stab_loss, strong_army_stab, military_alliance_stab])
            # if the user is a gp, increase stability by 5
            if user['gp']:
                total_stability += 5
            # update stability
            await conn.execute('''UPDATE cnc_users SET stability = stability + $2 WHERE user_id = $1;''',
                               user['user_id'], total_stability)

            # === REBELLION ===
            # if there is not currently a rebellion
            if not user['active_rebellion'] and not user['active_civil_war'] and not user['active_revolution']:
                # calculate the chance for a revolution based on the unrest
                if total_national_unrest > 70:
                    # roll the dice
                    revolution_chance = randint(1, total_national_unrest)
                    # if the roll is greater than 60
                    if revolution_chance > 60:
                        # define list of possible revolutions
                        revolution_choices = ["Anarchy"]
                        if "Divine Right" in user['tech']:
                            revolution_choices.append("Monarchy")
                        if "Patrician Values" in user['tech']:
                            revolution_choices.append("Republic")
                        if "Democratic Ideals" in user['tech']:
                            revolution_choices.append("Democracy")
                        if "Revolutionary Ideals" in user['tech']:
                            revolution_choices.append("Equalism")
                        # choose a random revolution
                        revolution_type = choice(revolution_choices)
                        # trigger a revolution
                        await conn.execute('''UPDATE cnc_users SET active_revolution = $2 WHERE user_id = $1;''',
                                           user['user_id'], revolution_type)
                        # set a number of provinces as rebellious on national unrest
                        rebellious_provinces = await conn.fetch('''SELECT *
                                                                   FROM cnc_provinces
                                                                   WHERE owner_id = $1
                                                                     AND id != $2
                                                                   ORDER BY RANDOM() limit $3;''',
                                                                user['user_id'], user['capital'],
                                                                max(total_national_unrest / 100, .75))
                        # define rebel provinces as a list
                        rebel_provinces = []
                        # update the rebellious provinces
                        for prov in rebellious_provinces:
                            # add to the list
                            rebel_provinces.append(prov['id'])
                            # update the db to set occupier = 1 (aka rebels)
                            await conn.execute('''UPDATE cnc_provinces
                                                  SET occupier_id = 1
                                                  WHERE id = $1;''', prov['id'])
                            # set the occupy color to black
                            await occupy_color(province=prov['id'],
                                               occupy_color="#000000",
                                               owner_color=user['color'],
                                               conn=conn)
                        # add to DM notification
                        dm_notification += (f"**A revolution has begun in our nation!** Rebels supporting a new "
                                            f"Government Type, {revolution_type}, have risen up in "
                                            f"arms against the {user['pretitle']} of {user['name']}! "
                                            f"They have occupied these provinces: {', '.join(rebel_provinces)}."
                                            f"We must react quickly, or they may overwhelm our nation!\n")

                # calculate the chance for a civil war based on the unrest
                elif total_national_unrest > 65:
                    # roll the dice
                    civil_war_chance = randint(1, total_national_unrest)
                    # if the roll is greater than 55
                    if civil_war_chance > 55:
                        # define list of possible civil war types
                        civil_war_type = await conn.fetchval('''SELECT govt_subtype FROM cnc_govts 
                                                                WHERE govt_type = $1 AND govt_subtype != $2 
                                                                ORDER BY RANDOM() LIMIT 1;''',
                                                             user['govt_type'], user['govt_subtype'])
                        # trigger a civil war
                        await conn.execute('''UPDATE cnc_users SET active_civil_war = $2 WHERE user_id = $1;''',
                                           user['user_id'], civil_war_type)
                        #  set a number of provinces as rebellious on national unrest
                        rebellious_provinces = await conn.fetch('''SELECT * FROM cnc_provinces 
                                                                   WHERE owner_id = $1 AND id != $2 
                                                                   ORDER BY RANDOM() limit $3;''',
                                                                user['user_id'], user['capital'],
                                                                max(total_national_unrest/100,.75))
                        # define rebel provinces as a list
                        rebel_provinces = []
                        # update the rebellious provinces
                        for prov in rebellious_provinces:
                            # add to the list
                            rebel_provinces.append(prov['id'])
                            # update the db to set occupier = 1 (aka rebels)
                            await conn.execute('''UPDATE cnc_provinces SET occupier_id = 1 
                                                  WHERE id = $1;''', prov['id'])
                            # set the occupy color to black
                            await occupy_color(province=prov['id'],
                                               occupy_color="#000000",
                                               owner_color=user['color'],
                                               conn=conn)
                        # add to DM notification
                        dm_notification += (f"**A Civil War has begun in our nation!** An armed faction of citizens "
                                            f"that supports a *{civil_war_type}* {user['govt_type']} have risen up and "
                                            f"threaten to overthrow the legitimate government of the "
                                            f"{user['pretitle']} of {user['name']}! They have occupied these provinces:"
                                            f" {', '.join(rebel_provinces)}.\n")

                # calculate the chance for a rebellion based on the unrest
                elif total_national_unrest > 50:
                    # roll the dice
                    rebellion_chance = randint(1, total_national_unrest)
                    # if the roll is greater than 45
                    if rebellion_chance > 45:
                        # trigger a rebellion
                        await conn.execute('''UPDATE cnc_users SET active_rebellion = TRUE WHERE user_id = $1;''',
                                           user['user_id'])
                        # set a number of provinces as rebellious on national unrest
                        rebellious_provinces = await conn.fetch('''SELECT * FROM cnc_provinces 
                                                                   WHERE owner_id = $1 AND id != $2 
                                                                   ORDER BY RANDOM() limit $3;''',
                                                                user['user_id'], user['capital'],
                                                                max(total_national_unrest/100,.75))
                        # define rebel provinces as a list
                        rebel_provinces = []
                        # update the rebellious provinces
                        for prov in rebellious_provinces:
                            # add to the list
                            rebel_provinces.append(prov['id'])
                            # update the db to set occupier = 1 (aka rebels)
                            await conn.execute('''UPDATE cnc_provinces SET occupier_id = 1 
                                                  WHERE id = $1;''', prov['id'])
                            # set the occupy color to black
                            await occupy_color(province=prov['id'],
                                               occupy_color="#000000",
                                               owner_color=user['color'],
                                               conn=conn)
                        # add to DM notification
                        dm_notification += (f"**Rebellious factions** have risen up in "
                                            f"arms against the {user['pretitle']} of {user['name']}! "
                                            f"They have occupied these provinces: {', '.join(rebel_provinces)}."
                                            f"If we are not careful, they may overwhelm our nation!\n")

            # if there is currently a rebellion
            else:
                # calculate if the rebels get to win or not
                if user['internal_conflict'] >= 6:
                    # === REBELS WIN ===
                    # if this is a revolution
                    if user['active_revolution']:
                        # select a random subtype
                        subtype = await conn.fetchval('''SELECT govt_subtype FROM cnc_govts 
                                                         WHERE govt_type = $1 ORDER BY RANDOM() LIMIT 1;''',
                                                      user['active_revolution'])
                        # update the user's government type
                        await conn.execute('''UPDATE cnc_users SET govt_type = $2, govt_subtype = $3 
                                              WHERE user_id = $1;''',
                                           user['user_id'], user['active_revolution'], subtype)
                        # set the auth reduction
                        await conn.execute('''INSERT INTO cnc_peace_treaties(primary_target, truce_length, reparations) 
                                              VALUES($1, $2, $3);''', user['name'], 5, [2,2,2])
                    # if this is a civil war
                    elif user['active_civil_war']:
                        # update the user's government subtype based on the civil war type
                        await conn.execute('''UPDATE cnc_users SET govt_subtype = $2 WHERE user_id = $1;''',
                                           user['user_id'], user['active_civil_war'])
                        # set the auth reduction
                        await conn.execute('''INSERT INTO cnc_peace_treaties(primary_target, truce_length, reparations)
                                              VALUES ($1, $2, $3);''', user['name'], 4, [2, 2, 2])
                    # if this is a rebellion
                    elif user['active_rebellion']:
                        # set tax
                        await conn.execute('''UPDATE cnc_users SET tax_level = 5 WHERE user_id = $1;''',
                                           user['user_id'])
                        # set the peace treaty
                        await conn.execute('''INSERT INTO cnc_peace_treaties(primary_target, truce_length, reparations, 
                                                                             manpower_reduction, government_mod_ban)
                                           VAUES($1, $2, $3, $4, TRUE);''',
                                           user['name'], 10, [1,1,1], .1)
                    # update the message
                    dm_notification += ("Our armies have been overwhelmed by rebel forces, "
                                        "who have executed their demands on our government!\n")

                # if they are not yet going to win, see if their ticker counts up
                else:
                    # check if 20% of the user's provinces are occupied
                    rebel_occupants_count = await conn.fetchval('''SELECT COUNT(id) FROM cnc_provinces 
                                                                   WHERE occupier_id = 1 AND owner_id = $1;''',
                                                                user['user_id'])
                    # if this counts for 20%
                    if (rebel_occupants_count/len(controlled_provs) > .2) and (len(controlled_provs) > 5):
                        # increase the ticker
                        await conn.execute('''UPDATE cnc_users SET internal_conflict = internal_conflict + 1 
                                              WHERE user_id = $1;''', user['user_id'])
                    # otherwise, do nothing
                    else:
                        pass
                    # check if new rebel provinces must be added
                    if user['unrest'] >= 55:
                        # roll the dice
                        further_rebellion = randint(1, total_national_unrest)
                        # if the roll is greater than 50
                        if further_rebellion > 50:
                            # select a random number of unrebelled provinces
                            new_rebel_provinces = await conn.fetch('''SELECT * FROM cnc_provinces 
                                                                   WHERE owner_id = $1 AND occupier_id != 1 AND id != $2 
                                                                   ORDER BY RANDOM() limit $3;''',
                                                                user['user_id'], user['capital'],
                                                                max(total_national_unrest/100,.55))
                            # define rebel provinces as a list
                            rebel_provinces = []
                            # update the rebellious provinces
                            for prov in new_rebel_provinces:
                                # add to the list
                                rebel_provinces.append(prov['id'])
                                # update the db to set occupier = 1 (aka rebels)
                                await conn.execute('''UPDATE cnc_provinces
                                                      SET occupier_id = 1
                                                      WHERE id = $1;''', prov['id'])
                                # set the occupy color to black
                                await occupy_color(province=prov['id'],
                                                   occupy_color="#000000",
                                                   owner_color=user['color'],
                                                   conn=conn)
                            # add to DM notification
                            dm_notification += (f"The ongoing rebellion against the {user['pretitle']} of "
                                                f"{user['name']} has further developed. Additional rebels have arisen in "
                                                f"these provinces: {', '.join(rebel_provinces)}.\n")

            # === AUTHORITY UPDATES ===
            # pull average dev
            average_dev = await conn.fetchval('''SELECT AVG(development)::float FROM cnc_provinces 
                                                 WHERE owner_id = $1 AND occupier_id = $1;''', user['user_id'])

            # === ECONOMIC AUTHORITY ===
            if user['govt_subtype'] != "Tusail":
                # calculate economic authority
                econ_auth_gain = 0
                # pull base economic amount from govt type
                econ_auth_gain += await conn.fetchval('''SELECT econ_auth FROM cnc_govts 
                                                                WHERE govt_subtype = $1;''',
                                                             user['govt_subtype'])
                # add the trade value
                econ_auth_gain += trade_value
                logging.getLogger(__name__).info(f"{user['name']} trade value: {trade_value} = "
                                                 f"{trade_good_production} * {trade_good_production_access}")
                # calculate tax income
                econ_auth_gain += average_dev * ((user['tax_level'] + tax_effect_boost)/100)
                # pull all mines
                mines = await conn.fetchval('''SELECT COUNT(id) FROM cnc_provinces 
                                               WHERE 'Mine' = ANY(structures) 
                                                 AND (owner_id = $1 AND occupier_id = $1);''',
                                            user['user_id'])
                # for every mine, add 0.5
                econ_auth_gain += 0.5 * mines
                # check for techs
                if "Currency" in user['tech']:
                    econ_auth_gain += 1
                if "Economics" in user['tech']:
                    econ_auth_gain += 1
                if "Banking and Investment" in user['tech']:
                    econ_auth_gain += 1
                if "Guilds" in user['tech']:
                    econ_auth_gain += 1

                # calculate reductions
                # reduce from public spending
                econ_auth_gain -= user['public_spend']
                # reduce from reparations
                for peace in peace_treaties:
                    # if there is one with econ reparations, reduce
                    if peace['reparations']:
                        econ_auth_gain -= peace['reparations'][0] if peace['reparations'][0] > 0 else 0
                    # there there is one with dismantle, reduce
                    if peace['dismantle']:
                        econ_auth_gain -= 3

                # update econ auth
                await conn.execute('''UPDATE cnc_users SET econ_auth = $2, last_econ_auth_gain = $2
                                      WHERE user_id = $1;''', user['user_id'], floor(econ_auth_gain))
            # otherwise, set at 0
            else:
                await conn.execute('''UPDATE cnc_users SET econ_auth = 0, last_econ_auth_gain = 0
                                      WHERE user_id = $1;''', user['user_id'])

            # === MILITARY AUTHORITY ===
            if user['govt_subtype'] != "Pacifistic":
                # calculate military authority gain
                mil_auth_gain = 0
                # add mil auth based on govt subtype
                mil_auth_gain += await conn.fetchval('''SELECT mil_auth FROM cnc_govts 
                                                        WHERE govt_subtype = $1;''', user['govt_subtype'])
                # for each military alliance, add 1 + x^1.25
                mil_auth_gain += (military_alliances**1.25) + military_alliances
                # based on the average development, add dev/5
                mil_auth_gain += average_dev/5

                # calculate reductions
                # reduce from military upkeep
                mil_auth_gain -= user['mil_upkeep']
                # reduce from wars if primary attacker
                for war in wars:
                    if war['primary_attacker'] == user['name']:
                        mil_auth_gain -= 2
                # reduce from reparations
                for peace in peace_treaties:
                    # if there is one with mil reparations, reduce
                    if peace['reparations']:
                        mil_auth_gain -= peace['reparations'][1] if peace['reparations'][1] > 0 else 0
                    # there there is one with dismantle, reduce
                    if peace['dismantle']:
                        mil_auth_gain -= 3

                # update mil auth
                await conn.execute('''UPDATE cnc_users SET mil_auth = $2, last_mil_auth_gain = $2
                                      WHERE user_id = $1;''', user['user_id'], floor(mil_auth_gain))
            # otherwise, set at 0
            else:
                await conn.execute('''UPDATE cnc_users SET mil_auth = 0, last_mil_auth_gain = 0
                                      WHERE user_id = $1;''', user['user_id'])

            # === POLITICAL AUTHORITY ====
            pol_auth_gain = 0
            # add pol auth based on govt subtype
            pol_auth_gain += await conn.fetchval('''SELECT pol_auth FROM cnc_govts WHERE govt_subtype = $1;''',
                                                user['govt_subtype'])
            # for each diplomatic relation, add x^1.35 + x/2
            pol_auth_gain += (diplomatic_relations**1.15) + (diplomatic_relations/2)
            # based on the average development, add dev/5
            pol_auth_gain += average_dev/5
            # add pol auth based on techs
            if "Basic Government" in user['tech']:
                pol_auth_gain += 1

            # calculate reductions
            # reduce pol auth based on national unrest
            pol_auth_gain -= total_national_unrest/15
            # reduce pol auth based on the number of OTHER members in the military alliance
            pol_auth_gain -= military_alliances - 1
            # reduce pol auth based on issued relations
            pol_auth_gain -= trade_pact_count
            pol_auth_gain -= await conn.fetchval('''SELECT count(id) FROM cnc_embargoes WHERE sender = $1;''',
                                                 user['name'])
            # if there is a capital, reduce by 1
            if user['capital']:
                pol_auth_gain -= 1
            # reduce pol auth based on reparations
            for peace in peace_treaties:
                # if there is one with pol reparations, reduce
                if peace['reparations']:
                    pol_auth_gain -= peace['reparations'][2] if peace['reparations'][2] > 0 else 0
                # if there is one with dismantle, reduce
                if peace['dismantle']:
                    pol_auth_gain -= 3

            # add pol auth gain
            await conn.execute('''UPDATE cnc_users SET pol_auth = $2, last_pol_auth_gain = $2 
                                  WHERE user_id = $1;''', user['user_id'], floor(pol_auth_gain))

            # === ARMY MOVEMENT RESET ===
            await conn.execute('''UPDATE cnc_armies SET movement = $2 WHERE owner_id = $1;''',
                               user['user_id'], user['movement_cap'])

            # add user dm notifications to the list
            self.user_dm_notifications[user['user_id']] = dm_notification if dm_notification != "" else None

        # for each user, update their auth depending on overlordship/subjection
        for user in user_list:
            # calculate puppets/overlords loss/gain
            if user['overlord']:
                # reduce by a quarter of the gain, min 1
                await conn.execute('''UPDATE cnc_users 
                                      SET econ_auth             = econ_auth - $1, 
                                          last_econ_auth_gain = last_econ_auth_gain - $1, 
                                          mil_auth              = mil_auth - $2, 
                                          last_mil_auth_gain  = last_mil_auth_gain - $2, 
                                          pol_auth              = pol_auth - $3, 
                                          last_pol_auth_gain  = last_pol_auth_gain - $3 
                                      WHERE user_id = $4;''',
                                   min(floor(user['last_econ_auth_gain']/4), 1),
                                   min(floor(user['last_mil_auth_gain']/4), 1),
                                   min(floor(user['last_pol_auth_gain']/4), 1),
                                   user['user_id'])
                # update the overlord's gains
                await conn.execute('''UPDATE cnc_users
                                      SET econ_auth             = econ_auth + $1,
                                          last_econ_auth_gain = last_econ_auth_gain + $1,
                                          mil_auth              = mil_auth + $2,
                                          last_mil_auth_gain  = last_mil_auth_gain + $2,
                                          pol_auth              = pol_auth + $3,
                                          last_pol_auth_gain  = last_pol_auth_gain + $3
                                      WHERE user_id = $4;''',
                                   min(floor(user['last_econ_auth_gain'] / 4), 1),
                                   min(floor(user['last_mil_auth_gain'] / 4), 1),
                                   min(floor(user['last_pol_auth_gain'] / 4), 1),
                                   user['overlord'])

        # set stability, authority, and unrest max/mins
        await conn.execute('''UPDATE cnc_users
                              SET stability = LEAST(GREATEST(stability, 0), 100),
                                  econ_auth = GREATEST(econ_auth, 0),
                                  mil_auth  = GREATEST(mil_auth, 0),
                                  pol_auth  = GREATEST(pol_auth, 0),
                                  unrest    = LEAST(GREATEST(unrest, 0), 100);''')


    async def _trade_market_updates(self):
        # establish connection
        conn = self.conn
        # production for unowned provinces
        unowned_provinces = await conn.fetch('''SELECT * FROM cnc_provinces WHERE owner_id = 0;''')
        # calculate flat production
        for prov in unowned_provinces:
            citizen_production = prov['citizens'] / 3872
            await conn.execute('''UPDATE cnc_provinces SET production = $2 WHERE id = $1;''',
                               prov['id'], floor(citizen_production))
        # pull all the trade goods
        trade_goods = {}
        trade_goods_raw = await conn.fetch('''SELECT * FROM cnc_trade_goods;''')
        # for each trade good
        for good in trade_goods_raw:
            # get the total production of all provinces that produce that trade good
            total_production = await conn.fetchval('''SELECT SUM(production) FROM cnc_provinces 
                                                      WHERE trade_good = $1;''', good['name'])
            # log the total production in the dict
            trade_goods[good['name']] = int(total_production)
            # calculate the proper market value of the good
            new_market_value = max((-(trade_goods[good['name']]/10)+10)**.88, 0.5)
            # execute the update
            await conn.execute('''UPDATE cnc_trade_goods SET market_value = $2 WHERE name = $1;''',
                               good['name'], new_market_value)

    async def _timer_updates(self):
        # define the connection
        conn = self.conn

        # === GLOBAL TURN UPDATE
        await conn.execute('''UPDATE cnc_data SET number = number + 1 WHERE name = 'Turn';''')

        # === TRUCE TIMER REDUCTION ===
        await conn.execute('''UPDATE cnc_peace_treaties 
                              SET truce_length = truce_length - 1, 
                                  end_embargo = CASE WHEN end_embargo > 0 THEN end_embargo - 1 END, 
                                  end_ma = CASE WHEN end_ma > 0 THEN end_ma - 1 END, 
                                  end_tp = CASE WHEN end_tp > 0 THEN end_tp - 1 END, 
                                  reparations_length = CASE WHEN reparations_length > 0 THEN reparations_length - 1 END, 
                                  humiliate = CASE WHEN humiliate > 0 THEN humiliate - 1 END, 
                                  dismantle = CASE WHEN dismantle > 0 THEN dismantle - 1 END, 
                                  manpower_reduction = CASE WHEN manpower_reduction > 0 THEN manpower_reduction - 1 END 
                              WHERE truce_length > 0 ;''')
        # remove any expired treaties
        await conn.execute('''DELETE FROM cnc_peace_treaties WHERE truce_length <= 0;''')

        # === WAR TIMER UPDATING ===
        await conn.execute('''UPDATE cnc_wars SET turns = turns + 1 WHERE active = True;''')
        # update any status quo wars as appropriate
        await conn.execute('''UPDATE cnc_wars SET war_score[2] = war_score[2] + POWER(turns, 1.27) 
                              WHERE db = 'Status Quo' AND active = True AND war_score[1] < 60;''')

        # === GENERAL TIMEOUT UPDATING ===
        await conn.execute('''UPDATE cnc_generals SET timeout = timeout - 1;''')
        # list all timed out generals
        timed_out_generals = await conn.fetch('''SELECT * FROM cnc_generals WHERE timeout <= 0;''')
        # add to the dm notification for each user
        for general in timed_out_generals:
            # army command optional
            if general['army_id']:
                # get army name
                army_name = await conn.fetchval('''SELECT army_name FROM cnc_armies 
                                                   WHERE army_id = $1;''', general['army_id'])
                army_command = f"They were commanding the {army_name} at the time of their death."
            else:
                army_command = ""
            # add to the dm notification
            self.user_dm_notifications[general['owner_id']] += (f"General **{general['name']}** has sadly passed away. "
                                                                f"Their legacy will live on in their achievements."
                                                                f"{army_command}\n")
        # remove timed out generals
        await conn.execute('''DELETE FROM cnc_generals WHERE timeout <= 0;''')

        # === TECHNOLOGY/RESEARCHING ===
        await conn.execute('''UPDATE cnc_researching SET turns = turns - 1;''')
        # complete research as necessary
        completed_research = await conn.fetch('''SELECT * FROM cnc_researching WHERE turns <= 0;''')
        for tech in completed_research:
            # update the user's techs
            await conn.execute('''UPDATE cnc_users SET tech = tech || $2 WHERE user_id = $1;''',
                               tech['user_id'], tech['tech'])
            # pull the db call of the tech
            tech_call = await conn.fetchval('''SELECT db_call FROM cnc_tech WHERE name = $1;''',
                                            tech['tech'])
            # execute the db call
            await conn.execute(tech_call, tech['user_id'])
            # add to the dm notification
            self.user_dm_notifications[tech['user_id']] += (f"Scholars have completed researching the "
                                                            f"{tech['tech']} technology!\n")
        # remove the completed research
        await conn.execute('''DELETE FROM cnc_researching WHERE turns <= 0;''')

        # === GOVERNMENT MODIFICATION TIMERS ===
        # reduce all by one
        await conn.execute('''UPDATE cnc_users
                              SET govt_type_countdown = CASE WHEN govt_type_countdown > 0 THEN govt_type_countdown - 1 END,
                                  govt_subtype_countdown = CASE WHEN govt_subtype_countdown > 0 THEN govt_subtype_countdown - 1 END;''')


    # TODO events










