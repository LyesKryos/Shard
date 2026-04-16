import asyncpg
import discord
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
        # run the GP updates
        await self._great_power_score()
        # run the timer updates
        await self._timer_updates()
        # run the tidy system
        await self._tidy_system()
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
            # if the user is a federal republic, increase the trade good access by an additional 5%
            if user['govt_subtype'] == "Federal":
                trade_good_production_access += 0.05
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
                # if the user has Livestock Farming, increase by 3%
                if "Livestock Farming" in user['tech']:
                    manpower_count *= 1.03
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
                # define development production boost
                development_production_boost = 0.6 + (prov['development']/17)**0.6
                # define citizen production
                citizen_production = max((prov['citizens']*development_production_boost) / 3872, 1)
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
                # increase the trade good's value by +2% for the local trade tech
                if "Local Trade" in user['tech']:
                    trade_good_value *= 1.05
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
                # define province's national unrest contribution based on the number of citizens
                prov_nat_unrest = max(((prov['citizens'] + citizen_growth)/1500),0)**1.22
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
            trade_good_production_access += 0.05 * (trade_pact_count * (1.05 if "International Trade" in user['tech'] else 1))
            # get a count of all the embargoes issued against this user
            embargo_count = await conn.fetchval('''SELECT count(id) FROM cnc_embargoes 
                                                   WHERE target = $1;''', user['name'])
            # for each embargo, decrease the trade good production access exponentially up to a max of 35% reduction
            trade_good_production_access -= min((embargo_count * 0.05) ** 1.6, 0.35)
            # calculate total trade value for this nation, protecting against negative values
            trade_value = max(trade_good_production * trade_good_production_access, 0)

            # === MANPOWER ===
            # peace treaty enforced manpower reduction
            treaty_enforced_manpower_reduction = 1 - sum([pt['manpower_reduction'] if pt['manpower_reduction'] else 0
                                                      for pt in peace_treaties])
            # log the manpower
            logging.getLogger(__name__).info(f"{user['name']} | manpower total: {manpower_count+3000}")
            # update manpower set on manpower regen rate
            await conn.execute('''UPDATE cnc_users SET manpower = manpower + $2 WHERE user_id = $1;''',
                               user['user_id'], 3000 + round(manpower_count * (user['manpower_regen'] / 100)))
            # enforce manpower cap
            manpower_cap = 3000 + (round((user['manpower_access']) * manpower_count) * treaty_enforced_manpower_reduction)
            await conn.execute('''UPDATE cnc_users SET manpower = $2 WHERE user_id = $1 AND manpower > $2;''',
                               user['user_id'], manpower_cap)
            # log the manpower cap
            logging.getLogger(__name__).info(f"{user['name']} | manpower cap: {manpower_cap} = {manpower_count} * {user['manpower_access']}")
    
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
            mil_stab_loss = ((user['last_mil_auth_gain']*2)-8) if user['last_mil_auth_gain'] < 4 else 0
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
            # set total national unrest as an integer 
            total_national_unrest = int(total_national_unrest)
            # if there is not currently a rebellion; also, tribal governments cannot have an uprising
            if not user['active_rebellion'] and not user['active_civil_war'] and not user['active_revolution'] and user['govt_type'] != 'Tribal':
                # define list of possible revolutions; anarchy is always an option!
                revolution_choices = ["Anarchy"]
                if "Divine Right" in user['tech'] and user['govt_type'] != "Monarchy":
                    revolution_choices.append("Monarchy")
                if "Patrician Values" in user['tech'] and user['govt_type'] != "Republic":
                    revolution_choices.append("Republic")
                if "Democratic Ideals" in user['tech'] and user['govt_type'] != "Democracy":
                    revolution_choices.append("Democracy")
                if "Revolutionary Ideals" in user['tech'] and user['govt_type'] != "Equalism":
                    revolution_choices.append("Equalism")
                # calculate the chance for a revolution based on the unrest
                if total_national_unrest > 70:
                    # roll the dice
                    revolution_chance = randint(1, total_national_unrest)
                    # if the user govt type is anarchy, increase chance by 25%
                    if user['govt_type'] == "Anarchy":
                        revolution_chance *= 1.25
                    # if the roll is greater than 60
                    if revolution_chance > 60:
                        # choose a random revolution
                        revolution_type = choice(revolution_choices)
                        # trigger a revolution
                        await conn.execute('''UPDATE cnc_users SET active_revolution = $2 WHERE user_id = $1;''',
                                           user['user_id'], revolution_type)
                        # set a number of provinces as rebellious on national unrest
                        rebellious_provinces = await conn.fetchval('''SELECT array_agg(id)
                                                                   FROM cnc_provinces
                                                                   WHERE owner_id = $1
                                                                     AND id != $2
                                                                   ORDER BY RANDOM() limit $3;''',
                                                                user['user_id'], user['capital'],
                                                                min(total_national_unrest / 10, len(controlled_provs)*.75))
                        # update the rebellious provinces
                        for prov in rebellious_provinces:
                            # update the db to set occupier = 1 (aka rebels)
                            await conn.execute('''UPDATE cnc_provinces
                                                  SET occupier_id = 1
                                                  WHERE id = $1;''', prov)
                        # add to DM notification
                        dm_notification += (f"**A revolution has begun in our nation!** Rebels supporting a new "
                                            f"Government Type, {revolution_type}, have risen up in "
                                            f"arms against the {user['pretitle']} of {user['name']}! "
                                            f"They have occupied these provinces: {', '.join(rebellious_provinces)}."
                                            f"We must react quickly, or they may overwhelm our nation!\n")

                # calculate the chance for a civil war based on the unrest
                elif total_national_unrest > 65:
                    # roll the dice
                    civil_war_chance = randint(1, total_national_unrest)
                    # if the user is anarchist, reduce civil war chance by 100
                    if user['govt_type'] == "Anarchy":
                        civil_war_chance -= 100
                    # if the user is an elective monarchy, reduce chance by 25%
                    if user['govt_subtype'] == "Elective":
                        civil_war_chance *= .75
                    # if the user is a direct democracy, reduce chance by 75%
                    if user['govt_subtype'] == "Direct":
                        civil_war_chance *= .25
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
                        # set a number of provinces as rebellious on national unrest
                        rebellious_provinces = await conn.fetchval('''SELECT array_agg(id)
                                                                   FROM cnc_provinces
                                                                   WHERE owner_id = $1
                                                                     AND id != $2
                                                                   ORDER BY RANDOM() LIMIT $3;''',
                                                                user['user_id'], user['capital'],
                                                                min(total_national_unrest / 10, len(controlled_provs)*.75))
                        # update the rebellious provinces
                        for prov in rebellious_provinces:
                            # update the db to set occupier = 1 (aka rebels)
                            await conn.execute('''UPDATE cnc_provinces
                                                  SET occupier_id = 1
                                                  WHERE id = $1;''', prov)
                        # add to DM notification
                        dm_notification += (f"**A Civil War has begun in our nation!** An armed faction of citizens "
                                            f"that supports a *{civil_war_type}* {user['govt_type']} have risen up and "
                                            f"threaten to overthrow the legitimate government of the "
                                            f"{user['pretitle']} of {user['name']}! They have occupied these provinces:"
                                            f" {', '.join(rebellious_provinces)}.\n")

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
                        rebellious_provinces = await conn.fetchval('''SELECT array_agg(id)
                                                                   FROM cnc_provinces
                                                                   WHERE owner_id = $1
                                                                     AND id != $2
                                                                   ORDER BY RANDOM() LIMIT $3;''',
                                                                user['user_id'], user['capital'],
                                                                min(total_national_unrest / 10, len(controlled_provs)*.75))
                        # update the rebellious provinces
                        for prov in rebellious_provinces:
                            # update the db to set occupier = 1 (aka rebels)
                            await conn.execute('''UPDATE cnc_provinces  
                                                  SET occupier_id = 1
                                                  WHERE id = $1;''', prov)
                        # add to DM notification
                        dm_notification += (f"**Rebellious factions** have risen up in "
                                            f"arms against the {user['pretitle']} of {user['name']}! "
                                            f"They have occupied these provinces: {', '.join(rebellious_provinces)}."
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
                govt_gain = await conn.fetchval('''SELECT econ_auth
                                       FROM cnc_govts
                                       WHERE govt_subtype = $1;''',
                                    user['govt_subtype'])
                econ_auth_gain += govt_gain
                logging.getLogger(__name__).info(f"econ auth\n{user['name']} | government type gain: {econ_auth_gain}")
                # add the trade value
                econ_auth_gain += trade_value
                logging.getLogger(__name__).info(f"{user['name']} | trade value: {trade_value} = "
                                                 f"{trade_good_production} * {trade_good_production_access}")
                # calculate tax income
                tax_income = average_dev * ((user['tax_level'] + tax_effect_boost)/100)
                econ_auth_gain += tax_income
                logging.getLogger(__name__).info(f"{user['name']} | tax income: {tax_income}")
                # pull all mines
                mines = await conn.fetchval('''SELECT COUNT(id) FROM cnc_provinces 
                                               WHERE 'Mine' = ANY(structures) 
                                                 AND (owner_id = $1 AND occupier_id = $1);''',
                                            user['user_id'])
                # for every mine, add 0.5
                mine_gain = 0.5 * mines
                econ_auth_gain += mine_gain
                logging.getLogger(__name__).info(f"{user['name']} | mine gain: {mine_gain}")
                # check for techs
                if "Currency" in user['tech']:
                    econ_auth_gain += 1
                    logging.getLogger(__name__).info(f"{user['name']} | currency gain: {1}")
                if "Economics" in user['tech']:
                    econ_auth_gain += 1
                    logging.getLogger(__name__).info(f"{user['name']} | economics gain: {1}")
                if "Banking and Investment" in user['tech']:
                    econ_auth_gain += 1
                    logging.getLogger(__name__).info(f"{user['name']} | banking gain: {1}")
                if "Guilds" in user['tech']:
                    econ_auth_gain += 1
                    logging.getLogger(__name__).info(f"{user['name']} | guilds gain: {1}")

                # calculate reductions
                # reduce from public spending
                econ_auth_gain -= user['public_spend']
                logging.getLogger(__name__).info(f"{user['name']} | public spend reduction: {user['public_spend']}")
                # reduce from reparations
                for peace in peace_treaties:
                    # if there is one with econ reparations, reduce
                    if peace['reparations']:
                        reparations = peace['reparations'][0] if peace['reparations'][0] > 0 else 0
                        econ_auth_gain -= reparations
                        logging.getLogger(__name__).info(f"{user['name']} | reparations reduction: {reparations}")
                    # if there is one with dismantle, reduce
                    if peace['dismantle']:
                        econ_auth_gain -= 3
                        logging.getLogger(__name__).info(f"{user['name']} | dismantle reduction: 3")

                # update econ auth
                await conn.execute('''UPDATE cnc_users 
                                      SET econ_auth = $2, last_econ_auth_gain = $2, econ_auth_gain = $3 
                                      WHERE user_id = $1;''', user['user_id'], floor(econ_auth_gain),
                                   floor(econ_auth_gain)-user['last_econ_auth_gain'])
                logging.getLogger(__name__).info(f"{user['name']} | econ auth gain: {floor(econ_auth_gain)}")
            # otherwise, set at 0
            else:
                await conn.execute('''UPDATE cnc_users 
                                      SET econ_auth = 0, last_econ_auth_gain = 0, econ_auth_gain = $2 
                                      WHERE user_id = $1;''', user['user_id'], 0-user['last_econ_auth_gain'])

            # === MILITARY AUTHORITY ===
            if user['govt_subtype'] != "Pacifistic":
                # calculate military authority gain
                mil_auth_gain = 0
                # add mil auth based on govt subtype
                govt_gain = await conn.fetchval('''SELECT mil_auth
                                       FROM cnc_govts
                                       WHERE govt_subtype = $1;''', user['govt_subtype'])
                mil_auth_gain += govt_gain
                logging.getLogger(__name__).info(f"mil auth\n{user['name']} | government type gain: {mil_auth_gain}")
                # for each military alliance, add 1 + x^0.625
                mil_alliance_gain = (military_alliances**1.05)+1
                mil_auth_gain += mil_alliance_gain
                logging.getLogger(__name__).info(f"{user['name']} | military alliance gain: {mil_alliance_gain}")
                # based on the average development, add dev/5
                dev_gain = average_dev/5
                mil_auth_gain += average_dev/5
                logging.getLogger(__name__).info(f"{user['name']} | dev gain: {dev_gain}")
                # calculate reductions
                # reduce from military upkeep
                mil_auth_gain -= user['mil_upkeep']
                logging.getLogger(__name__).info(f"{user['name']} | mil upkeep reduction: {user['mil_upkeep']}")
                # reduce from wars if primary attacker
                for war in wars:
                    if war['primary_attacker'] == user['name']:
                        mil_auth_gain -= 2
                        logging.getLogger(__name__).info(f"{user['name']} | war reduction: 2")
                # reduce from reparations
                for peace in peace_treaties:
                    # if there is one with mil reparations, reduce
                    if peace['reparations']:
                        reparations = peace['reparations'][1] if peace['reparations'][1] > 0 else 0
                        mil_auth_gain -= reparations
                        logging.getLogger(__name__).info(f"{user['name']} | reparations reduction: {reparations}")
                    # there there is one with dismantle, reduce
                    if peace['dismantle']:
                        mil_auth_gain -= 3
                        logging.getLogger(__name__).info(f"{user['name']} | dismantle reduction: 3")

                # update mil auth
                await conn.execute('''UPDATE cnc_users 
                                      SET mil_auth = $2, last_mil_auth_gain = $2, mil_auth_gain = $3
                                      WHERE user_id = $1;''', user['user_id'], floor(mil_auth_gain),
                                   floor(mil_auth_gain)-user['last_mil_auth_gain'])
                logging.getLogger(__name__).info(f"{user['name']} | mil auth gain: {floor(mil_auth_gain)}")
            # otherwise, set at 0
            else:
                await conn.execute('''UPDATE cnc_users SET mil_auth = 0, last_mil_auth_gain = 0, mil_auth_gain = $2
                                      WHERE user_id = $1;''', user['user_id'], 0-user['last_mil_auth_gain'])
                logging.getLogger(__name__).info(f"{user['name']} | mil auth gain: 0")

            # === POLITICAL AUTHORITY ====
            pol_auth_gain = 0
            # add pol auth based on govt subtype
            govt_gain = await conn.fetchval('''SELECT pol_auth FROM cnc_govts WHERE govt_subtype = $1;''',
                                                user['govt_subtype'])
            pol_auth_gain += govt_gain
            logging.getLogger(__name__).info(f"pol auth\n{user['name']} | government type gain: {pol_auth_gain}")
            # for each diplomatic relation, add x^1.35 + x/2
            relations_gain =(diplomatic_relations**1.15) + (diplomatic_relations/2)
            pol_auth_gain += relations_gain
            logging.getLogger(__name__).info(f"{user['name']} | diplomatic relations gain: {relations_gain}")
            # based on the average development, add dev/5
            dev_gain = average_dev/5
            pol_auth_gain += dev_gain
            logging.getLogger(__name__).info(f"{user['name']} | dev gain: {dev_gain}")
            # add pol auth based on techs
            if "Basic Government" in user['tech']:
                pol_auth_gain += 1
                logging.getLogger(__name__).info(f"{user['name']} | basic gov gain: {1}")

            # calculate reductions
            # reduce pol auth based on average national unrest
            nat_unrest_reduction = average_national_unrest/15
            pol_auth_gain -= nat_unrest_reduction * (.9 if user['govt_subtype'] == "Constitutional" else 1)
            logging.getLogger(__name__).info(f"{user['name']} | national unrest reduction: {nat_unrest_reduction}")
            # reduce pol auth based on the number of OTHER members in the military alliance
            military_alliance_reduction = military_alliances - 1 if military_alliances != 0 else 0
            logging.getLogger(__name__).info(f"{user['name']} | military alliance reduction: {military_alliance_reduction}")
            # reduce pol auth based on issued relations
            logging.getLogger(__name__).info(f"{user['name']} | trade pact reduction: {trade_pact_count}")
            embargo_reduction = await conn.fetchval('''SELECT count(id) FROM cnc_embargoes WHERE sender = $1;''',
                                                 user['name'])
            # add together
            pol_auth_gain -= embargo_reduction + trade_pact_count + military_alliance_reduction
            # modify if republic
            if user['govt_type'] == "Republic":
                # relation reduction definition
                relation_reduction = embargo_reduction + trade_pact_count + military_alliance_reduction
                # reduce impact
                pol_auth_gain += 2 if relation_reduction >= 2 else 0
            logging.getLogger(__name__).info(f"{user['name']} | embargo reduction: {embargo_reduction}")
            # if there is a capital, reduce by 1
            if user['capital']:
                pol_auth_gain -= 1
                logging.getLogger(__name__).info(f"{user['name']} | capital reduction: 1")
            # reduce pol auth based on reparations
            for peace in peace_treaties:
                # if there is one with pol reparations, reduce
                if peace['reparations']:
                    reparations = peace['reparations'][2] if peace['reparations'][2] > 0 else 0
                    pol_auth_gain -= logging.getLogger(__name__).info(f"{user['name']} | reparations reduction: {reparations}")
                # if there is one with dismantle, reduce
                if peace['dismantle']:
                    pol_auth_gain -= 3
                    logging.getLogger(__name__).info(f"{user['name']} | dismantle reduction: 3")

            # add pol auth gain
            await conn.execute('''UPDATE cnc_users SET pol_auth = $2, last_pol_auth_gain = $2, pol_auth_gain = $3 
                                  WHERE user_id = $1;''', user['user_id'], floor(pol_auth_gain),
                               floor(pol_auth_gain)-user['last_pol_auth_gain'])
            logging.getLogger(__name__).info(f"{user['name']} | pol auth gain: {floor(pol_auth_gain)}")

            # === ARMY/FORT RESET ===
            await conn.execute('''UPDATE cnc_armies SET movement = $2 WHERE owner_id = $1;''',
                               user['user_id'], user['movement_cap'])
            await conn.execute('''UPDATE cnc_provinces SET fort_level = $2 
                                  WHERE owner_id = $1 AND occupier_id = $1 AND 'Fort' = ANY(structures);''',
                               user['user_id'], user['fort_level'])
            # if the user's govt type is Monarchy and they have a capital, add one fort level for free
            if user['capital'] and user['govt_type'] == "Monarchy":
                await conn.execute('''UPDATE cnc_provinces SET fort_level = fort_level + 1 WHERE id = $1;''',
                                   user['capital'])

            # === FREE GOVERNMENT CHANGE CHECK ===
            # pull the total development
            total_dev = await conn.fetchval('''SELECT sum(development) FROM cnc_provinces 
                                               WHERE owner_id = $1 AND occupier_id = $1;''', user['user_id'])
            # if the total dev is above 50 and the user's govt type is Tribal, give free government change if they have not already gotten it
            if total_dev > 50 and user['govt_type'] == "Tribal" and not user['free_govt_change']:
                await conn.execute('''UPDATE cnc_users SET free_govt_change = TRUE WHERE user_id = $1;''',
                                   user['user_id'])
                dm_notification += f"{user['name']} has gained free government change!\n"

            # === OVEREXTENSION CALCULATIONS ===
            # if the government is tribal, set to 25
            if user['govt_type'] == "Tribal":
                overextension_limit = 25
            # if the government subtype is free city set to 20
            elif user['govt_subtype'] == "Free City":
                overextension_limit = 20
            # otherwise, set it to 45
            else:
                overextension_limit = 45
            # if user has the imperialism tech, set to +10
            if "Imperialism" in user['tech']:
                overextension_limit += 10
            # set overextension
            await conn.execute('''UPDATE cnc_users SET overextend_limit = $2 WHERE user_id = $1;''', user['user_id'], overextension_limit)


            # add user dm notifications to the list
            self.user_dm_notifications[user['user_id']] = dm_notification
            
        # outside the loop functions
        for user in user_list:
            # calculate puppets/overlords loss/gain
            if user['overlord']:
                # reduce by a quarter of the gain, min 1
                await conn.execute('''UPDATE cnc_users 
                                      SET econ_auth             = econ_auth - $1, 
                                          last_econ_auth_gain   = last_econ_auth_gain - $1,
                                          econ_auth_gain        = econ_auth_gain - $1,
                                          mil_auth              = mil_auth - $2, 
                                          last_mil_auth_gain    = last_mil_auth_gain - $2, 
                                          mil_auth_gain         = mil_auth_gain - $2,
                                          pol_auth              = pol_auth - $3, 
                                          last_pol_auth_gain    = last_pol_auth_gain - $3, 
                                          pol_auth_gain         = pol_auth_gain - $3
                                      WHERE user_id = $4;''',
                                   max(floor(user['last_econ_auth_gain']/4), 1),
                                   max(floor(user['last_mil_auth_gain']/4), 1),
                                   max(floor(user['last_pol_auth_gain']/4), 1),
                                   user['user_id'])
                logging.getLogger(__name__).info(f"{user['name']} | puppet status loss: "
                                                 f"{max(floor(user['last_econ_auth_gain']/4), 1),
                                                   max(floor(user['last_mil_auth_gain']/4), 1),
                                                   max(floor(user['last_pol_auth_gain']/4), 1)}")
                # update the overlord's gains
                await conn.execute('''UPDATE cnc_users
                                      SET econ_auth             = econ_auth + $1,
                                          last_econ_auth_gain   = last_econ_auth_gain + $1,
                                          econ_auth_gain        = econ_auth_gain + $1,
                                          mil_auth              = mil_auth + $2,
                                          last_mil_auth_gain    = last_mil_auth_gain + $2,
                                          mil_auth_gain         = mil_auth_gain + $2,
                                          pol_auth              = pol_auth + $3,
                                          last_pol_auth_gain    = last_pol_auth_gain + $3,
                                          pol_auth_gain         = pol_auth_gain + $3
                                      WHERE user_id = $4;''',
                                   max(floor(user['last_econ_auth_gain'] / 4), 1),
                                   max(floor(user['last_mil_auth_gain'] / 4), 1),
                                   max(floor(user['last_pol_auth_gain'] / 4), 1),
                                   user['overlord'])
                logging.getLogger(__name__).info(f"{user['overlord']} | overlord status gain: "
                                                 f"{max(floor(user['last_econ_auth_gain']/4), 1),
                                                   max(floor(user['last_mil_auth_gain']/4), 1),
                                                   max(floor(user['last_pol_auth_gain']/4), 1)}")

            # === GOVERNMENT TYPE/SUBTYPE ENFORCEMENTS ===
            # if the user is a merchant republic, remove all embargoes
            if user['govt_subtype'] == "Merchant":
                removed_embargoes = await conn.execute('''DELETE FROM cnc_embargoes WHERE sender = $1 RETURNING target;''',
                                                       user['name'])
                # notify users
                for embargoed_user in removed_embargoes:
                    # get the user id
                    unembargoed_user = await conn.fetchval('''SELECT user_id FROM cnc_users WHERE name = $1;''',
                                                           embargoed_user['target'])
                    # add to the user's dm
                    self.user_dm_notifications[unembargoed_user] += (f"{user['name']} has removed all "
                                                                     f"embargoes from {embargoed_user['target']} "
                                                                     f"because they are a Merchant Republic.\n")
                # notify republic
                self.user_dm_notifications[user['user_id']] += (f"{user['name']} has been obliged to end all embargoes "
                                                                f"against other nations because they are a "
                                                                f"Merchant Republic.\n")

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
                               prov['id'], max(floor(citizen_production),1))
        # get turn number
        turn = await conn.fetchval('''SELECT number::INTEGER FROM cnc_data WHERE name = 'Turn';''')
        # get the turn-production coefficient:
        turn_production_coefficient = min(.075*(turn**.56), 1) * 500
        # pull all the trade goods
        trade_goods_raw = await conn.fetch('''SELECT * FROM cnc_trade_goods;''')
        # for each trade good
        for good in trade_goods_raw:
            # get the total production of all provinces that produce that trade good
            total_production = await conn.fetchval('''SELECT SUM(production)::INTEGER FROM cnc_provinces 
                                                      WHERE trade_good = $1;''', good['name'])
            # calculate the proper market value of the good
            new_market_value = max(min((turn_production_coefficient/total_production)**1.03, 27), .5)
            # execute the update
            await conn.execute('''UPDATE cnc_trade_goods SET market_value = $2 WHERE name = $1;''',
                               good['name'], round(new_market_value,2))

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
                               tech['user_id'], [tech['tech']])
            # pull the db call of the tech
            tech_call = await conn.fetchval('''SELECT db_call FROM cnc_tech WHERE name = $1 AND db_call IS NOT NULL;''',
                                            tech['tech'])
            # execute the db call if it is not none
            if tech_call is not None:
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

    async def _great_power_score(self):
        # establish connection
        conn = self.conn
        # set all nations to non-gp
        await conn.execute('''UPDATE cnc_users SET gp = FALSE;''')
        # pull each user's info
        all_users = await conn.fetch('''SELECT * FROM cnc_users;''')
        # for each user
        for user in all_users:
            # define base gp score
            gp_score = 0
            # get development and citizens
            citizens = await conn.fetchval('''SELECT SUM(citizens) FROM cnc_provinces WHERE owner_id = $1 AND occupier_id = $1;''', user['user_id'])
            development = await conn.fetchval('''SELECT AVG(development) FROM cnc_provinces WHERE owner_id = $1 AND occupier_id = $1;''', user['user_id']) 
            # add citizen and development score
            gp_score += citizens/10000
            gp_score += float(development)/7.5
            # add auth gains
            gp_score += user['econ_auth'] + user['pol_auth'] + user['mil_auth']
            # stability score gain
            gp_score += user['stability']/10
            # get number of armies and generals/quality
            army_troop_count = await conn.fetchval('''SELECT SUM(troops) FROM cnc_armies WHERE owner_id = $1;''', user['user_id'])
            general_score = await conn.fetchval('''SELECT COUNT(general_id) * AVG(level) FROM cnc_generals WHERE owner_id = $1;''', user['user_id'])
            # add troop count and general score
            gp_score += int(army_troop_count)/3000 if army_troop_count is not None else 0
            gp_score += float(general_score) if general_score is not None else 0
            # add techs
            tech_count = await conn.fetchval('''SELECT cardinality(tech) FROM cnc_users WHERE user_id = $1;''', user['user_id'])
            # add score
            gp_score += int(tech_count)
            # count military alliances
            alliances_count = await conn.fetchval('''SELECT cardinality(members) FROM cnc_alliances WHERE $1 = ANY(members);''', user['name'])
            # count trade pacts
            pacts_count = await conn.fetchval('''SELECT count(id) FROM cnc_trade_pacts WHERE $1 = ANY(members);''', user['name'])
            # count diplomatic relations
            dr_count = await conn.fetchval('''SELECT count(id) FROM cnc_drs WHERE $1 = ANY(members);''', user['name'])
            # add scores
            gp_score += alliances_count if alliances_count is not None else 0
            gp_score += pacts_count if pacts_count is not None else 0
            gp_score += dr_count if dr_count is not None else 0
            # update score for user
            await conn.execute('''UPDATE cnc_users SET gp_score = $2 WHERE user_id = $1;''', user['user_id'], gp_score)

        # remove all great powers
        await conn.execute('''UPDATE cnc_users SET gp = FALSE;''')
        # once all users are done, check to define the top 3, if they have more than 50 GP score
        gp_check = await conn.fetch('''SELECT * FROM cnc_users WHERE gp_score > 50 ORDER BY gp_score DESC LIMIT 3;''')
        # if none are above 50, set no one
        if len(gp_check) == 0:
            return
        # otherwise, set the top three (or fewer)
        else:
            # for each gp, set the value and update their extension limit
            for gp in gp_check:
                await conn.execute('''UPDATE cnc_users 
                                      SET gp = TRUE, overextend_limit = overextend_limit + 15 
                                      WHERE user_id = $1;''', gp['user_id'])
            # now check all alliances to remove unpermitted gps
            # remove all great powers that were in an alliance and notify them
            removed_great_powers = await conn.fetch('''WITH nations_to_remove AS 
                                                                (SELECT a.id,a.members as old_alliance, 
                                                                        ARRAY(SELECT elem FROM unnest(a.members) 
                                                                        WITH ORDINALITY AS t(elem, ord) 
                                                                        JOIN cnc_users u ON t.elem = u.name 
                                                                        AND u.gp = TRUE ORDER BY ord OFFSET 1) as removed 
                                                                 FROM cnc_alliances a 
                                                                 WHERE (SELECT COUNT(*) 
                                                                        FROM unnest(a.members) 
                                                                                 AS nation JOIN cnc_users u 
                                                                                                ON nation = u.name 
                                                                                                    AND u.gp = TRUE) > 1), 
                                                            updated AS (UPDATE cnc_alliances a 
                                                       SET members = ARRAY(SELECT elem 
                                                           FROM unnest(a.members) WITH ORDINALITY AS t(elem, ord) 
                                                           WHERE elem NOT IN (SELECT unnest(n.removed) 
                                                           FROM nations_to_remove n WHERE n.id = a.id) ORDER BY ord) 
                                                       FROM nations_to_remove n 
                                                       WHERE a.id = n.id RETURNING a.id, a.members as new_alliance) 
            SELECT u.id, n.old_alliance, u.new_alliance, n.removed as removed_nations 
            FROM updated u JOIN nations_to_remove n ON u.id = n.id;''')

            # for each removed great power, notify all members of the alliance
            for alliance in removed_great_powers:
                for member in alliance['new_alliance']:
                    # get their user id
                    user_id = await conn.fetchval('''SELECT user_id
                                                     FROM cnc_users
                                                     WHERE name = $1;''', member)
                    # add to the dm notification
                    self.user_dm_notifications[user_id] += (
                        f"Your ally(s), {', '.join(alliance['removed_nations'])}, have "
                        f"been removed from your alliance. They have become a "
                        f"Great Power, but the alliance already contains a Great Power.\n")
                for member in alliance['removed_nations']:
                    # get their user id
                    user_id = await conn.fetchval('''SELECT user_id
                                                     FROM cnc_users
                                                     WHERE name = $1;''', member)
                    # add to the dm notification
                    self.user_dm_notifications[user_id] += (
                        f"You have been removed from your alliance because you exceeded"
                        f" the Great Power alliance limit.\n")

            # get the number of puppets each user has (if any)
            puppet_count = await conn.fetch('''SELECT u.user_id, u.name, u.gp, COUNT(p.user_id) as puppet_count, array_agg(p.user_id) as puppet_ids FROM cnc_users u INNER JOIN cnc_users p ON p.overlord = u.user_id GROUP BY u.user_id, u.name, u.gp;''')
            # check that the count is correct
            for overlord in puppet_count:
                # if the overlord has more than two puppets and is not a gp, 
                if overlord['puppet_count'] > 2 and not overlord['gp']:
                    # remove a random one
                    freed_puppet = choice(overlord['puppet_ids'])
                    # remove that puppet
                    puppet_name = await conn.execute('''UPDATE cnc_users SET overlord = NULL WHERE user_id = $1 RETURNING name;''', freed_puppet)
                    # notify both users
                    self.user_dm_notifications[overlord['user_id']] += (f"{puppet_name['name']} has been freed from subjugation under {overlord['name']} because we held too many puppets!\n")
                    self.user_dm_notifications[freed_puppet] += f"{puppet_name['name']} has been freed from subjugation under {overlord['name']} because they held too many puppets! Our age of liberation has begun.\n"
                # if the overlord has more than three puppets while being a gp
                if overlord['puppet_count'] > 3 and overlord['gp']:
                    # remove a random one
                    freed_puppet = choice(overlord['puppet_ids'])
                    # remove that puppet
                    puppet_name = await conn.execute('''UPDATE cnc_users SET overlord = NULL WHERE user_id = $1 RETURNING name;''', freed_puppet)
                    # notify both users
                    self.user_dm_notifications[overlord['user_id']] += (f"{puppet_name['name']} has been freed from subjugation under {overlord['name']} because we held too many puppets!\n")
                    self.user_dm_notifications[freed_puppet] += f"{puppet_name['name']} has been freed from subjugation under {overlord['name']} because they held too many puppets! Our age of liberation has begun.\n"

            # if a player has become a great power, remove all overlords and notify both
            removed_overlords = await conn.fetch('''UPDATE cnc_users SET overlord = NULL 
                                                    WHERE gp = TRUE AND overlord is not NULL 
                                                        RETURNING user_id, name, overlord;''')
            # for each removed overlord, notify the overlord and user
            for overlord in removed_overlords:
                self.user_dm_notifications[overlord['overlord']] += (f"{overlord['name']} has been removed from "
                                                                     f"subjugation under our glorious nation "
                                                                     f"because they became a Great Power!\n")
                self.user_dm_notifications[overlord['user_id']] += (f"You have been removed from subjugation under "
                                                                    f"your previous overlord because you are now "
                                                                    f"a Great Power!\n")

            # wrap up
            return

    async def _tidy_system(self):
        # establish connection
        conn = self.conn
        # update all relations to remove blank relations
        await conn.execute('''DELETE FROM cnc_alliances WHERE cardinality(members) < 2;''')
        await conn.execute('''DELETE FROM cnc_trade_pacts WHERE cardinality(members) < 2;''')
        await conn.execute('''DELETE FROM cnc_drs WHERE cardinality(members) < 2;''')
        await conn.execute('''DELETE FROM cnc_military_access WHERE cardinality(members) < 2;''')

    # TODO events