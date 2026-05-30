from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Anime, Episode, Favorite, History, Folder, FolderItem, Voiceover, WatchedEpisode
from datetime import datetime

async def get_user(session: AsyncSession, telegram_id: int):
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()

async def get_all_users(session: AsyncSession):
    result = await session.execute(select(User))
    return result.scalars().all()

async def get_user_by_username(session: AsyncSession, username: str):
    username = username.lstrip("@")
    result = await session.execute(select(User).where(User.username.ilike(username)))
    return result.scalar_one_or_none()

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

async def add_anime(session: AsyncSession, title: str, description: str, photo_file_id: str, is_4k: bool = False):
    anime = Anime(title=title, description=description, photo_file_id=photo_file_id, is_4k=is_4k)
    session.add(anime)
    await session.commit()
    await session.refresh(anime)
    return anime

async def get_or_create_voiceover(session: AsyncSession, anime_id: int, name: str):
    name = name.strip() if name != "-" else "Оригинал"
    result = await session.execute(
        select(Voiceover).where(Voiceover.anime_id == anime_id, Voiceover.name == name)
    )
    vo = result.scalars().first()
    if not vo:
        vo = Voiceover(anime_id=anime_id, name=name)
        session.add(vo)
        await session.commit()
        await session.refresh(vo)
    return vo

async def get_voiceovers(session: AsyncSession, anime_id: int):
    result = await session.execute(select(Voiceover).where(Voiceover.anime_id == anime_id))
    return result.scalars().all()

async def get_voiceover(session: AsyncSession, voiceover_id: int):
    result = await session.execute(select(Voiceover).where(Voiceover.id == voiceover_id))
    return result.scalars().first()

async def delete_voiceover(session: AsyncSession, voiceover_id: int):
    vo = await get_voiceover(session, voiceover_id)
    if vo:
        await session.delete(vo)
        await session.commit()
        return True
    return False

async def add_episode(session: AsyncSession, anime_id: int, episode_number: int, tg_file_id: str, description: str = None, voiceover_id: int = None):
    # Если voiceover_id не передан, получаем "Оригинал"
    if not voiceover_id:
        vo = await get_or_create_voiceover(session, anime_id, "Оригинал")
        voiceover_id = vo.id

    result = await session.execute(
        select(Episode).where(
            Episode.anime_id == anime_id, 
            Episode.episode_number == episode_number,
            Episode.voiceover_id == voiceover_id
        )
    )
    episode = result.scalars().first()
    
    if episode:
        episode.tg_file_id = tg_file_id
        if description is not None:
            episode.description = description if description != "-" else None
    else:
        desc_val = description if description != "-" else None
        episode = Episode(
            anime_id=anime_id, 
            episode_number=episode_number, 
            tg_file_id=tg_file_id, 
            description=desc_val,
            voiceover_id=voiceover_id
        )
        session.add(episode)
        
    await session.commit()
    return episode

async def delete_anime(session: AsyncSession, anime_id: int):
    anime = await get_anime(session, anime_id)
    if anime:
        from sqlalchemy import delete
        await session.execute(delete(FolderItem).where(FolderItem.anime_id == anime_id))
        await session.execute(delete(Episode).where(Episode.anime_id == anime_id))
        await session.execute(delete(Favorite).where(Favorite.anime_id == anime_id))
        await session.execute(delete(History).where(History.anime_id == anime_id))
        await session.execute(delete(WatchedEpisode).where(WatchedEpisode.anime_id == anime_id))
        await session.delete(anime)
        await session.commit()
        return True
    return False

async def update_anime(session: AsyncSession, anime_id: int, title: str = None, description: str = None):
    anime = await get_anime(session, anime_id)
    if not anime:
        return False
    if title:
        anime.title = title
    if description:
        anime.description = description
    await session.commit()
    return True

async def delete_episode(session: AsyncSession, episode_id: int):
    episode = await get_episode_by_id(session, episode_id)
    if episode:
        ep_num = episode.episode_number
        anime_id = episode.anime_id
        voiceover_id = episode.voiceover_id
        
        await session.delete(episode)
        
        # Смещаем номера серий
        from sqlalchemy import update
        await session.execute(
            update(Episode)
            .where(
                Episode.anime_id == anime_id,
                Episode.voiceover_id == voiceover_id,
                Episode.episode_number > ep_num
            )
            .values(episode_number=Episode.episode_number - 1)
        )
        await session.commit()
        return True
    return False

