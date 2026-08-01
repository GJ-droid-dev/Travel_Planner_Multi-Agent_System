import asyncio, asyncpg, os
from dotenv import load_dotenv
load_dotenv()
async def main():
    db_url = os.environ['DATABASE_URL'].replace('&channel_binding=require', '')
    conn = await asyncpg.connect(db_url)
    val = await conn.fetchval("""
SELECT
itinerary
FROM
plans
WHERE
id::text
LIKE
'b1c0d01c%'
LIMIT
1
""")
    print(val)
    await conn.close()
asyncio.run(main())
