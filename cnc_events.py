import asyncpg
import traceback


class Events:

    def __init__(self, nation, ctx):
        self.nation = nation

        # creates connection pool
        try:
            self.pool: asyncpg.pool = ctx.bot.pool
        except Exception:
            ctx.bot.logger.warning(traceback.format_exc())

    async def bountiful_harvest(self):
        conn = self.pool
        nation = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1;''', self.nation)
        if (0.7 * nation['total_manpower']) <= nation['manpower'] <= (0.8 * nation['total_manpower']):
            return 1.5

    async def scant_harvest(self):
        conn = self.pool
        nation = await conn.fetchrow('''SELECT * FROM cncusers WHERE username = $1;''', self.nation)
        if nation['manpower'] <= (0.4 * nation['total_manpower']):
            return 0.5
