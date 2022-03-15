import asyncio
import asyncpg
from random import randrange

async def resources():
    conn = await asyncpg.connect('postgresql://posgres@127.0.0.1:5432', database="botdb", password="postgres")
    provinceinfo = await conn.fetch('''SELECT * FROM provinces;''')
    province_ids = [p['id'] for p in provinceinfo]
    for p in province_ids:
        terrain = await conn.fetchrow('''SELECT terrain FROM provinces WHERE id = $1;''', p)
        if terrain['terrain'] == 0:
            await conn.execute('''UPDATE provinces SET worth = $1, troops = $2, manpower = $3 WHERE id = $4;''', randrange(300, 500), randrange(400, 600), randrange(3000, 5000), p)
        if terrain['terrain'] == 1:
            await conn.execute('''UPDATE provinces SET worth = $1, troops = $2, manpower = $3 WHERE id = $4;''', randrange(50, 150), randrange(150, 300), randrange(500, 800), p)
        if terrain['terrain'] == 2:
            await conn.execute('''UPDATE provinces SET worth = $1, troops = $2, manpower = $3 WHERE id = $4;''', randrange(200, 450), randrange(375, 800), randrange(2500, 4500), p)
        if terrain['terrain'] == 5:
            await conn.execute('''UPDATE provinces SET worth = $1, troops = $2, manpower = $3 WHERE id = $4;''', randrange(800, 1200), randrange(300, 700), randrange(600, 900), p)
        if terrain['terrain'] == 7:
            await conn.execute('''UPDATE provinces SET worth = $1, troops = $2, manpower = $3 WHERE id = $4;''', randrange(50, 100), randrange(100, 200), randrange(150, 300), p)
        if terrain['terrain'] == 9:
            await conn.execute('''UPDATE provinces SET worth = $1, troops = $2, manpower = $3 WHERE id = $4;''', randrange(25, 50), randrange(50, 100), randrange(150, 300), p)

asyncio.get_event_loop().run_until_complete(resources())
print("Done")