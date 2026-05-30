from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import DB_URL
from database.models import Base

engine = create_async_engine(DB_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Auto-migration for display_id
        from sqlalchemy import text
        try:
            await conn.execute(text("ALTER TABLE anime ADD COLUMN display_id VARCHAR;"))
            await conn.execute(text("UPDATE anime SET display_id = CAST(id AS VARCHAR) WHERE display_id IS NULL;"))
        except Exception:
            pass

