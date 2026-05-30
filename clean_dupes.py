import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, delete
from sqlalchemy.orm import declarative_base

from database.models import Episode, Base
from config import DB_URL

async def main():
    engine = create_async_engine(DB_URL)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with SessionLocal() as session:
        result = await session.execute(select(Episode))
        episodes = result.scalars().all()
        
        # Track seen (anime_id, episode_number)
        seen = set()
        duplicates_to_delete = []
        
        for ep in episodes:
            key = (ep.anime_id, ep.episode_number)
            if key in seen:
                duplicates_to_delete.append(ep.id)
            else:
                seen.add(key)
                
        if duplicates_to_delete:
            print(f"Found {len(duplicates_to_delete)} duplicate episodes. Deleting...")
            await session.execute(delete(Episode).where(Episode.id.in_(duplicates_to_delete)))
            await session.commit()
            print("Duplicates deleted successfully!")
        else:
            print("No duplicates found.")

if __name__ == "__main__":
    asyncio.run(main())
