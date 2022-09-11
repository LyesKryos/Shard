import random

import discord
from discord.ext import commands
import asyncpg
import traceback
import re


class Events:

    def __init__(self, ctx: commands.Context, nation: str = None, event: str = None, current: bool = False):
        # define nation, context, and event
        self.nation = nation
        self.ctx = ctx
        self.event = event
        self.current = current
        self.random_good = None
        # creates connection pool
        try:
            self.pool: asyncpg.pool = ctx.bot.pool
        except Exception:
            ctx.bot.logger.warning(traceback.format_exc())

    def space_replace(self, userinput: str) -> str:
        """Replaces spaces with underscores and titles"""
        to_regex = userinput.replace(" ", "_").lower()
        return re.sub(r"[^a-zA-Z0-9_-]", ' ', to_regex)

    def underscore_replace(self, userinput: str) -> str:
        """Replaces underscores with spaces and lowers the text"""
        to_regex = userinput.replace("_", " ").title()
        return re.sub(r"[^a-zA-Z0-9_-]", ' ', to_regex)

    async def event_info(self):
        # establish connection pool
        conn = self.pool
        # fetch user information
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', self.ctx.author.id)
        # if the user is not registered
        if userinfo is None:
            await self.ctx.send("You are not registered.")
            return
        # if the user requests information about their current event
        if self.event is None:
            # if no event is in effect
            if userinfo['event'] == '':
                await self.ctx.send(f"No current event is effecting {userinfo['username']}.")
                return
            # fetch event info
            event_info = await conn.fetchrow('''SELECT * FROM cnc_events WHERE name = $1;''',
                                             userinfo['event'])
            # construct embed and send
            event_embed = discord.Embed(title=userinfo['event'],
                                        description=f"The current event affecting {userinfo['username']}.")
            event_embed.add_field(name="Effect", value=f"{event_info['effects']}", inline=False)
            event_embed.add_field(name="Type", value=f"{event_info['type'].title()}")
            event_embed.add_field(name="Duration", value=f"{event_info['duration']} turns")
            event_embed.add_field(name="Weight", value=f"{event_info['weight']}")
            await self.ctx.send(embed=event_embed)
            return
        else:
            # fetch event info
            event_info = await conn.fetchrow('''SELECT * FROM cnc_events WHERE name = $1;''',
                                             self.space_replace(self.event))
            # construct embed and send
            event_embed = discord.Embed(title=event_info['name'],
                                        description=f"The current event affecting {userinfo['username']}.")
            event_embed.add_field(name="Effect", value=f"{event_info['effects']}")
            event_embed.add_field(name="\u200b", value="\u200b")
            event_embed.add_field(name="Weight", value=f"{event_info['weight']}")
            event_embed.add_field(name="Description", value=f"{event_info['description']}")
            await self.ctx.send(embed=event_embed)
            return

    async def event_effects(self):
        try:
            # establish connection pool
            conn = self.pool
            # fetch user info
            userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE lower(username) = $1;''',
                                           self.nation.lower())
            user_id = userinfo['user_id']
            # count provinces
            provinces = await conn.fetchrow(
                '''SELECT count(*) FROM provinces WHERE occupier_id = $1 and owner_id = $1;''',
                user_id)
            province_count = provinces['count']
            # fetch event_info
            event_info = await conn.fetchrow('''SELECT * FROM cnc_events WHERE name = $1;''', self.event)
            # execute effects; if the event is weighted less than 100, roll d100
            event = self.space_replace(self.event)
            user = self.ctx.bot.get_user(user_id)
            # if the event is bountiful_harvest
            if event == "bountiful_harvest":
                if self.current:
                    await conn.execute(
                        '''UPDATE cnc_modifiers SET manpower_mod = manpower_mod + 0.5 WHERE user_id = $1;''',
                        user_id)
                else:
                    # if the manpower is between 70-80%, increase the mod by .5
                    if (.7 * userinfo['maxmanpower']) < userinfo['manpower'] < (.8 * userinfo['maxmanpower']):
                        await conn.execute(
                            '''UPDATE cnc_modifiers SET manpower_mod = manpower_mod + 0.5 WHERE user_id = $1;''',
                            user_id)
                        await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 
                                                WHERE user_id = $3;''', event_info['name'], event_info['duration'],
                                           user_id)
                        await user.send(
                            f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                            f" This event will last {event_info['duration']} turns.")
                return
            # if the event is scant_harvest
            if event == "scant_harvest":
                if self.current:
                    await conn.execute(
                        '''UPDATE cnc_modifiers SET manpower_mod = manpower_mod - 0.5 WHERE user_id = $1;''',
                        user_id)
                else:
                    # if the manpower is between 70-80%, increase the mod by .5
                    if (0 * userinfo['maxmanpower']) < userinfo['manpower'] < (.4 * userinfo['maxmanpower']):
                        await conn.execute(
                            '''UPDATE cnc_modifiers SET manpower_mod = manpower_mod - 0.5 WHERE user_id = $1;''',
                            user_id)
                        await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 
                                                WHERE user_id = $3;''', event_info['name'], event_info['duration'],
                                           user_id)
                        await user.send(
                            f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                            f" This event will last {event_info['duration']} turns.")
                return
            # if the event is population_boom
            if event == "population_boom":
                if self.current:
                    await conn.execute(
                        '''UPDATE cnc_modifiers SET manpower_mod = manpower_mod + 0.25 WHERE user_id = $1;''',
                        user_id)
                else:
                    # if the tax is less than 10%
                    if userinfo['taxation'] >= 10:
                        await conn.execute(
                            '''UPDATE cnc_modifiers SET manpower_mod = manpower_mod + 0.25 WHERE user_id = $1;''',
                            user_id)
                        await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 
                                                WHERE user_id = $3;''', event_info['name'], event_info['duration'],
                                           user_id)
                        await user.send(
                            f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                            f" This event will last {event_info['duration']} turns.")
                        return
            # if event is population_decline
            if event == "population_decline":
                if self.current:
                    await conn.execute(
                        '''UPDATE cnc_modifiers SET manpower_mod = manpower_mod - 0.25 WHERE user_id = $1;''',
                        user_id)
                    return
                # if the tax is greater than 20%
                if userinfo['taxation'] <= 20:
                    await conn.execute(
                        '''UPDATE cnc_modifiers SET manpower_mod = manpower_mod - 0.25 WHERE user_id = $1;''',
                        user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 
                                                                    WHERE user_id = $3;''', event_info['name'],
                                       event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                    return
            # if event is disease outbreak
            if event == "disease_outbreak":
                if self.current:
                    await conn.execute('''UPDATE cncusers SET manpower = manpower * 0.75 WHERE user_id = $1;''',
                                       user_id)
                    return
                # if the public_service is below 15%
                if userinfo['public_services'] <= 15:
                    await conn.execute('''UPDATE cncusers SET manpower = manpower * 0.75 WHERE user_id = $1;''',
                                       user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                    return
            # if event is trade_boom
            if event == "trade_boom":
                if self.current:
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
                    return
                # if there are more than 2 trade routes and the user is not at war
                trade_routes = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE 
                (recipient_id = $1 OR sender_id = $1) AND active = TRUE AND type = 'trade';''', user_id)
                wars = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE (recipient_id = $1 OR sender_id = $1) 
                AND active = TRUE AND type = 'war';''', user_id)
                if trade_routes['count'] >= 2 and wars['count'] == 0:
                    # increase all trade goods by +1
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
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                    return
            # if event is trade_decline
            if event == "trade_decline":
                if self.current:
                    await conn.execute('''UPDATE cnc_modifiers SET 
                                                        wool_mod = wool_mod - 10,
                                                        fish_mod = fish_mod - 10,
                                                        fur_mod = fur_mod - 10,
                                                        grain_mod = grain_mod - 10,
                                                        livestock_mod = livestock_mod - 10,
                                                        salt_mod = salt_mod - 10,
                                                        wine_mod = wine_mod - 10,
                                                        copper_mod = copper_mod - 10,
                                                        iron_mod = iron_mod - 10,
                                                        precious_goods_mod = precious_goods_mod - 10,
                                                        spices_mod = spices_mod - 10,
                                                        tea_and_coffee_mod = tea_and_coffee_mod - 10,
                                                        chocolate_mod = chocolate_mod - 10,
                                                        cotton_mod = cotton_mod - 10,
                                                        sugar_mod = sugar_mod - 10,
                                                        tobacco_mod = tobacco_mod - 10,
                                                        dyes_mod = dyes_mod - 10,
                                                        silk_mod = silk_mod - 10,
                                                        rare_wood_mod = rare_wood_mod - 10,
                                                        glass_mod = glass_mod - 10,
                                                        paper_mod = paper_mod - 10,
                                                        precious_stones_mod = precious_stones_mod - 10,
                                                        coal_mod = coal_mod - 10,
                                                        fruits_mod = fruits_mod - 10,
                                                        raw_stone_mod = raw_stone_mod - 10,
                                                        wood_mod = wood_mod - 10,
                                                        tin_mod = tin_mod - 10,
                                                        ivory_mod = ivory_mod - 10,
                                                        WHERE user_id = $1;''', userinfo['user_id'])
                    return
                # if there are more than 2 trade routes and the user is not at war
                trade_routes = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE 
                   (recipient_id = $1 OR sender_id = $1) AND active = TRUE AND type = 'trade';''', user_id)
                wars = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE (recipient_id = $1 OR sender_id = $1) 
                   AND active = TRUE AND type = 'war';''', user_id)
                if trade_routes['count'] >= 2 and wars['count'] == 0:
                    # decrease all trade goods by -1
                    await conn.execute('''UPDATE cnc_modifiers SET 
                                                        wool_mod = wool_mod - 10,
                                                        fish_mod = fish_mod - 10,
                                                        fur_mod = fur_mod - 10,
                                                        grain_mod = grain_mod - 10,
                                                        livestock_mod = livestock_mod - 10,
                                                        salt_mod = salt_mod - 10,
                                                        wine_mod = wine_mod - 10,
                                                        copper_mod = copper_mod - 10,
                                                        iron_mod = iron_mod - 10,
                                                        precious_goods_mod = precious_goods_mod - 10,
                                                        spices_mod = spices_mod - 10,
                                                        tea_and_coffee_mod = tea_and_coffee_mod - 10,
                                                        chocolate_mod = chocolate_mod - 10,
                                                        cotton_mod = cotton_mod - 10,
                                                        sugar_mod = sugar_mod - 10,
                                                        tobacco_mod = tobacco_mod - 10,
                                                        dyes_mod = dyes_mod - 10,
                                                        silk_mod = silk_mod - 10,
                                                        rare_wood_mod = rare_wood_mod - 10,
                                                        glass_mod = glass_mod - 10,
                                                        paper_mod = paper_mod - 10,
                                                        precious_stones_mod = precious_stones_mod - 10,
                                                        coal_mod = coal_mod - 10,
                                                        fruits_mod = fruits_mod - 10,
                                                        raw_stone_mod = raw_stone_mod - 10,
                                                        wood_mod = wood_mod - 10,
                                                        tin_mod = tin_mod - 10,
                                                        ivory_mod = ivory_mod - 10,
                                                        WHERE user_id = $1;''', userinfo['user_id'])
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is trade_route_closes
            if event == "trade_route_closes":
                # if there are more than 4 trade routes and the user is at war
                trade_routes = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE 
                      (recipient_id = $1 OR sender_id = $1) AND active = TRUE AND type = 'trade';''', user_id)
                wars = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE (recipient_id = $1 OR sender_id = $1) 
                      AND active = TRUE AND type = 'war';''', user_id)
                if trade_routes['count'] >= 4 and wars['count'] > 0:
                    # deactivate a random trade route
                    trade_route = await conn.fetchrow('''SELECT * FROM interactions WHERE 
                    (recipient_id = $1 OR sender_id = $1) AND active = TRUE AND type = 'trade' ORDER BY random()
                    ;''', user_id)
                    await conn.execute('''UPDATE cnc_modifiers SET active = FALSE WHERE id = $1;''',
                                       trade_route['id'])
                    if trade_route['recipient_id'] != user_id:
                        user_obj = self.ctx.bot.get_user(trade_route['recipient_id'])
                        await user_obj.send(f"{trade_route['recipient']}'s trade route with {self.nation} has been"
                                            f"closed due to an event.")
                    else:
                        user_obj = self.ctx.bot.get_user(trade_route['sender_id'])
                        await user_obj.send(f"{trade_route['sender']}'s trade route with {self.nation} has been"
                                            f"closed due to an event.")
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                    return
            # if event is military_reform
            if event == "military_reform":
                if self.current:
                    await conn.execute('''UPDATE cnc_modifiers SET attack_level = attack_level + 1, 
                    defense_level = defense_level + 1 WHERE user_id = $1;''', user_id)
                    return
                # if the military spending is above 20% and the nation is not at war
                wars = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE (recipient_id = $1 OR sender_id = $1) 
                   AND active = TRUE AND type = 'war';''', user_id)
                if userinfo['military_upkeep'] >= 20 and wars['count'] == 0:
                    await conn.execute('''UPDATE cnc_modifiers SET attack_level = attack_level + 1, 
                    defense_level = defense_level + 1 WHERE user_id = $1;''', user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is robber_bands
            if event == "robber_bands":
                if self.current:
                    await conn.execute('''UPDATE cnc_modifiers SET 
                                                        wool_mod = ROUND(wool_mod - 30),
                                                        fish_mod = ROUND(fish_mod - 30),
                                                        fur_mod = ROUND(fur_mod - 30),
                                                        grain_mod = ROUND(grain_mod - 30),
                                                        livestock_mod = ROUND(livestock_mod - 30),
                                                        salt_mod = ROUND(salt_mod - 30),
                                                        wine_mod = ROUND(wine_mod - 30),
                                                        copper_mod = ROUND(copper_mod - 30),
                                                        iron_mod = ROUND(iron_mod - 30),
                                                        precious_goods_mod = ROUND(precious_goods_mod - 30),
                                                        spices_mod = ROUND(spices_mod - 30),
                                                        tea_and_coffee_mod = ROUND(tea_and_coffee_mod - 30),
                                                        chocolate_mod = ROUND(chocolate_mod - 30),
                                                        cotton_mod = ROUND(cotton_mod - 30),
                                                        sugar_mod = ROUND(sugar_mod - 30),
                                                        tobacco_mod = ROUND(tobacco_mod - 30),
                                                        dyes_mod = ROUND(dyes_mod - 30),
                                                        silk_mod = ROUND(silk_mod - 30),
                                                        rare_wood_mod = ROUND(rare_wood_mod - 30),
                                                        glass_mod = ROUND(glass_mod - 30),
                                                        paper_mod = ROUND(paper_mod - 30),
                                                        precious_stones_mod = ROUND(precious_stones_mod - 30),
                                                        coal_mod = ROUND(coal_mod - 30),
                                                        fruits_mod = ROUND(fruits_mod - 30),
                                                        raw_stone_mod = ROUND(raw_stone_mod - 30),
                                                        wood_mod = ROUND(wood_mod - 30),
                                                        tin_mod = ROUND(tin_mod - 30),
                                                        ivory_mod = ROUND(ivory_mod - 30)
                                                        WHERE user_id = $1;''', userinfo['user_id'])
                    return
                # if there are more than 4 trade routes, decrease all trade goods by -3 value
                trade_routes = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE 
                   (recipient_id = $1 OR sender_id = $1) AND active = TRUE AND type = 'trade';''', user_id)
                if trade_routes['count'] >= 4:
                    await conn.execute('''UPDATE cnc_modifiers SET 
                                                        wool_mod = ROUND(wool_mod - 30),
                                                        fish_mod = ROUND(fish_mod - 30),
                                                        fur_mod = ROUND(fur_mod - 30),
                                                        grain_mod = ROUND(grain_mod - 30),
                                                        livestock_mod = ROUND(livestock_mod - 30),
                                                        salt_mod = ROUND(salt_mod - 30),
                                                        wine_mod = ROUND(wine_mod - 30),
                                                        copper_mod = ROUND(copper_mod - 30),
                                                        iron_mod = ROUND(iron_mod - 30),
                                                        precious_goods_mod = ROUND(precious_goods_mod - 30),
                                                        spices_mod = ROUND(spices_mod - 30),
                                                        tea_and_coffee_mod = ROUND(tea_and_coffee_mod - 30),
                                                        chocolate_mod = ROUND(chocolate_mod - 30),
                                                        cotton_mod = ROUND(cotton_mod - 30),
                                                        sugar_mod = ROUND(sugar_mod - 30),
                                                        tobacco_mod = ROUND(tobacco_mod - 30),
                                                        dyes_mod = ROUND(dyes_mod - 30),
                                                        silk_mod = ROUND(silk_mod - 30),
                                                        rare_wood_mod = ROUND(rare_wood_mod - 30),
                                                        glass_mod = ROUND(glass_mod - 30),
                                                        paper_mod = ROUND(paper_mod - 30),
                                                        precious_stones_mod = ROUND(precious_stones_mod - 30),
                                                        coal_mod = ROUND(coal_mod - 30),
                                                        fruits_mod = ROUND(fruits_mod - 30),
                                                        raw_stone_mod = ROUND(raw_stone_mod - 30),
                                                        wood_mod = ROUND(wood_mod - 30),
                                                        tin_mod = ROUND(tin_mod - 30),
                                                        ivory_mod = ROUND(ivory_mod - 30)
                                                        WHERE user_id = $1;''', userinfo['user_id'])
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is privateers
            if event == "privateers":
                if self.current:
                    await conn.execute('''UPDATE cnc_modifiers SET 
                                                        wool_mod = wool_mod + 20,
                                                        fish_mod = fish_mod + 20,
                                                        fur_mod = fur_mod + 20,
                                                        grain_mod = grain_mod + 20,
                                                        livestock_mod = livestock_mod + 20,
                                                        salt_mod = salt_mod + 20,
                                                        wine_mod = wine_mod + 20,
                                                        copper_mod = copper_mod + 20,
                                                        iron_mod = iron_mod + 20,
                                                        precious_goods_mod = precious_goods_mod + 20,
                                                        spices_mod = spices_mod + 20,
                                                        tea_and_coffee_mod = tea_and_coffee_mod + 20,
                                                        chocolate_mod = chocolate_mod + 20,
                                                        cotton_mod = cotton_mod + 20,
                                                        sugar_mod = sugar_mod + 20,
                                                        tobacco_mod = tobacco_mod + 20,
                                                        dyes_mod = dyes_mod + 20,
                                                        silk_mod = silk_mod + 20,
                                                        rare_wood_mod = rare_wood_mod + 20,
                                                        glass_mod = glass_mod + 20,
                                                        paper_mod = paper_mod + 20,
                                                        precious_stones_mod = precious_stones_mod + 20,
                                                        coal_mod = coal_mod + 20,
                                                        fruits_mod = fruits_mod + 20,
                                                        raw_stone_mod = raw_stone_mod + 20,
                                                        wood_mod = wood_mod + 20,
                                                        tin_mod = tin_mod + 20,
                                                        ivory_mod = ivory_mod + 20
                                                        WHERE user_id = $1;''', user_id)
                    return
                # if there are more than 2 trade routes, at war, and have the tech, increase all trade goods by +2 value
                trade_routes = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE 
                   (recipient_id = $1 OR sender_id = $1) AND active = TRUE AND type = 'trade';''', user_id)
                wars = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE (recipient_id = $1 OR sender_id = $1) 
                   AND active = TRUE AND type = 'war';''', user_id)
                if "Privateers" in userinfo['researched'] and trade_routes['count'] >= 2 and wars['count'] > 0:
                    await conn.execute('''UPDATE cnc_modifiers SET 
                                                        wool_mod = wool_mod + 20,
                                                        fish_mod = fish_mod + 20,
                                                        fur_mod = fur_mod + 20,
                                                        grain_mod = grain_mod + 20,
                                                        livestock_mod = livestock_mod + 20,
                                                        salt_mod = salt_mod + 20,
                                                        wine_mod = wine_mod + 20,
                                                        copper_mod = copper_mod + 20,
                                                        iron_mod = iron_mod + 20,
                                                        precious_goods_mod = precious_goods_mod + 20,
                                                        spices_mod = spices_mod + 20,
                                                        tea_and_coffee_mod = tea_and_coffee_mod + 20,
                                                        chocolate_mod = chocolate_mod + 20,
                                                        cotton_mod = cotton_mod + 20,
                                                        sugar_mod = sugar_mod + 20,
                                                        tobacco_mod = tobacco_mod + 20,
                                                        dyes_mod = dyes_mod + 20,
                                                        silk_mod = silk_mod + 20,
                                                        rare_wood_mod = rare_wood_mod + 20,
                                                        glass_mod = glass_mod + 20,
                                                        paper_mod = paper_mod + 20,
                                                        precious_stones_mod = precious_stones_mod + 20,
                                                        coal_mod = coal_mod + 20,
                                                        fruits_mod = fruits_mod + 20,
                                                        raw_stone_mod = raw_stone_mod + 20,
                                                        wood_mod = wood_mod + 20,
                                                        tin_mod = tin_mod + 20,
                                                        ivory_mod = ivory_mod + 20
                                                        WHERE user_id = $1;''', user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is military_mutiny
            if event == "military_mutiny":
                if self.current:
                    await conn.execute('''UPDATE cnc_modifiers SET troop_upkeep_mod = troop_upkeep_mod + .25
                    WHERE user_id = $1;''', user_id)
                    return
                # if the military spending is less than 5%, add 25% to upkeep cost
                if userinfo['military_upkeep'] <= 5:
                    await conn.execute('''UPDATE cnc_modifiers SET troop_upkeep_mod = troop_upkeep_mod + .25
                    WHERE user_id = $1;''', user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is allied_military_coordination
            if event == "allied_military_coordination":
                if self.current:
                    await conn.execute('''UPDATE cnc_modifiers SET troop_upkeep_mod = troop_upkeep_mod - .15
                    WHERE user_id = $1;''', user_id)
                    return
                # if the military spending is more than 20% and the nation has an ally
                alliances = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE 
                   (recipient_id = $1 OR sender_id = $1) AND active = TRUE AND type = 'alliance';''', user_id)
                if userinfo['military_upkeep'] >= 20 and alliances['count'] > 0:
                    await conn.execute('''UPDATE cnc_modifiers SET troop_upkeep_mod = troop_upkeep_mod - .15
                    WHERE user_id = $1;''', user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is enemy_military_espionage
            if event == "enemy_military_espionage":
                if self.current:
                    await conn.execute('''UPDATE cnc_modifiers SET troop_upkeep_mod = troop_upkeep_mod + .15
                        WHERE user_id = $1;''', user_id)
                    return
                # if the military spending is less than 5% and the nation is at war
                wars = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE (recipient_id = $1 OR sender_id = $1) 
                   AND active = TRUE AND type = 'war';''', user_id)
                if userinfo['military_upkeep'] <= 5 and wars['count'] > 0:
                    await conn.execute('''UPDATE cnc_modifiers SET troop_upkeep_mod = troop_upkeep_mod + .15
                        WHERE user_id = $1;''', user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is national_scandal
            if event == "national_scandal":
                if self.current:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest + 10 WHERE user_id = $1;''', user_id)
                    return
                # if the user has more than 15 provinces, add 10 national unrest
                if province_count >= 15:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest + 10 WHERE user_id = $1;''', user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is government_scandal
            if event == "government_scandal":
                if self.current:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest + 20 WHERE user_id = $1;''', user_id)
                    return
                # if the user has more than 50 provinces and owns a capital, add 20 national unrest
                if province_count >= 50 and userinfo['capital'] != 0:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest + 20 WHERE user_id = $1;''',
                        user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is international_scandal
            if event == "international_scandal":
                # if the user has more than 70 provinces, a capital, and an alliance, end a random alliance and +40 unrest
                alliances = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE 
                   (recipient_id = $1 OR sender_id = $1) AND active = TRUE AND type = 'alliance';''', user_id)
                if province_count >= 70 and alliances['count'] > 0 and userinfo['capital'] != 0:
                    alliance = await conn.fetchrow('''SELECT * FROM interactions WHERE 
                    (recipient_id = $1 OR sender_id = $1) AND active = TRUE AND type = 'alliance' ORDER BY random();''',
                                                   user_id)
                    await conn.execute('''UPDATE interactions SET active = FALSE WHERE id = $1;''', alliance['id'])
                    if alliance['recipient_id'] != user_id:
                        user_obj = self.ctx.bot.get_user(alliance['recipient_id'])
                        await user_obj.send(f"{alliance['recipient']}'s trade route with {self.nation} has been"
                                            f"closed due to an event.")
                    else:
                        user_obj = self.ctx.bot.get_user(alliance['sender_id'])
                        await user_obj.send(f"{alliance['sender']}'s trade route with {self.nation} has been"
                                            f"closed due to an event.")
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                    return
            # if event is social_reform
            if event == "social_reform":
                if self.current:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest - 100 WHERE user_id = $1;''', user_id)
                    return
                # if the user owns more than 15 provinces and the national unrest is above 60
                if province_count >= 15 and userinfo['national_unrest'] >= 60:
                    # reduce national unrest by 10
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest - 100 WHERE user_id = $1;''',
                        user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is patriotic_parade
            if event == "patriotic_parade":
                if self.current:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest - 10 WHERE user_id = $1;''', user_id)
                    await conn.execute('''UPDATE cnc_modifiers SET troop_upkeep_mod = troop_upkeep_mod - .1 
                    WHERE user_id = $1;''', user_id)
                    return
                # if the national unrest is higher than 60 and there is a war
                wars = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE (recipient_id = $1 OR sender_id = $1) 
                   AND active = TRUE AND type = 'war';''', user_id)
                wars = wars['count']
                if userinfo['national_unrest'] <= 60 and wars > 0:
                    # decrease national unrest by 10 and troop upkeep by 10%
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest - 10 WHERE user_id = $1;''',
                        user_id)
                    await conn.execute('''UPDATE cnc_modifiers SET troop_upkeep_mod = troop_upkeep_mod - .1 
                    WHERE user_id = $1;''', user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is heroic_battle
            if event == "heroic_battle":
                if self.current:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest - 15 WHERE user_id = $1;''', user_id)
                    await conn.execute('''UPDATE cnc_modifiers SET troop_upkeep_mod = troop_upkeep_mod - .05
                    WHERE user_id = $1;''', user_id)
                    return
                # if the national unrest is higher than 60 and there is a war
                wars = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE (recipient_id = $1 OR sender_id = $1) 
                   AND active = TRUE AND type = 'war';''', user_id)
                wars = wars['count']
                if userinfo['national_unrest'] <= 60 and wars > 0:
                    # decrease national unrest by 10 and troop upkeep by 10%
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest - 15 WHERE user_id = $1;''',
                        user_id)
                    await conn.execute('''UPDATE cnc_modifiers SET troop_upkeep_mod = troop_upkeep_mod - .05
                    WHERE user_id = $1;''', user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is disastrous_battle
            if event == "disastrous_battle":
                if self.current:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest + 10 WHERE user_id = $1;''', user_id)
                    return
                # if the national unrest is higher than 60 and there is a war
                wars = await conn.fetchrow('''SELECT count(*) FROM interactions WHERE (recipient_id = $1 OR sender_id = $1) 
                   AND active = TRUE AND type = 'war';''', user_id)
                wars = wars['count']
                if userinfo['national_unrest'] <= 60 and wars > 0:
                    # decrease national unrest by 10 and troop upkeep by 10%
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest + 10 WHERE user_id = $1;''',
                        user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is religious_festival
            if event == "religious_festival":
                # weight of 75
                roll = random.randint(1, 100)
                if self.current:
                    await conn.execute('''UPDATE cncusers SET national_unrest = national_unrest - 25 
                    WHERE user_id = $1;''', user_id)
                    return
                if roll >= 25:
                    # if the user has a national unrest of 60 or less, more than 15 provinces, and the religion tech
                    if userinfo['national_unrest'] <= 60 and province_count >= 15 and "Religion" in userinfo[
                        'researched']:
                        # decrease the national unrest by 25
                        await conn.execute('''UPDATE cncusers SET national_unrest = national_unrest - 25 
                        WHERE user_id = $1;''', user_id)
                        await conn.execute(
                            '''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                            event_info['name'], event_info['duration'], user_id)
                        await user.send(
                            f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                            f" This event will last {event_info['duration']} turns.")
                return
            # if event is religious_scandal
            if event == "religious_scandal":
                # weight of 75
                roll = random.randint(1, 100)
                if self.current:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest + 25 WHERE user_id = $1;''', user_id)
                    return
                if roll >= 25:
                    # if the user has a national unrest of 60 or less, more than 15 provinces, and the religion tech
                    if userinfo['national_unrest'] <= 60 and province_count >= 15 and "Religion" in userinfo[
                        'researched']:
                        # increase the national unrest by 25
                        await conn.execute(
                            '''UPDATE cncusers SET national_unrest = national_unrest + 25 WHERE user_id = $1;''',
                            user_id)
                        await conn.execute(
                            '''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                            event_info['name'], event_info['duration'], user_id)
                        await user.send(
                            f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                            f" This event will last {event_info['duration']} turns.")
                return
            # if event is religious_miracle
            if event == "religious_miracle":
                # weight of 25
                roll = random.randint(1, 100)
                if self.current:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest - 50 WHERE user_id = $1;''',
                        user_id)
                    return
                if roll >= 75:
                    # if the user has a national unrest of 60 or less, more than 30 provinces, and the religion tech
                    if userinfo['national_unrest'] <= 60 and province_count >= 30 and "Religion" in userinfo[
                        'researched']:
                        # decrease the national unrest by 50
                        await conn.execute(
                            '''UPDATE cncusers SET national_unrest = national_unrest - 50 WHERE user_id = $1;''',
                            user_id)
                        await conn.execute(
                            '''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                            event_info['name'], event_info['duration'], user_id)
                        await user.send(
                            f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                            f" This event will last {event_info['duration']} turns.")
                    return
            # if event is religious_disaster
            if event == "religious_disaster":
                # weight of 25
                roll = random.randint(1, 100)
                if self.current:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest + 50 WHERE user_id = $1;''',
                        user_id)
                    return
                if roll >= 75:
                    # if the user has a national unrest of 60 or less, more than 30 provinces, and the religion tech
                    if userinfo['national_unrest'] <= 60 and province_count >= 30 and "Religion" in userinfo[
                        'researched']:
                        # increase the national unrest by 50
                        await conn.execute(
                            '''UPDATE cncusers SET national_unrest = national_unrest + 50 WHERE user_id = $1;''',
                            user_id)
                        await conn.execute(
                            '''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                            event_info['name'], event_info['duration'], user_id)
                        await user.send(
                            f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                            f" This event will last {event_info['duration']} turns.")
                    return
            # if event is corruption
            if event == "corruption":
                if self.current:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest + 20 WHERE user_id = $1;''', user_id)
                    return
                # if the taxation is above 20%, increase national unrest by 20
                if userinfo['taxation'] >= 20:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest + 20 WHERE user_id = $1;''',
                        user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is royal_death
            if event == "royal_death":
                if self.current:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest + 20 WHERE user_id = $1;''',
                        user_id)
                    return
                # if the national unrest is less than 60 and there are more than 40 provinces, add 20 national unrest
                if userinfo['national_unrest'] <= 60 and province_count >= 40:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest + 20 WHERE user_id = $1;''',
                        user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                    return
            # if event is royal_birth
            if event == "royal_birth":
                if self.current:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest - 20 WHERE user_id = $1;''',
                        user_id)
                    return
                # if the national unrest is less than 60 and there are more than 40 provinces, subtract 20 national unrest
                if userinfo['national_unrest'] <= 60 and province_count >= 40:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest - 20 WHERE user_id = $1;''',
                        user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                    return
            # if event is pleased_nobles
            if event == "pleased_nobles":
                if self.current:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest - 10 WHERE user_id = $1;''',
                        user_id)
                    return
                # if the regional administration tech is researched, subtract 10 national unrest
                if "Regional Administration" in userinfo['researched']:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest - 10 WHERE user_id = $1;''',
                        user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                    return
            # if event is unhappy_nobles
            if event == "unhappy_nobles":
                # if the regional administration tech is researched, add 10 national unrest
                if "Regional Administration" in userinfo['researched']:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest + 10 WHERE user_id = $1;''',
                        user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                    return
            # if event is noble_endorsement
            if event == "noble_endorsement":
                if self.current:
                    await conn.execute('''UPDATE cnc_modifiers SET tax_mod = tax_mod + 0.15 WHERE user_id = $1;''',
                                       user_id)
                    return
                # if the regional administration tech is researched, add 15% tax efficiency
                if "Regional Administration" in userinfo['researched']:
                    await conn.execute('''UPDATE cnc_modifiers SET tax_mod = tax_mod + 0.15 WHERE user_id = $1;''',
                                       user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                    return
            # if event is religious_endorsement
            if event == "religious_endorsement":
                if self.current:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest - 105 WHERE user_id = $1;''',
                        user_id)
                    return
                # if the religion tech is researched, decrease national unrest by 15
                if "Religion" in userinfo['researched']:
                    await conn.execute(
                        '''UPDATE cncusers SET national_unrest = national_unrest - 105 WHERE user_id = $1;''',
                        user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                    return
            # if event is renowned_scientist_arrives
            if event == "renowned_scientist_arrives":
                if self.current:
                    await conn.execute('''UPDATE cnc_researching SET turn = turn - 1 WHERE user_id = $1;''', user_id)
                    return
                # if the education technology is researched, reduce the current researching tech turn by an extra 1
                if "Education" in userinfo['researched']:
                    await conn.execute('''UPDATE cnc_researching SET turn = turn - 1 WHERE user_id = $1;''', user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is wealthy_merchant_arrives
            if event == "wealthy_merchant_arrives":
                if self.current:
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
                                            WHERE user_id = $1;''', user_id)
                    return
                # if the merchants tech is researched, add
                if "Merchants" in userinfo['researched']:
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
                                            WHERE user_id = $1;''', user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                    return
            # if event is powerful_general_arrives
            if event == "powerful_general_arrives":
                if self.current:
                    await conn.execute('''UPDATE cnc_modifiers SET troop_upkeep_mod = troop_upkeep_mod - .25 
                    WHERE user_id = $1;''', user_id)
                    return
                # if the military strategy tech is researched, decrease troop upkeep by 25%
                if "Military Strategy" in userinfo['researched']:
                    await conn.execute('''UPDATE cnc_modifiers SET troop_upkeep_mod = troop_upkeep_mod - .25 
                    WHERE user_id = $1;''', user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is submissive_serfs
            if event == "submissive_serfs":
                if self.current:
                    await conn.execute('''UPDATE cnc_modifiers SET workshop_production_mod = workshop_production_mod + 0.5
                    WHERE user_id = $1;''', user_id)
                    return
                # if the workshops tech is researched, add 0.5 workshops production
                if "Workshops" in userinfo['researched']:
                    await conn.execute('''UPDATE cnc_modifiers SET workshop_production_mod = workshop_production_mod + 0.5
                    WHERE user_id = $1;''', user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is worker_strike
            if event == "worker_strike":
                if self.current:
                    await conn.execute('''UPDATE cnc_modifiers SET workshop_production_mod = workshop_production_mod - 0.5
                    WHERE user_id = $1;''', user_id)
                    return
                # if the workshops tech is researched, subtract 0.5 workshops production
                if "Workshops" in userinfo['researched']:
                    await conn.execute('''UPDATE cnc_modifiers SET workshop_production_mod = workshop_production_mod - 0.5
                    WHERE user_id = $1;''', user_id)
                    await conn.execute('''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                                       event_info['name'], event_info['duration'], user_id)
                    await user.send(
                        f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                        f" This event will last {event_info['duration']} turns.")
                return
            # if event is newly_minted_coins
            if event == "newly_minted_coins":
                # weighed 50
                roll = random.randint(1, 100)
                if self.current:
                    await conn.execute('''UPDATE cnc_modifiers SET gold_mod = gold_mod + 5, silver_mod = silver_mod + 5
                    WHERE user_id = $1;''', user_id)
                    return
                if roll >= 50:
                    # if the banking and investments tech has been researched, add 5 to the gold/silver market value
                    if "Banking and Investments" in userinfo['researched']:
                        await conn.execute('''UPDATE cnc_modifiers SET gold_mod = gold_mod + 5, silver_mod = silver_mod + 5
                        WHERE user_id = $1;''', user_id)
                        await conn.execute(
                            '''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                            event_info['name'], event_info['duration'], user_id)
                        await user.send(
                            f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                            f" This event will last {event_info['duration']} turns.")
                return
            # if event is counterfeit_coinage
            if event == "counterfeit_coinage":
                # weighed 50
                roll = random.randint(1, 100)
                if self.current:
                    await conn.execute('''UPDATE cnc_modifiers SET gold_mod = gold_mod - 5, silver_mod = silver_mod - 5
                                WHERE user_id = $1;''', user_id)
                    return
                if roll >= 50:
                    # if the banking and investments tech has been researched, subtract 5 from the gold/silver market value
                    if "Banking and Investments" in userinfo['researched']:
                        await conn.execute('''UPDATE cnc_modifiers SET gold_mod = gold_mod - 5, silver_mod = silver_mod - 5
                                    WHERE user_id = $1;''', user_id)
                        await conn.execute(
                            '''UPDATE cncusers SET event = $1, event_duration = $2 WHERE user_id = $3;''',
                            event_info['name'], event_info['duration'], user_id)
                        await user.send(
                            f"The event {self.underscore_replace(event)} has happened to {userinfo['username']}."
                            f" This event will last {event_info['duration']} turns.")
                return
        except Exception:
            self.ctx.bot.logger.warning(traceback.format_exc())

    async def global_effects(self):
        # establish connection pool
        conn = self.pool
        # execute effects; if the event is weighted less than 100, roll d100
        event = self.space_replace(self.event)
        # event channel
        event_channel = self.ctx.bot.get_channel(835579413625569322)
        # turns
        turn = await conn.fetchrow('''SELECT * FROM cnc_data WHERE data_name = 'turn';''')
        turn = turn['data_value']
        # if event is famine
        if event == "famine":
            # weighted 75
            roll = random.randint(1, 100)
            if self.current:
                await conn.execute('''UPDATE cnc_modifiers SET manpower_mod = mandpower_mod - .25;''')
                return
            if roll >= 25:
                # if the turn is 56 or later, reduce manpower gain by 25%
                if turn >= 56:
                    await conn.execute('''UPDATE cnc_modifiers SET manpower_mod = mandpower_mod - .25;''')
                    await event_channel.send("A great **Famine** has struck the world! Global manpower increase is "
                                             "reduced by 25%.")
                return
        # if event is plague
        if event == "plague":
            # weighted 25
            roll = random.randint(1, 100)
            if self.current:
                await conn.execute('''UPDATE cnc_modifiers SET manpower_mod = mandpower_mod - .25;''')
                return
            if roll >= 75:
                # if the turn is 112 or later, reduce manpower gain by 25%
                if turn >= 112:
                    await conn.execute('''UPDATE cnc_modifiers SET manpower_mod = mandpower_mod - .25;''')
                    await event_channel.send("A great **Plague** has struck the world! Global manpower increase is "
                                             "reduced by 75%.")
                return
        # if event is organized_peasant_uprising
        if event == "organized_peasant_uprising":
            # weighted 50
            roll = random.randint(1, 100)
            if self.current:
                await conn.execute('''UPDATE cncusers SET national_unrest = national_unrest + 15;''')
                return
            if roll >= 50:
                # if the turn is 28 or later, increase national unrest by 15
                if turn >= 28:
                    await conn.execute('''UPDATE cncusers SET national_unrest = national_unrest + 15;''')
                    await event_channel.send("The peasants of the world have organized and have begun an **Uprising**!"
                                             " National unrest for all nations is increased by 15.")
                return
        # if event is calm_and_mild_spring
        if event == "calm_and_mild_spring":
            # weighted 80
            roll = random.randint(1, 100)
            if self.current:
                await conn.execute('''UPDATE cncusers SET national_unrest = national_unrest - 105;''')
                await conn.execute('''UPDATE cnc_modifiers SET manpower_mod = manpower_mod + .05;''')
                return
            if roll >= 20:
                # if the turn is 8 or later, increase manpower by 5% and national unrest by 15
                if turn >= 8:
                    await conn.execute('''UPDATE cncusers SET national_unrest = national_unrest - 105;''')
                    await conn.execute('''UPDATE cnc_modifiers SET manpower_mod = manpower_mod + .05;''')
                    await event_channel.send("Spring has arrived! It is **Calm and Mild**, giving all nations 5% more"
                                             "manpower and 15 less national unrest.")
                return
        # if event is bountiful_autumn
        if event == "bountiful_autumn":
            # weighted 80
            roll = random.randint(1, 100)
            if self.current:
                await conn.execute('''UPDATE cnc_modifiers SET manpower_mod = manpower_mod + .25;''')
                return
            if roll >= 20:
                # if the turn is 8 or later, increase manpower gain by 25%
                if turn >= 8:
                    await conn.execute('''UPDATE cnc_modifiers SET manpower_mod = manpower_mod + .25;''')
                    await event_channel.send("A **Bountiful Autumn** has blessed the world! Manpower gain is increased"
                                             "by 25%.")
                return
        # if event is lunar_eclipse
        if event == "lunar_eclipse":
            # weighted 80
            roll = random.randint(1, 100)
            if self.current:
                await conn.execute('''UPDATE cnc_modifiers SET manpower_mod = manpower_mod + .05;''')
                return
            if roll >= 20:
                # if the turn is 56 or later, increase manpower gain by 5% and a random trade good's value by -10
                if turn >= 56:
                    await conn.execute('''UPDATE cnc_modifiers SET manpower_mod = manpower_mod + .05;''')
                    random_good = await conn.fetchrow('''SELECT * FROM trade_goods ORDER BY random();''')
                    await conn.execute('''UPDATE trade_goods SET market_value = market_value - 10 WHERE name = $1;''',
                                       random_good['name'])
                    await event_channel.send(
                        "The sky is darkened by a **Lunar Eclipse**! Manpower gain is increased by 5% and "
                        f"{random_good['name']}'s market value has decreased by 10.")
                return
        # if event is solar_eclipse
        if event == "solar_eclipse":
            # weighted 80
            roll = random.randint(1, 100)
            if self.current:
                await conn.execute('''UPDATE cncusers SET national_unrest = national_unrest + 5;''')
                return
            if roll >= 20:
                # if the turn is 56 or later, increase national unrest by 5 and a random trade good's value by -10
                if turn >= 56:
                    await conn.execute('''UPDATE cncusers SET national_unrest = national_unrest + 5;''')
                    random_good = await conn.fetchrow('''SELECT * FROM trade_goods ORDER BY random();''')
                    await conn.execute(
                        '''UPDATE trade_goods SET market_value = market_value - 10 WHERE name = $1;''',
                        random_good['name'])
                    await event_channel.send(
                        "The sky is darkened by a **Solar Eclipse**! National unrest is increased by 5 and "
                        f"{random_good['name']}'s market value has decreased by 10.")
                return
        # if event is comet_sighting
        if event == "comet_sighting":
            # weighted 80
            roll = random.randint(1, 100)
            if self.current:
                await conn.execute('''UPDATE cncusers SET national_unrest = national_unrest + 5;''')
                return
            if roll >= 20:
                # if the turn is 56 or later, increase national unrest by 5
                if turn >= 56:
                    await conn.execute('''UPDATE cncusers SET national_unrest = national_unrest + 5;''')
                    await event_channel.send(
                        "A **Comet** has been sighted in the night sky! National unrest is increased by 5.")
                return
        # if event is new_trade_highway
        if event == "new_trade_highway":
            # weighted 80
            roll = random.randint(1, 100)
            if self.current:
                return
            if roll >= 20:
                # if the turn is 112 or later, increase market value for random good by 30
                if turn >= 112:
                    random_good = await conn.fetchrow('''SELECT * FROM trade_goods ORDER BY random();''')
                    await conn.execute(
                        '''UPDATE trade_goods SET market_value = market_value + 30 WHERE name = $1;''',
                        random_good['name'])
                    await event_channel.send(
                        f"A **New Trade Highway** has been established! {random_good['name']}'s market value has "
                        f"increased by 30!")
                return
        # if event is international_trade_collapse
        if event == "international_trade_collapse":
            # weighted 80
            roll = random.randint(1, 100)
            if self.current:
                return
            if roll >= 20:
                # if the turn is 112 or later, decrease market value for random good by 50
                if turn >= 112:
                    random_good = await conn.fetchrow('''SELECT * FROM trade_goods 
                    WHERE name != 'Gold' or name != 'Silver' ORDER BY random();''')
                    await conn.execute(
                        '''UPDATE trade_goods SET market_value = market_value - 50 WHERE name = $1;''',
                        random_good['name'])
                    await event_channel.send(
                        f"The world has suffered an **International Trade Collapse**! {random_good['name']}'s "
                        f"market value has decreased by 50!")
                return
        # if event is mines_run_dry
        if event == "mines_run_dry":
            # weighted 50
            roll = random.randint(1, 100)
            if self.current:
                return
            if roll >= 50:
                # if the turn is 224 or later, decrease market value for gold and silver by 50
                if turn >= 224:
                    await conn.execute(
                        '''UPDATE trade_goods SET market_value = market_value - 50 
                        WHERE name = 'Silver' or name = 'Gold';''')
                    await event_channel.send(
                        f"Overmining and prospecting has caused many of the world's mines to **Run Dry**! "
                        f"The market value of Gold and Silver has decreased by 50!")
                return
        # if event is new_mine_struck
        if event == "new_mine_struck":
            # weighted 50
            roll = random.randint(1, 100)
            if self.current:
                return
            if roll >= 50:
                # if the turn is 224 or later, increase market value for gold and silver by 50
                if turn >= 224:
                    await conn.execute(
                        '''UPDATE trade_goods SET market_value = market_value + 50 
                        WHERE name = 'Silver' or name = 'Gold';''')
                    await event_channel.send(
                        "A **New Mine** has been struck! The market value of Gold and Silver has increased by 50.")
                return
