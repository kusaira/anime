from datetime import datetime
from sqlalchemy import BigInteger, ForeignKey, Boolean, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_until: Mapped[datetime] = mapped_column(DateTime, nullable=True)

class Anime(Base):
    __tablename__ = 'anime'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    display_id: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    description: Mapped[str] = mapped_column(String)
    photo_file_id: Mapped[str] = mapped_column(String)
    is_4k: Mapped[bool] = mapped_column(Boolean, default=False)

class Voiceover(Base):
    __tablename__ = 'voiceovers'
    id: Mapped[int] = mapped_column(primary_key=True)
    anime_id: Mapped[int] = mapped_column(ForeignKey('anime.id', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(String)

class Episode(Base):
    __tablename__ = 'episodes'
    id: Mapped[int] = mapped_column(primary_key=True)
    anime_id: Mapped[int] = mapped_column(ForeignKey('anime.id', ondelete='CASCADE'))
    episode_number: Mapped[int] = mapped_column(Integer)
    tg_file_id: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String, nullable=True)
    voiceover_id: Mapped[int] = mapped_column(ForeignKey('voiceovers.id', ondelete='CASCADE'), nullable=True)

class Favorite(Base):
    __tablename__ = 'favorites'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    anime_id: Mapped[int] = mapped_column(ForeignKey('anime.id', ondelete='CASCADE'))

class History(Base):
    __tablename__ = 'history'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    anime_id: Mapped[int] = mapped_column(ForeignKey('anime.id', ondelete='CASCADE'))
    last_episode_number: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Folder(Base):
    __tablename__ = 'folders'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    photo_file_id: Mapped[str] = mapped_column(String)
    is_4k: Mapped[bool] = mapped_column(Boolean, default=False)

class FolderItem(Base):
    __tablename__ = 'folder_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    folder_id: Mapped[int] = mapped_column(ForeignKey('folders.id', ondelete='CASCADE'))
    anime_id: Mapped[int] = mapped_column(ForeignKey('anime.id', ondelete='CASCADE'))

class WatchedEpisode(Base):
    __tablename__ = 'watched_episodes'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    anime_id: Mapped[int] = mapped_column(ForeignKey('anime.id', ondelete='CASCADE'))
    episode_number: Mapped[int] = mapped_column(Integer)
