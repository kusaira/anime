import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database.engine import init_db, AsyncSessionLocal
from middlewares.db_middleware import DbSessionMiddleware
from handlers import user, search, payments, admin

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    
    # Инициализация базы данных
    await init_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Подключаем middleware
    dp.update.middleware(DbSessionMiddleware(session_pool=AsyncSessionLocal))
    
    # Подключаем роутеры
    dp.include_router(user.router)
    dp.include_router(search.router)
    dp.include_router(payments.router)
    dp.include_router(admin.router)
    
    # Запускаем бота
    try:
        logging.info("Starting bot")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