async def search_anime(session: AsyncSession, query: str):
    query_lower = query.lower()
    result = await session.execute(select(Anime))
    all_anime = result.scalars().all()
    return [a for a in all_anime if a.title and query_lower in a.title.lower()]

async def get_anime(session: AsyncSession, anime_id: int):
    result = await session.execute(select(Anime).where(Anime.id == anime_id))
    return result.scalar_one_or_none()

async def get_anime_by_title(session: AsyncSession, title: str):
    result = await session.execute(select(Anime).where(Anime.title.ilike(title.strip())))
    return result.scalars().first()

async def get_all_anime(session: AsyncSession):
    result = await session.execute(select(Anime))
    return result.scalars().all()

async def get_episodes(session: AsyncSession, anime_id: int, voiceover_id: int = None):
    query = select(Episode).where(Episode.anime_id == anime_id)
    if voiceover_id:
        query = query.where(Episode.voiceover_id == voiceover_id)
    result = await session.execute(query.order_by(Episode.episode_number))
    return result.scalars().all()

async def get_episode(session: AsyncSession, anime_id: int, episode_number: int, voiceover_id: int = None):
    query = select(Episode).where(Episode.anime_id == anime_id, Episode.episode_number == episode_number)
    if voiceover_id:
        query = query.where(Episode.voiceover_id == voiceover_id)
    result = await session.execute(query)
    return result.scalars().first()

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
        hist.last_episode_number = max(hist.last_episode_number, episode_number)
        hist.updated_at = datetime.utcnow()
    else:
        hist = History(user_id=user_id, anime_id=anime_id, last_episode_number=episode_number)
        session.add(hist)
    await session.commit()

async def mark_episode_watched(session: AsyncSession, user_id: int, anime_id: int, episode_number: int):
    result = await session.execute(
        select(WatchedEpisode).where(
            WatchedEpisode.user_id == user_id,
            WatchedEpisode.anime_id == anime_id,
            WatchedEpisode.episode_number == episode_number
        )
    )
    if not result.scalar_one_or_none():
        watched = WatchedEpisode(user_id=user_id, anime_id=anime_id, episode_number=episode_number)
        session.add(watched)
        await session.commit()

async def get_watched_episodes(session: AsyncSession, user_id: int, anime_id: int):
    result = await session.execute(
        select(WatchedEpisode.episode_number).where(
            WatchedEpisode.user_id == user_id,
            WatchedEpisode.anime_id == anime_id
        )
    )
    return result.scalars().all()

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

async def update_folder(session: AsyncSession, folder_id: int, title: str = None, description: str = None, photo_file_id: str = None):
    folder = await get_folder(session, folder_id)
    if not folder:
        return False
    if title:
        folder.title = title
    if description:
        folder.description = description
    if photo_file_id:
        folder.photo_file_id = photo_file_id
    await session.commit()
    return True

async def delete_folder(session: AsyncSession, folder_id: int):
    folder = await get_folder(session, folder_id)
    if folder:
        from sqlalchemy import delete
        await session.execute(delete(FolderItem).where(FolderItem.folder_id == folder_id))
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
    query_lower = query.lower()
    result = await session.execute(select(Folder))
    all_folders = result.scalars().all()
    return [f for f in all_folders if f.title and query_lower in f.title.lower()]

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

async def unlink_anime_from_folder(session: AsyncSession, folder_id: int, anime_id: int):
    from sqlalchemy import delete
    result = await session.execute(
        delete(FolderItem).where(FolderItem.folder_id == folder_id, FolderItem.anime_id == anime_id)
    )
    await session.commit()
    return result.rowcount > 0

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

async def get_unlinked_anime(session: AsyncSession, is_4k: bool = False):
    # Считаем привязанными только те аниме, папки которых реально существуют
    valid_folder_items = select(FolderItem.anime_id).join(Folder, Folder.id == FolderItem.folder_id)
    
    if is_4k:
        condition = Anime.is_4k == True
    else:
        from sqlalchemy import or_
        condition = or_(Anime.is_4k == False, Anime.is_4k.is_(None))
        
    result = await session.execute(
        select(Anime).where(~Anime.id.in_(valid_folder_items), condition)
    )
    return result.scalars().all()

async def get_4k_anime(session: AsyncSession):
    result = await session.execute(select(Anime).where(Anime.is_4k == True))
    return result.scalars().all()
