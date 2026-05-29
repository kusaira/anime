import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, ADMIN_CHAT_IDS
from database import init_db, AsyncSessionLocal
from middlewares import ThrottlingMiddleware, DbSessionMiddleware
from handlers import user, admin

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    
    await init_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Передаем admin_chat_ids во все хендлеры
    dp.workflow_data.update({'admin_chat_ids': ADMIN_CHAT_IDS})
    
    # Подключаем middlewares
    dp.message.middleware(ThrottlingMiddleware(limit_seconds=2))
    dp.update.middleware(DbSessionMiddleware(session_pool=AsyncSessionLocal))
    
    # Подключаем роутеры
    dp.include_router(admin.router) # Сначала админ (перехват реплаев)
    dp.include_router(user.router)  # Затем юзер (все остальные сообщения)
    
    try:
        logging.info("Starting support bot")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
