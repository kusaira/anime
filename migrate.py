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
            
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN notified_expiration BOOLEAN DEFAULT 0;"))
            print("Column notified_expiration added.")
        except Exception as e:
            print("Column notified_expiration might already exist:", e)
            
    async with AsyncSessionLocal() as session:
        # Убрал перезапись display_id, чтобы не затирать кастомные ID
        print("Migrated successfully!")

if __name__ == "__main__":
    asyncio.run(migrate_display_ids())
