import random
import asyncpg
import math
import asyncio
from ShardBot import Shard


class calculations:

    def __init__(self, AttackingArmySize: int, DefendingArmySize: int, TerrainID: int):
        self.AttackingArmySize = AttackingArmySize
        self.DefendingArmySize = DefendingArmySize
        self.TerrainID = TerrainID
        self.armydifference = 0
        self.armymod = 0
        self.attackmod = 0
        self.defensemod = 0
        self.terrainmod = 0
        self.defenseoutput = 0
        self.attackoutput = 0
        self.attackroll = random.randint(1, 6)
        self.defenseroll = random.randint(1, 6)
        self.AttackingCasualties = 0
        self.DefendingCasualties = 0
        self.RemainingAttackingArmy = 0
        self.RemainingDefendingArmy = 0
        self.maxcas = 0

        # creates connection pool
        self.pool = asyncpg.create_pool('postgres://postgres@127.0.0.1:5432',
                                                      database="botdb")


    async def ArmyDifference(self):
        # calculates the army difference between the two initial numbers
        self.armydifference = self.AttackingArmySize - self.DefendingArmySize
        return self.armydifference

    async def ArmyMod(self):
        # calculates the army modifier based on the army difference
        await self.ArmyDifference()
        self.armymod = self.armydifference / 100
        return self.armymod

    async def AttackMod(self):
        # calculates the attacking army modifier
        await self.ArmyMod()
        self.attackmod = round(((self.armymod * self.attackroll) * 0.45) / 100, 4)
        return self.attackmod

    async def DefenseMod(self):
        # calculates the defending army modifier
        await self.ArmyMod()
        self.defensemod = round(((self.armymod * self.defenseroll) * 0.25) / 100, 4)
        return self.defensemod

    async def TerrainMod(self):
        # connection to database and gathers the terrain modifier based on the terrain ID
        conn = self.pool
        rawtmod = await conn.fetchrow('''SELECT modifier FROM terrains WHERE id = $1;''', self.TerrainID)
        self.terrainmod = float(rawtmod["modifier"])
        return self.terrainmod

    async def Output(self):
        # calls all the class functions necessary
        await self.AttackMod()
        await self.DefenseMod()
        await self.TerrainMod()
        # defines the attack output based on the attack roll, mod, and terrain mod
        self.attackoutput = self.attackroll + (self.attackmod - self.terrainmod)
        # defines the defense output based on the defense roll, mod, and terrain mod
        self.defenseoutput = self.defenseroll + (self.defensemod + self.terrainmod)
        return self.attackoutput, self.defenseoutput

    async def Casualties(self):
        # calls all the class functions necessary
        await self.Output()
        await self.TerrainMod()
        # connects to the database
        conn = self.pool
        # selects all from maxcas where the modifier value is the same as the terrain mod for both the defense maxcas
        # and attack maxcas
        maxcasraw = await conn.fetchrow('''SELECT * FROM maxcas WHERE modifier = $1;''', self.terrainmod)
        defensecasraw = await conn.fetchrow('''SELECT * FROM maxcas WHERE modifier = 0.0;''')
        self.maxcas = maxcasraw[str(self.defenseroll)]
        defensemaxcas = defensecasraw[str(self.attackroll)]
        # if the attacking army is larger than the defending army
        if self.AttackingArmySize > self.DefendingArmySize:
            # the attacking army casualties are equal to the attacking army minus the attacking army minus the
            # defending army size multiplies by the maxcas and multiplied by a random float between 0 and 1
            self.AttackingCasualties = math.ceil(
                self.AttackingArmySize - (self.AttackingArmySize - ((self.DefendingArmySize * self.maxcas) * random())))
        elif self.DefendingArmySize >= self.AttackingArmySize:
            # if the attacking army is smaller than the defending army, the inverse of the above
            self.AttackingCasualties = math.ceil(
                self.DefendingArmySize - (self.DefendingArmySize - ((self.AttackingArmySize * self.maxcas) * random())))
        # if the defending army is smaller than the attacking army
        if self.DefendingArmySize < self.AttackingArmySize:
            # the defending army casualties are equal to the attacking army minus the attacking army minus the
            # defending army size multiplies by the maxcas and multiplied by a random float between 0 and 1
            self.DefendingCasualties = math.ceil(self.AttackingArmySize - (
                    self.AttackingArmySize - ((self.DefendingArmySize * defensemaxcas) * random())))
        elif self.AttackingArmySize <= self.DefendingArmySize:
            # if the attacking army is smaller than the defending army, the inverse of the above
            self.DefendingCasualties = math.ceil(self.DefendingArmySize - (
                    self.DefendingArmySize - ((self.AttackingArmySize * defensemaxcas) * random())))
        # calculates the remaining numbers of the
        self.RemainingAttackingArmy = self.AttackingArmySize - self.AttackingCasualties
        self.RemainingDefendingArmy = self.DefendingArmySize - self.DefendingCasualties
        self.attackroll += self.attackmod
        self.defenseroll += self.defensemod
        if self.TerrainID == 8:
            self.defenseroll += 1
        return self.RemainingAttackingArmy, self.RemainingDefendingArmy, self.AttackingCasualties, self.DefendingCasualties, self.attackroll, self.defenseroll

