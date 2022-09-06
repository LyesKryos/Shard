import asyncpg
import traceback
import re


class Technology:

    def __init__(self, nation: str, tech: str, lookup: bool, ctx):
        # nation name
        self.nation = nation
        # tech name
        self.tech = tech
        self.lookup = lookup
        # creates connection pool
        try:
            self.pool: asyncpg.pool = ctx.bot.pool
        except Exception:
            ctx.bot.logger.warning(traceback.format_exc())
        self.ctx = ctx

    def sanitize_links_underscore(self, userinput: str) -> str:
        # replaces user input with proper, url-friendly code
        to_regex = userinput.replace(" ", "_")
        return re.sub(r"[^a-zA-Z0-9_-]", ' ', to_regex)

    def research(self):
        conn = self.pool
        tech_id = self.sanitize_links_underscore(self.tech)
        tech = await conn.fetchrow('''SELECT * FROM cnc_tech WHERE name = $1;''', tech_id)
        if tech is None:
            await self.ctx.send(f"No such technology as {self.tech}")
            return
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE user_id = $1;''', self.ctx.author.id)
        required_tech = tech['prerequisites']
        all_required = required_tech.split(',')
        some_required = required_tech.split('/')
        if len(some_required) >= 2:
            tech_check = any(researched in userinfo['researched'] for researched in some_required)
            if not tech_check:
                await self.ctx.send(f"{userinfo['username']} does not have all the necessary research completed.")
                return
        else:
            tech_check = all(researched in userinfo['researched'] for researched in all_required)
            if not tech_check:
                await self.ctx.send(f"{userinfo['username']} does not have all the necessary research completed.")
                return
        researching = await conn.fetchrow('''SELECT * FROM cnc_researching WHERE user_id = $1;''', self.ctx.author.id)
        if researching is not None:
            await self.ctx.send(f"{userinfo['username']} is already researching a technology.")
            return
        research_time = 4 + len(userinfo['researched'])
        if tech['exclusive'] is not None:
            if any(researched in userinfo['researched'] for researched in tech['exclusive']):
                await self.ctx.send(f"{tech['name']} cannot be researched "
                                    f"because it is mutually exclusive with {tech['exclusive']}.")
                return
        research_boosters = ['Writing', 'Mathematics', 'Literacy', 'Education', 'Chemistry']
        research_time *= 1 + (len(set(userinfo['researched']).intersection(research_boosters))*0.05)
        await conn.execute('''INSERT INTO cnc_researching VALUES ($1, $2, $3);''',
                           self.ctx.author.id, tech_id, research_time)
        await self.ctx.send(f"{tech['name']} will be finished researching in {research_time} turns.")

    def effects(self):
        conn = self.pool
        userinfo = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1;''', self.nation)
        techs = userinfo['researched']
        income_mod = 1
        tax_mod = 1
        workshop_procduction_mod = 1
        production_mod = 1
        trade_route = 0
        trade_route_efficiency_mod = 1
        national_unrest_suppression_efficiency_mod = 1
        local_unrest_suppresssion_efficiency_mod = 1
        wool_mod = 0
        fish_mod = 0
        fur_mod = 0
        grain_mod = 0
        livestock_mod = 0
        salt_mod = 0
        wine_mod = 0
        copper_mod = 0
        iron_mod = 0
        precious_goods_mod = 0
        spices_mod = 0
        tea_and_coffee_mod = 0
        chocolate_mod = 0
        cotton_mod = 0
        sugar_mod = 0
        tobacco_mod = 0
        dyes_mod = 0
        silk_mod = 0
        rare_wood_mod = 0
        glass_mod = 0
        paper_mod = 0
        precious_stones_mod = 0
        coal_mod = 0
        fruits_mod = 0
        raw_stone_mod = 0
        wood_mod = 0
        tin_mod = 0
        ivory_mod = 0
        market_value = 0
        for t in techs:
            if t == 'Currency':
                tax_mod += .05
            if t == 'Local Trade':
                income_mod += .005 * len(userinfo['provinces_owned'])
            if t == 'Agriculture':
                grain_mod += 1
                wine_mod += 1
                tea_and_coffee_mod += 1
                sugar_mod += 1
                tobacco_mod += 1
                fruits_mod += 1
            if t == 'Economic Stratification':
                tax_mod += .05
            if t == 'Regional Trade':
                income_mod += .01 * len(userinfo['provinces_owned'])
            if t == 'Early Industry':
                workshop_procduction_mod += 0.5
            if t == 'Guilds':
                workshop_procduction_mod += 0.5
            if t == 'Local Tariffs':
                production_mod += .05
            if t == 'Manorialism':
                workshop_procduction_mod += 0.5
            if t == 'Cottage Industry':
                wool_mod += 1
                fish_mod += 1
                fur_mod += 1
                grain_mod += 1
                livestock_mod += 1
                salt_mod += 1
                wine_mod += 1
                copper_mod += 1
                iron_mod += 1
                precious_goods_mod += 1
                spices_mod += 1
                tea_and_coffee_mod += 1
                chocolate_mod += 1
                cotton_mod += 1
                sugar_mod += 1
                tobacco_mod += 1
                dyes_mod += 1
                silk_mod += 1
                rare_wood_mod += 1
                glass_mod += 1
                paper_mod += 1
                precious_stones_mod += 1
                coal_mod += 1
                fruits_mod += 1
                raw_stone_mod += 1
                wood_mod += 1
                tin_mod += 1
                ivory_mod += 1
            if t == 'Global Markets':
                market_value += 1
            if t == 'Economics':
                tax_mod += 0.05
            if t == 'Banking and Investments':
                trade_route += 1
            if t == 'Early Industrialization':
                workshop_procduction_mod += 2
            if t == 'Merchants':
                trade_route_efficiency_mod += 0.05
            if t == 'Trade Fleets':
                trade_route_efficiency_mod += 0.05
            if t == 'Trading Ports':
                trade_route_efficiency_mod += userinfo['portlimit'][0] * 0.01
            if t == 'Privateering':
                incoming_trade = await conn.fetchrow('''SELECT count(*) FROM cnc_interactions
                WHERE recipient = $1 AND active = True;''', self.nation)
                if incoming_trade['count'] is None:
                    trade_count = 0
                else:
                    trade_count = incoming_trade['count']
                war = await conn.fetchrow('''SELECT * FROM cnc_interactions WHERE (recipient = $1 or sender = $1) and 
                active = True and type = 'war';''', self.nation)
                if war is not None:
                    mod = 0.05
                else:
                    mod = 0.01
                trade_route_efficiency_mod += trade_count * mod
            if t == 'Predatory Trading':
                trade_route_efficiency_mod += .01
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
                trade_route_efficiency_mod += trade_count * 0.01
            if t == 'Heraldry':
                national_unrest_suppression_efficiency_mod += 0.25
            if t == 'Philosophy':
                national_unrest_suppression_efficiency_mod += 0.05
            if t == 'Religion':
                national_unrest_suppression_efficiency_mod += 0.05
            if t == 'City Administration':
                tax_mod += 0.01
            if t == 'Regional Governance':
                local_unrest_suppresssion_efficiency_mod += 0.01
            if t == 'National Government':
                national_unrest_suppression_efficiency_mod += 0.05
            if t == 'Machines':
                workshop_procduction_mod += 0.5
            if t == 'Printing Press':
                national_unrest_suppression_efficiency_mod += 0.05
            if t == 'Irrigation':
                grain_mod += 1
                wine_mod += 1
                tea_and_coffee_mod += 1
                sugar_mod += 1
                tobacco_mod += 1
                fruits_mod += 1
            if t == 'Animal Husbandry':
                wool_mod += 1
                fur_mod += 1
                livestock_mod += 1
                fish_mod += 1
            if t == 'Livestock Farming':
                wool_mod += 1
                fur_mod += 1
                livestock_mod += 1
                fish_mod += 1
            if t == 'Crop Rotation':
                grain_mod += 1
                wine_mod += 1
                tea_and_coffee_mod += 1
                sugar_mod += 1
                tobacco_mod += 1
                fruits_mod += 1
            if t == 'Cash Crops':
                tobacco_mod += 1
                sugar_mod += 1
                cotton_mod += 1
                tea_and_coffee_mod += 1
            if t == 'Early Industrial Farming':
                grain_mod += 1
                wine_mod += 1
                tea_and_coffee_mod += 1
                sugar_mod += 1
                tobacco_mod += 1
                fruits_mod += 1
                wool_mod += 1
                fur_mod += 1
                livestock_mod += 1
                fish_mod += 1







