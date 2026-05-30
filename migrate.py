import asyncio
from database.engine import AsyncSessionLocal, engine
from sqlalchemy import text

async def migrate_display_ids():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE anime ADD COLUMN display_id VARCHAR;"))
            print("Column added.")
        except Exception as e:
            print("Column might already exist:", e)
            
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT id FROM anime;"))
        rows = result.fetchall()
        for row in rows:
            anime_id = row[0]
            await session.execute(text("UPDATE anime SET display_id = :d_id WHERE id = :a_id"), {"d_id": str(anime_id), "a_id": anime_id})
        await session.commit()
        print("Migrated successfully!")

if __name__ == "__main__":
    asyncio.run(migrate_display_ids())
