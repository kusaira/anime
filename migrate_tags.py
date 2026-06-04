import asyncio
from database.engine import engine
from sqlalchemy import text

async def migrate_tags():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE anime ADD COLUMN aliases VARCHAR;"))
            print("Column 'aliases' added successfully.")
        except Exception as e:
            print("Column 'aliases' might already exist or error occurred:", e)

if __name__ == "__main__":
    asyncio.run(migrate_tags())
