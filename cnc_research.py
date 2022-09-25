import math
import time
from base64 import b64encode
import asyncpg
import traceback
import re
import requests
from PIL import Image, ImageColor
import discord
from discord.ext import commands


class Technology:

    def __init__(self, nation: str, bot: commands.Bot = None, ctx: commands.Context = None, tech: str = None, techs: list = None):
        # nation name
        self.nation = nation
        # tech name
        self.tech = tech
        self.techs = techs
        self.ctx = ctx
        self.bot = bot
        # creates connection pool
        if self.ctx is not None:
            try:
                self.pool: asyncpg.pool = self.ctx.bot.pool
            except Exception:
                self.ctx.bot.logger.warning(traceback.format_exc())
        else:
            try:
                self.pool: asyncpg.pool = self.bot.pool
            except Exception:
                self.bot.logger.warning(traceback.format_exc())


    def sanitize_links_underscore(self, userinput: str) -> str:
        # replaces user input with proper, url-friendly code
        to_regex = userinput.replace(" ", "_")
        return re.sub(r"[^a-zA-Z0-9_-]", ' ', to_regex)

    async def research(self):
        # create connection
        conn = self.pool
        # fetch tech info
        tech = await conn.fetchrow('''SELECT * FROM cnc_tech WHERE name = $1;''', self.tech.title())
        # if the tech doesn't exist
        if tech is None:
            await self.ctx.send(f"No such technology as {self.tech}")
            return
        # fetch userinfo
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', self.ctx.author.id)
        # fetch province count
        province_count = await conn.fetchrow('''SELECT count(*) FROM provinces WHERE owner_id = $1 and occupier_id = $1;''',
                                             userinfo['user_id'])
        if province_count['count'] is None:
            provinces = 0
        else:
            provinces = province_count['count']
        # if tech is already researched
        if self.tech.title() in userinfo['researched']:
            await self.ctx.send(f"{self.tech.title()} has already been researched by {userinfo['username']}.")
            return
        # fetch modifiers
        modifiers = await conn.fetchrow('''SELECT * FROM cnc_modifiers WHERE user_id = $1;''', self.ctx.author.id)
        # set prerequisites
        required_tech = tech['prerequisites']
        # split the all and some requirement
        all_required = required_tech.split(', ')
        some_required = required_tech.split('/')
        # if there are some required and not all
        if len(some_required) >= 2:
            tech_check = any(researched in userinfo['researched'] for researched in some_required)
            if not tech_check:
                await self.ctx.send(f"{userinfo['username']} does not have all the necessary research completed.")
                return
        else:
            tech_check = all(researched in userinfo['researched'] for researched in all_required)
            if not tech_check:
                if all_required[0] != 'None':
                    await self.ctx.send(f"{userinfo['username']} does not have all the necessary research completed.")
                    return
        # fetch current researching
        researching = await conn.fetchrow('''SELECT * FROM cnc_researching WHERE user_id = $1;''', self.ctx.author.id)
        # if the user is already researching a tech
        if researching is not None:
            await self.ctx.send(f"{userinfo['username']} is already researching a technology.")
            return
        # calculated the research time
        research_time = 4 + len(userinfo['researched'])
        # if there is an exclusive tech that conflicts
        if tech['exclusive'] is not None:
            if any(researched in userinfo['researched'] for researched in tech['exclusive']):
                await self.ctx.send(f"{tech['name']} cannot be researched "
                                    f"because it is mutually exclusive with {tech['exclusive']}.")
                return
        # if the user has any research boosters, apply
        research_time *= modifiers['research_mod'] * .5
        research_time += math.floor(provinces/15)
        # check the user focus and the technology's field
        if tech['field'] == "Economy":
            if userinfo['focus'] == "e":
                research_time -= 1
        elif tech['field'] == "Strategy":
            if userinfo['focus'] == "s":
                research_time -= 1
        elif tech['field'] == "Military":
            if userinfo['focus'] == "m":
                research_time -= 1
        # apply research budget
        research_time += (-userinfo['research_budget']/5) + 2
        research_time = round(research_time)
        if research_time <= 0:
            research_time = 1
        # insert into researching and send message
        await conn.execute('''INSERT INTO cnc_researching VALUES ($1, $2, $3);''',
                           self.ctx.author.id, self.tech.title(), int(research_time))
        await self.ctx.send(f"{tech['name']} will be finished researching in {int(research_time)} turns.")

    async def effects(self):
        conn = self.pool
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1;''', self.nation)
        provinces_owned = await conn.fetch('''SELECT * FROM provinces WHERE owner_id = $1;''', userinfo['user_id'])
        if provinces_owned is None:
            provinces_owned = [0]
        else:
            provinces_owned = [p['id'] for p in provinces_owned]
        for t in self.techs:
            if t == 'Currency':
                await conn.execute('''UPDATE cnc_modifiers SET tax_mod = tax_mod + 0.5 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Local Trade':
                await conn.execute('''UPDATE cnc_modifiers SET income_mod = income_mod + (0.005 * $2) 
                WHERE user_id = $1;''', userinfo['user_id'], len(provinces_owned))
            if t == 'Agriculture':
                await conn.execute('''UPDATE cnc_modifiers SET
                grain_mod = grain_mod + 10,
                wine_mod = wine_mod + 10,
                tea_and_coffee_mod = tea_and_coffee_mod + 10,
                sugar_mod = sugar_mod + 10,
                tobacco_mod = tobacco_mod + 10,
                fruits_mod = fruits_mod + 10
                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Economic Stratification':
                await conn.execute('''UPDATE cnc_modifiers SET tax_mod = tax_mod + 0.05 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Regional Trade':
                await conn.execute('''UPDATE cnc_modifiers SET income_mod = income_mod + (0.01 * $2) WHERE user_id = $1;''',
                                   userinfo['user_id'], len(provinces_owned))
            if t == 'Early Industry':
                await conn.execute('''UPDATE cnc_modifiers SET workshop_production_mod = workshop_production_mod + 0.5 
                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Guilds':
                await conn.execute('''UPDATE cnc_modifiers SET workshop_production_mod = workshop_production_mod + 0.5 
                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Local Tariffs':
                await conn.execute('''UPDATE cnc_modifiers SET production_mod = production_mod + 1 
                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Manorialism':
                await conn.execute('''UPDATE cnc_modifiers SET workshop_production_mod = workshop_production_mod + 0.5
                            WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Cottage Industry':
                await conn.execute('''UPDATE cnc_modifiers SET 
                    wool_mod = wool_mod + 10,
                    fish_mod = fish_mod + 10,
                    fur_mod = fur_mod + 10,
                    grain_mod = grain_mod + 10,
                    livestock_mod = livestock_mod + 10,
                    salt_mod = salt_mod + 10,
                    wine_mod = wine_mod + 10,
                    copper_mod = copper_mod + 10,
                    iron_mod = iron_mod + 10,
                    precious_goods_mod = precious_goods_mod + 10,
                    spices_mod = spices_mod + 10,
                    tea_and_coffee_mod = tea_and_coffee_mod + 10,
                    chocolate_mod = chocolate_mod + 10,
                    cotton_mod = cotton_mod + 10,
                    sugar_mod = sugar_mod + 10,
                    tobacco_mod = tobacco_mod + 10,
                    dyes_mod = dyes_mod + 10,
                    silk_mod = silk_mod + 10,
                    rare_wood_mod = rare_wood_mod + 10,
                    glass_mod = glass_mod + 10,
                    paper_mod = paper_mod + 10,
                    precious_stones_mod = precious_stones_mod + 10,
                    coal_mod = coal_mod + 10,
                    fruits_mod = fruits_mod + 10,
                    raw_stone_mod = raw_stone_mod + 10,
                    wood_mod = wood_mod + 10,
                    tin_mod = tin_mod + 10,
                    ivory_mod = ivory_mod + 10
                    WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Global Markets':
                await conn.execute('''UPDATE cnc_modifiers SET market_value = market_vale + 1 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Economics':
                await conn.execute('''UPDATE cnc_modifiers SET tax_mod = tax_mod + 0.05 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Banking and Investments':
                await conn.execute('''UPDATE cnc_modifiers SET trade_route = 1 WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Early Industrialization':
                await conn.execute('''UPDATE cnc_modifiers SET workshop_production_mod = workshop_production_mod + 2 
                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Merchants':
                await conn.execute('''UPDATE cnc_modifiers 
                SET trade_route_efficiency_mod = trade_route_efficiency mod + 0.05
                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Trade Fleets':
                await conn.execute('''UPDATE cnc_modifiers 
                            SET trade_route_efficiency_mod = trade_route_efficiency_mod + 0.05
                            WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Trading Ports':
                await conn.execute('''UPDATE cnc_modifiers 
                            SET trade_route_efficiency_mod = trade_route_efficiency_mod + (0.01 * $2)
                            WHERE user_id = $1;''', userinfo['user_id'], userinfo['portlimit'][0])
            if t == 'Privateering':
                incoming_trade = await conn.fetchrow('''SELECT count(*) FROM cnc_interactions
                WHERE recipient = $1 AND active = True;''', self.nation)
                if incoming_trade['count'] is None:
                    trade_count = 0
                else:
                    trade_count = incoming_trade['count']
                await conn.execute('''UPDATE cnc_modifiers 
                SET trade_route_efficiency_mod = trade_route_efficiency_mod + $2 WHERE user_id = $1;''',
                                   userinfo['user_id'], trade_count * 0.01)
            if t == 'Predatory Trading':
                await conn.execute('''UPDATE cnc_modifiers 
                            SET trade_route_efficiency_mod = trade_route_efficiency_mod + 0.01
                            WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Trade Regulations':
                trade_count = 0
                incoming_trade = await conn.fetchrow('''SELECT count(*) FROM cnc_interactions
                                WHERE recipient = $1 AND active = True;''', self.nation)
                if incoming_trade['count'] is not None:
                    trade_count += incoming_trade['count']
                outgoing_trade = await conn.fetchrow('''SELECT count(*) FROM cnc_interactions
                                                WHERE sender = $1 AND active = True;''', self.nation)
                if outgoing_trade['count'] is not None:
                    trade_count += incoming_trade['count']
                await conn.execute('''UPDATE cnc_modifiers 
                            SET trade_route_efficiency_mod = trade_route_efficiency_mod + (0.01 * $2)
                            WHERE user_id = $1;''', userinfo['user_id'], trade_count)
            if t == 'Heraldry':
                await conn.execute('''UPDATE cnc_modifiers 
                SET national_unrest_suppression_efficiency_mod = national_unrest_suppression_efficiency_mod + 0.25 
                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Philosophy':
                await conn.execute('''UPDATE cnc_modifiers 
                SET national_unrest_suppression_efficiency_mod = national_unrest_suppression_efficiency_mod + 0.25 
                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Religion':
                await conn.execute('''UPDATE cnc_modifiers 
                SET national_unrest_suppression_efficiency_mod = national_unrest_suppression_efficiency_mod + 0.25 
                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'City Administration':
                await conn.execute('''UPDATE cnc_modifiers SET tax_mod = tax_mod + 0.01 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Regional Governance':
                await conn.execute('''UPDATE cnc_modifiers 
                SET local_unrest_suppresssion_efficiency_mod = local_unrest_suppresssion_efficiency_mod + 0.01
                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'National Government':
                await conn.execute('''UPDATE cnc_modifiers 
                SET national_unrest_suppression_efficiency_mod = national_unrest_suppression_efficiency_mod + 0.05
                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Machines':
                await conn.execute('''UPDATE cnc_modifiders SET workshop_production_mod = workshop_production_mod + 0.5
                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Printing Press':
                await conn.execute('''UPDATE cnc_modifiers 
                SET national_unrest_suppression_efficiency_mod = national_unrest_suppression_efficiency_mod + 0.05
                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Irrigation':
                await conn.execute('''UPDATE cnc_modifiers SET
                            grain_mod = grain_mod + 10,
                            wine_mod = wine_mod + 10,
                            tea_and_coffee_mod = tea_and_coffee_mod + 10,
                            sugar_mod = sugar_mod + 10,
                            tobacco_mod = tobacco_mod + 10,
                            fruits_mod = fruits_mod + 10
                            WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Animal Husbandry':
                await conn.execute('''UPDATE cnc_modifiers SET 
                    wool_mod = wool_mod + 10,
                    fish_mod = fish_mod + 10,
                    fur_mod = fur_mod + 10,
                    grain_mod = grain_mod + 10,
                    livestock_mod = livestock_mod + 10 WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Livestock Farming':
                await conn.execute('''UPDATE cnc_modifiers SET 
                    wool_mod = wool_mod + 10,
                    fish_mod = fish_mod + 10,
                    fur_mod = fur_mod + 10,
                    grain_mod = grain_mod + 10,
                    livestock_mod = livestock_mod + 10 WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Crop Rotation':
                await conn.execute('''UPDATE cnc_modifiers SET
                            grain_mod = grain_mod + 10,
                            wine_mod = wine_mod + 10,
                            tea_and_coffee_mod = tea_and_coffee_mod + 10,
                            sugar_mod = sugar_mod + 10,
                            tobacco_mod = tobacco_mod + 10,
                            fruits_mod = fruits_mod + 10 
                            WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Cash Crops':
                await conn.execute('''UPDATE cnc_modifiers SET
                            grain_mod = grain_mod + 10,
                            wine_mod = wine_mod + 10,
                            tea_and_coffee_mod = tea_and_coffee_mod + 10,
                            sugar_mod = sugar_mod + 10,
                            tobacco_mod = tobacco_mod + 10,
                            fruits_mod = fruits_mod + 10
                            WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Early Industrial Farming':
                await conn.execute('''UPDATE cnc_modifiers SET
                            grain_mod = grain_mod + 10,
                            wine_mod = wine_mod + 10,
                            tea_and_coffee_mod = tea_and_coffee_mod + 10,
                            sugar_mod = sugar_mod + 10,
                            tobacco_mod = tobacco_mod + 10,
                            fruits_mod = fruits_mod +1,
                            wool_mod = wool_mod + 10,
                            fish_mod = fish_mod + 10,
                            fur_mod = fur_mod + 10,
                            grain_mod = grain_mod + 10,
                            livestock_mod = livestock_mod + 10
                            WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Basic Metalworking':
                await conn.execute('''UPDATE cnc_modifiers SET army_limit = army_limit + 20000 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Trained Soldiers':
                await conn.execute('''UPDATE cnc_modifiers SET attack_level = attack_level + 1 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Horsemanship':
                await conn.execute('''UPDATE cnc_modifiers SET movement_cost_mod = movement_cost_mod - 0.25 
                WHERE user_id = $1''', userinfo['user_id'])
            if t == 'Archery':
                await conn.execute('''UPDATE cnc_modifiers SET attack_level = attack_level + 1 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Iron Metalworking':
                await conn.execute('''UPDATE cnc_modifiers SET army_limit = army_limit + 50000 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Early Armor':
                await conn.execute('''UPDATE cnc_modifiers SET defense_level = defense_level + 1 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Comitati':
                await conn.execute('''UPDATE cnc_modifiers SET defense_level = defense_level + 1 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Retinues':
                await conn.execute('''UPDATE cnc_modifiers SET attack_level = attack_level + 1 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Professional Soldiers':
                await conn.execute('''UPDATE cnc_modifiers SET attack_level = attack_level + 1 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Military Strategy':
                await conn.execute('''UPDATE cnc_modifiers SET attack_level = attack_level + 1 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Steel Metalworking':
                await conn.execute('''UPDATE cnc_modifiers SET army_limit = army_limit + 50000 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Plate Armor':
                await conn.execute('''UPDATE cnc_modifiers SET defense_level = defense_level + 1 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Chivalry':
                await conn.execute('''UPDATE cnc_modifiers SET attack_level = attack_level + 1 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Demi-Lancer':
                await conn.execute('''UPDATE cnc_modifiers SET movement_cost_mod = movement_cost_mod - 0.25, 
                                    army_limit = army_limit + 50000 WHERE user_id = $1''', userinfo['user_id'])
            if t == 'Gendarmes':
                await conn.execute('''UPDATE cnc_modifiers SET attack_level = attack_level + 10, 
                defense_level = defense_level + 1 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Gunpowder':
                await conn.execute('''UPDATE cnc_modifiers SET attack_level = attack_level + 1 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Gothic Plate':
                await conn.execute('''UPDATE cnc_modifiers SET defense_level = defense_level + 1 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Cuirass':
                await conn.execute('''UPDATE cnc_modifiers SET movement_cost_mod = movement_cost_mod - 0.25, 
                                               army_limit = army_limit + 25000 WHERE user_id = $1''', userinfo['user_id'])
            if t == 'Levee En Masse':
                await conn.execute('''UPDATE cnc_modifiers SET army_limit = army_limit + 100000 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Munitions Armor':
                await conn.execute('''UPDATE cnc_modifiers SET army_limit = army_limit + 50000 WHERE user_id = $1;''',
                                   userinfo['user_id'])
            if t == 'Light Infantry':
                await conn.execute('''UPDATE cnc_modifiers SET movement_cost_mod = movement_cost_mod - 0.25 
                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Writing':
                await conn.execute('''UPDATE cnc_modifiers SET research_mod = research_mod - 0.05
                WHERE user_id = $1;''', userinfo['user_id'])
                await conn.execute('''UPDATE cnc_modifiers SET research_mod = ROUND(research_mod::numeric, 2)
                                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Mathematics':
                await conn.execute('''UPDATE cnc_modifiers SET research_mod = research_mod - 0.05
                                WHERE user_id = $1;''', userinfo['user_id'])
                await conn.execute('''UPDATE cnc_modifiers SET research_mod = ROUND(research_mod::numeric, 2)
                                                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Literacy':
                await conn.execute('''UPDATE cnc_modifiers SET research_mod = research_mod - 0.05
                                WHERE user_id = $1;''', userinfo['user_id'])
                await conn.execute('''UPDATE cnc_modifiers SET research_mod = ROUND(research_mod::numeric, 2)
                                                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Education':
                await conn.execute('''UPDATE cnc_modifiers SET research_mod = research_mod - 0.05
                                WHERE user_id = $1;''', userinfo['user_id'])
                await conn.execute('''UPDATE cnc_modifiers SET research_mod = ROUND(research_mod::numeric, 2)
                                                WHERE user_id = $1;''', userinfo['user_id'])
            if t == 'Chemistry':
                await conn.execute('''UPDATE cnc_modifiers SET research_mod = research_mod - 0.05
                                WHERE user_id = $1;''', userinfo['user_id'])
                await conn.execute('''UPDATE cnc_modifiers SET research_mod = ROUND(research_mod::numeric, 2)
                                                WHERE user_id = $1;''', userinfo['user_id'])

    async def lookup(self):
        conn = self.pool
        techinfo = await conn.fetchrow('''SELECT * FROM cnc_tech WHERE lower(name) = $1;''', self.tech.lower())
        if techinfo is None:
            await self.ctx.send("No such technology exists.")
            return
        techembed = discord.Embed(color=discord.Color.dark_red(), title=str(techinfo['name']))
        techembed.set_thumbnail(url=str(techinfo['image']))
        techembed.add_field(name='Field', value=str(techinfo['field']))
        techembed.add_field(name='Prerequisites', value=str(techinfo['prerequisites']))
        techembed.add_field(name='Effect', value=str(techinfo['effect']))
        techembed.add_field(name='Description', value=str(techinfo['description']), inline=False)
        if techinfo['exclusive'] is not None:
            techembed.add_field(name='Mutually Exclusive Tech', value=str(techinfo['exclusive']))
        await self.ctx.send(embed=techembed)

    async def tree(self):
        conn = self.pool
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1;''', self.nation)
        loading = await self.ctx.send("Loading...")
        async with self.ctx.typing():
            tree = Image.open(fr"/root/Documents/Shard/CNC/Tech Tree/Cnc Tech Tree Lines.png").convert("RGBA")
            units = Image.open(fr"/root/Documents/Shard/CNC/Tech Tree/CnC Tech Tree Units.png").convert("RGBA")
            for t in userinfo['researched']:
                techinfo = await conn.fetchrow('''SELECT * FROM cnc_tech WHERE name = $1;''', t)
                tech_unit = Image.open(fr"/root/Documents/Shard/CNC/Tech Tree/{techinfo['name']}.png")
                unit_cord = techinfo['cords']
                width = tech_unit.size[0]
                height = tech_unit.size[1]
                cords = (int(unit_cord[0]), int(unit_cord[1]))
                color = ImageColor.getrgb(userinfo['usercolor'])
                for x in range(0, width):
                    for y in range(0, height):
                        data = tech_unit.getpixel((x, y))
                        if data != (0, 0, 0, 0):
                            tech_unit.putpixel((x, y), color)
                tech_unit = tech_unit.convert("RGBA")
                units.paste(tech_unit, box=cords, mask=tech_unit)
            tree = tree.convert("RGBA")
            units.paste(tree, mask=tree)
            units.save(fr"/root/Documents/Shard/CNC/Tech Tree/CnC Tech Tree Colored.png")
            with open(fr"/root/Documents/Shard/CNC/Tech Tree/CnC Tech Tree Colored.png", "rb") as preimg:
                img = b64encode(preimg.read())
            params = {"key": "a64d9505a13854ff660980db67ee3596",
                      "image": img,
                      "name": f"{userinfo['username']} Tech Tree"}
            time.sleep(1)
            upload = await self.ctx.bot.loop.run_in_executor(None, requests.post, "https://api.imgbb.com/1/upload",
                                                params)
            response = upload.json()
            await loading.edit(content=response["data"]["url"])
            return
