from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class MessageMap(Base):
    __tablename__ = 'message_map'
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_message_id = Column(Integer, index=True) # ID сообщения в чате админов
    user_telegram_id = Column(BigInteger)          # ID пользователя в ТГ
    user_message_id = Column(Integer)              # Оригинальный ID сообщения юзера
    created_at = Column(DateTime, default=datetime.utcnow)

engine = create_async_engine('sqlite+aiosqlite:///support.db', echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def save_message_mapping(session: AsyncSession, admin_msg_id: int, user_tg_id: int, user_msg_id: int):
    new_map = MessageMap(
        admin_message_id=admin_msg_id,
        user_telegram_id=user_tg_id,
        user_message_id=user_msg_id
    )
    session.add(new_map)
    await session.commit()

async def get_mapping_by_admin_msg(session: AsyncSession, admin_msg_id: int):
    from sqlalchemy import select
    result = await session.execute(
        select(MessageMap).where(MessageMap.admin_message_id == admin_msg_id)
    )
    return result.scalar_one_or_none()
