from random import randint, choice, uniform
import asyncpg
from typing import Tuple


class Skirmish:

    def __init__(self, attacking_army: asyncpg.Record, attached_attackers: int, defending_armies: list[asyncpg.Record] | list[dict],
                 terrain_id: int, conn: asyncpg.Pool, attack_mod: float, defense_mod: float, siege: bool = False):
        # define the class variables
        self.attacking_army = attacking_army
        self.defending_armies = defending_armies
        self.attached_attackers = attached_attackers
        self.terrain_id = terrain_id
        self.conn = conn
        self.attack_mod = attack_mod
        self.defense_mod = defense_mod
        self.siege = siege

    async def skirmish(self) -> Tuple[str, float, float]:
        """Execute the skirmish using the attacking army, defending army(s), and terrain.

        Returns skirmish victor -> str = 'attacker' or 'defender' and casualties percentages -> float, float."""
        # define the connection
        conn = self.conn
        # define the attack and defense roll modifiers
        attack_roll_mod = 0
        defense_roll_mod = 0

        # === TOTAL LOSS DEFENSE ===
        # if either army = 0 troops at any point, defer the win automatically to them
        if self.attacking_army['troops'] <= 0:
            victor = "defender"
            attack_casualties_percent, defense_casualties_percent = 0, 0
            return victor, attack_casualties_percent, defense_casualties_percent
        if sum(a['troops'] for a in self.defending_armies) <= 0:
            victor = "attacker"
            attack_casualties_percent, defense_casualties_percent = 0, 0
            return victor, attack_casualties_percent, defense_casualties_percent

        # === GENERALS INFO ===
        # get the attacking general info
        attacking_general_level = 0
        if self.attacking_army['general']:
            # pull the general level IF they are an attack general
            general_level = await conn.fetchval('''SELECT * FROM cnc_generals 
                                                   WHERE general_id = $1 AND type = 'Assault';''',
                                                self.attacking_army['general'])
            attacking_general_level = general_level if general_level is not None else 0
            # if this is a siege instead
            if self.siege:
                # pull the general level IF they are an siege general
                general_level = await conn.fetchval('''SELECT *
                                                       FROM cnc_generals
                                                       WHERE general_id = $1
                                                         AND type = 'Siege';''',
                                                    self.attacking_army['general'])
                attacking_general_level = general_level if general_level is not None else 0

        # add the general level to the attack roll
        attack_roll_mod += attacking_general_level

        # get the general of the largest defending army
        defending_general_army = max(self.defending_armies, key=lambda army: army['troops'])
        # get the defending general info
        defending_general_level = 0
        if defending_general_army['general']:
            # pull the general level IF they are a defensive general
            general_level = await conn.fetchval('''SELECT * FROM cnc_generals 
                                                   WHERE general_id = $1 AND type = 'Defensive';''',
                                                defending_general_army['general'])
            defending_general_level = general_level if general_level is not None else 0
        # add the general level to the defense roll
        defense_roll_mod += defending_general_level

        # === TERRAIN CASUALTIES ===
        terrain_casualties = await conn.fetchval('''SELECT modifier FROM cnc_terrains WHERE id = $1;''',
                                                 self.terrain_id)

        # === ARMY SIZE CONSIDERATIONS ===
        total_attackers = self.attacking_army['troops'] + self.attached_attackers
        total_defenders = sum(a['troops'] for a in self.defending_armies)
        # if the attacker is larger than the defender, add commensurate to the attacker
        if total_attackers > total_defenders:
            ratio = total_attackers / total_defenders
            attack_roll_mod += ((ratio - 1) if ratio - 1 > .25 else 0)
        # otherwise, do the defender. if the army sizes are the same, the ratio should pan out to 0 anyway
        else:
            ratio = total_defenders / total_attackers
            defense_roll_mod += ((ratio - 1) if ratio - 1 > .25 else 0)

        # === ROLLS ===
        attack_roll = randint(1, 5) + (attack_roll_mod * self.attack_mod)
        defense_roll = randint(1, 5) + (defense_roll_mod * self.defense_mod)
        # determine the victor
        if attack_roll > defense_roll:
            victor = "attacker"
        # ties default to defender
        else:
            victor = "defender"

        # === CASUALTIES ===
        # the attacker casualties = anywhere from 1% to defender roll/10 percent times the terrain casualties potential
        attack_casualties_percent = uniform(0.01, (defense_roll / 10)) * uniform(1, 1 + terrain_casualties)
        # the defender casualties = same as above
        defense_casualties_percent = uniform(0.01, (attack_roll / 10)) * uniform(1, 0.95 + terrain_casualties)

        return victor, attack_casualties_percent, defense_casualties_percent


