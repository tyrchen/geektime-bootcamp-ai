import asyncio
import asyncpg

async def test():
    conn = await asyncpg.connect(
        'postgresql://postgres:postgres@localhost:5432/blog_small',
        command_timeout=5
    )
    result = await conn.fetchval("SELECT 1")
    await conn.close()
    print(f"SUCCESS! Result: {result}")

asyncio.run(test())
