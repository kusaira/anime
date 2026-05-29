from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Anime, Episode, Favorite, History, Folder, FolderItem
from datetime import datetime

async def get_user(session: AsyncSession, telegram_id: int):
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()

async def get_all_users(session: AsyncSession):
    result = await session.execute(select(User))
    return result.scalars().all()

async def create_user(session: AsyncSession, telegram_id: int, username: str):
    user = User(telegram_id=telegram_id, username=username)
    session.add(user)
    await session.commit()
    return user

async def set_premium(session: AsyncSession, telegram_id: int, premium_until: datetime):
    await session.execute(
        update(User)
        .where(User.telegram_id == telegram_id)
        .values(is_premium=True, premium_until=premium_until)
    )
    await session.commit()

async def add_anime(session: AsyncSession, title: str, description: str, photo_file_id: str):
    anime = Anime(title=title, description=description, photo_file_id=photo_file_id)
    session.add(anime)
    await session.commit()
    await session.refresh(anime)
    return anime

async def add_episode(session: AsyncSession, anime_id: int, episode_number: int, tg_file_id: str):
    episode = Episode(anime_id=anime_id, episode_number=episode_number, tg_file_id=tg_file_id)
    session.add(episode)
    await session.commit()
    return episode

async def delete_anime(session: AsyncSession, anime_id: int):
    anime = await get_anime(session, anime_id)
    if anime:
        await session.delete(anime)
        await session.commit()
        return True
    return False

async def delete_episode(session: AsyncSession, episode_id: int):
    episode = await get_episode_by_id(session, episode_id)
    if episode:
        await session.delete(episode)
        await session.commit()
        return True
    return False

async def search_anime(session: AsyncSession, query: str):
    result = await session.execute(select(Anime).where(Anime.title.ilike(f"%{query}%")))
    return result.scalars().all()

async def get_anime(session: AsyncSession, anime_id: int):
    result = await session.execute(select(Anime).where(Anime.id == anime_id))
    return result.scalar_one_or_none()

async def get_anime_by_title(session: AsyncSession, title: str):
    result = await session.execute(select(Anime).where(Anime.title.ilike(title.strip())))
    return result.scalars().first()

async def get_all_anime(session: AsyncSession):
    result = await session.execute(select(Anime))
    return result.scalars().all()

async def get_episodes(session: AsyncSession, anime_id: int):
    result = await session.execute(select(Episode).where(Episode.anime_id == anime_id).order_by(Episode.episode_number))
    return result.scalars().all()

async def get_episode(session: AsyncSession, anime_id: int, episode_number: int):
    result = await session.execute(
        select(Episode)
        .where(Episode.anime_id == anime_id, Episode.episode_number == episode_number)
    )
    return result.scalar_one_or_none()

async def get_episode_by_id(session: AsyncSession, episode_id: int):
    result = await session.execute(select(Episode).where(Episode.id == episode_id))
    return result.scalar_one_or_none()

async def toggle_favorite(session: AsyncSession, user_id: int, anime_id: int):
    result = await session.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.anime_id == anime_id)
    )
    fav = result.scalar_one_or_none()
    if fav:
        await session.delete(fav)
        await session.commit()
        return False
    else:
        new_fav = Favorite(user_id=user_id, anime_id=anime_id)
        session.add(new_fav)
        await session.commit()
        return True

async def get_favorites(session: AsyncSession, user_id: int):
    result = await session.execute(
        select(Anime)
        .join(Favorite, Favorite.anime_id == Anime.id)
        .where(Favorite.user_id == user_id)
    )
    return result.scalars().all()

async def update_history(session: AsyncSession, user_id: int, anime_id: int, episode_number: int):
    result = await session.execute(
        select(History).where(History.user_id == user_id, History.anime_id == anime_id)
    )
    hist = result.scalar_one_or_none()
    if hist:
        hist.last_episode_number = episode_number
        hist.updated_at = datetime.utcnow()
    else:
        hist = History(user_id=user_id, anime_id=anime_id, last_episode_number=episode_number)
        session.add(hist)
    await session.commit()

async def get_history(session: AsyncSession, user_id: int, limit: int = 5):
    result = await session.execute(
        select(History, Anime)
        .join(Anime, Anime.id == History.anime_id)
        .where(History.user_id == user_id)
        .order_by(History.updated_at.desc())
        .limit(limit)
    )
    return result.all()

async def get_user_history_for_anime(session: AsyncSession, user_id: int, anime_id: int):
    result = await session.execute(
        select(History).where(History.user_id == user_id, History.anime_id == anime_id)
    )
    return result.scalar_one_or_none()

# --- Folders ---

async def add_folder(session: AsyncSession, title: str, description: str, photo_file_id: str):
    folder = Folder(title=title, description=description, photo_file_id=photo_file_id)
    session.add(folder)
    await session.commit()
    await session.refresh(folder)
    return folder

async def delete_folder(session: AsyncSession, folder_id: int):
    folder = await get_folder(session, folder_id)
    if folder:
        await session.delete(folder)
        await session.commit()
        return True
    return False

async def get_folder(session: AsyncSession, folder_id: int):
    result = await session.execute(select(Folder).where(Folder.id == folder_id))
    return result.scalar_one_or_none()

async def get_folder_by_title(session: AsyncSession, title: str):
    result = await session.execute(select(Folder).where(Folder.title.ilike(title.strip())))
    return result.scalars().first()

async def get_all_folders(session: AsyncSession):
    result = await session.execute(select(Folder))
    return result.scalars().all()

async def search_folders(session: AsyncSession, query: str):
    result = await session.execute(select(Folder).where(Folder.title.ilike(f"%{query}%")))
    return result.scalars().all()

async def link_anime_to_folder(session: AsyncSession, folder_id: int, anime_id: int):
    # Проверка на существование линка
    existing = await session.execute(
        select(FolderItem).where(FolderItem.folder_id == folder_id, FolderItem.anime_id == anime_id)
    )
    if not existing.scalar_one_or_none():
        link = FolderItem(folder_id=folder_id, anime_id=anime_id)
        session.add(link)
        await session.commit()
        return True
    return False

async def get_anime_in_folder(session: AsyncSession, folder_id: int):
    result = await session.execute(
        select(Anime)
        .join(FolderItem, FolderItem.anime_id == Anime.id)
        .where(FolderItem.folder_id == folder_id)
    )
    return result.scalars().all()

async def is_anime_in_any_folder(session: AsyncSession, anime_id: int):
    result = await session.execute(select(FolderItem).where(FolderItem.anime_id == anime_id))
    return result.scalars().first() is not None

async def get_folder_for_anime(session: AsyncSession, anime_id: int):
    result = await session.execute(
        select(Folder)
        .join(FolderItem, FolderItem.folder_id == Folder.id)
        .where(FolderItem.anime_id == anime_id)
    )
    return result.scalar_one_or_none()

async def get_unlinked_anime(session: AsyncSession):
    result = await session.execute(
        select(Anime).where(~Anime.id.in_(select(FolderItem.anime_id)))
    )
    return result.scalars().all()