class Battle:

    def __init__(self, attacking_army: asyncpg.Record, defending_armies: list[asyncpg.Record] | list[dict],
                 province_info: asyncpg.Record, conn: asyncpg.Pool, attack_mod: float, defense_mod: float,
                 landing: bool = False, siege: bool = False):
        # define the class variables
        self.attacking_army = attacking_army
        self.attached_attackers = []
        self.defending_armies = defending_armies
        self.province_info = province_info
        self.conn = conn
        self.attack_mod = attack_mod
        self.defense_mod = defense_mod
        self.landing = landing
        self.siege = siege

    async def battle(self) -> Tuple[str, int, int]:
        """Simulates a battle based on given parameters. Internally updates armies based on casualties.

        Returns victor -> str = 'attacker' or 'defender' and total casualties -> int (attacker), int (defender)"""
        # establish conn
        conn = self.conn

        # pull any attacking attached armies
        self.attached_attackers = await conn.fetch('''SELECT * FROM cnc_armies WHERE attached = $1;''',
                                                   self.attacking_army['army_id'])

        # === DEFENDING GENERAL INFO ===
        # get the general of the largest defending army
        defending_general_army = max(self.defending_armies, key=lambda army: army['troops'])
        # get the defending general info
        defending_general_level = 0
        if defending_general_army['general'] is not None:
            # pull the general level IF they are a defensive general
            general_level = await conn.fetchval('''SELECT level FROM cnc_generals 
                                                   WHERE general_id = $1 AND type = 'Defensive';''',
                                                defending_general_army['general'])
            defending_general_level = general_level if general_level is not None else 0

        # === BASE TERRAIN ROLLS ===
        base_terrain_rolls = await conn.fetchval('''SELECT roll FROM cnc_terrains WHERE id = $1;''',
                                                 self.province_info['terrain'])

        # === NUMBER OF SKIRMISHES ===
        skirmishes = max(defending_general_level + base_terrain_rolls, 1)

        # === TERRAIN OPTIONS ===
        terrain_options = [self.province_info['terrain']]
        # add options based on structures/geography
        if self.province_info['river']:
            # the id for river is 3
            terrain_options.append(3)
        if "City" in self.province_info['structures']:
            # the id for cities is 4
            terrain_options.append(4)
        if "Fort" in self.province_info['structures']:
            # the id for forts is 8
            terrain_options.append(8)
        if self.landing:
            # the id for landing is 6
            terrain_options.append(6)

        # === SIEGE ===
        if self.siege:
            # set the terrain options only to 8 (fort)
            terrain_options = [8]
            # set the skirmishes to the fort level
            skirmishes = self.province_info['fort_level']


        # === EXECUTE SKIRMISH ===
        # define casualties
        total_attack_casualties = 0
        total_defense_casualties = 0
        # define victories
        attack_victory_tally = 0
        defense_victory_tally = 0

        for skirm in range(skirmishes):
            # select a terrain
            terrain_id = choice(terrain_options)
            # attackers
            attached_attackers = sum(a['troops'] for a in self.attached_attackers)
            # initialize the skirmish class
            _skirmish = Skirmish(self.attacking_army, attached_attackers, self.defending_armies, terrain_id,
                                 conn, self.attack_mod, self.defense_mod, self.siege)

            victor, attack_casualties_percent, defense_casualties_percent = await _skirmish.skirmish()

            # update the casualty tracker
            total_attack_casualties += round((self.attacking_army['troops'] + attached_attackers)
                                             * attack_casualties_percent)
            # get the total number of attackers
            attacker_troop_count = self.attacking_army['troops'] + (attached_attackers if attached_attackers else 0)
            # define casualties share
            attack_casualties_share = (attacker_troop_count * (1-attack_casualties_percent))/(len(self.attached_attackers) + 1)

            # tally the victory
            if victor == "attacker":
                attack_victory_tally += 1
            else:
                defense_victory_tally += 1

            # update the attacking casualties in the db
            await conn.execute('''UPDATE cnc_armies
                                  SET troops = troops - $1
                                  WHERE army_id = $2 OR attached = $2;''',
                                round(attack_casualties_share), self.attacking_army['army_id'])

            # update the attacking army stats internally
            self.attacking_army = await conn.fetchrow('''SELECT *
                                                         FROM cnc_armies
                                                         WHERE army_id = $1;''',
                                                      self.attacking_army['army_id'])
            # and do the same for the attached armies (if any)
            self.attached_attackers = await conn.fetch('''SELECT * FROM cnc_armies WHERE attached = $1;''',
                                                       self.attacking_army['army_id'])

            # get the total defense casualties and add them to the tracker
            total_defense_casualties += round(
                sum(a['troops'] for a in self.defending_armies) * defense_casualties_percent)
            # define casualties share
            defense_casualties_share = (sum(a['troops'] for a in self.defending_armies) * (1-defense_casualties_percent)))/len(self.defending_armies)

            # for each of the defending armies, share the casualties
            refreshed = []
            for army in self.defending_armies:
                if army['army_id'] is None:
                    # manually reduce the synthetic troop count
                    updated = dict(army)
                    updated['troops'] = army['troops'] * (1 - defense_casualties_percent)
                    refreshed.append(updated)
                else:
                    # execute casualties
                    await conn.execute('''UPDATE cnc_armies
                                          SET troops = troops - $2
                                          WHERE army_id = $1;''',
                                       army['army_id'], defense_casualties_share)
                    army = await conn.fetchrow('''SELECT *
                                                  FROM cnc_armies
                                                  WHERE army_id = $1;''',
                                               army['army_id'])
                    refreshed.append(army)
            self.defending_armies = refreshed

            # === TOTAL LOSS CHECK ===
            # if any armies have 0, they are destroyed and removed from the battle
            if self.attacking_army['troops'] + sum(a['troops'] for a in self.attached_attackers) <= 0:
                defense_victory_tally = float('inf')
                break
            if sum(a['troops'] for a in self.defending_armies) <= 0:
                attack_victory_tally = float('inf')
                break

        # determine the victor
        if attack_victory_tally > defense_victory_tally:
            total_victor = "attacker"
        # defender wins ties
        else:
            total_victor = "defender"

        # return victor, total attack casualties, and total defense casualties
        return total_victor, total_attack_casualties, total_defense_casualties