import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database.engine import init_db, AsyncSessionLocal
from middlewares.db_middleware import DbSessionMiddleware
from middlewares.whitelist_middleware import WhitelistMiddleware
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
    dp.message.middleware(WhitelistMiddleware())
    dp.callback_query.middleware(WhitelistMiddleware())
    
    # Подключаем роутеры
    dp.include_router(user.router)
    dp.include_router(search.router)
    dp.include_router(payments.router)
    dp.include_router(admin.router)
    
    # Глобальный обработчик ошибок
    from aiogram.types import ErrorEvent
    import traceback
    from config import SUPERADMIN_IDS

    @dp.errors()
    async def global_error_handler(event: ErrorEvent, bot: Bot):
        logging.error(f"Critical error: {event.exception}", exc_info=True)
        tb_str = ''.join(traceback.format_exception(type(event.exception), event.exception, event.exception.__traceback__))
        
        error_msg = f"<b>⚠️ ПРОИЗОШЛА ОШИБКА! ПЕРЕШЛИ ЭТОТ ЛОГ РАЗРАБОТЧИКУ</b>\n\n<pre><code class='language-python'>{tb_str[-3800:]}</code></pre>"
        for admin_id in SUPERADMIN_IDS:
            try:
                await bot.send_message(admin_id, error_msg, parse_mode="HTML")
            except Exception:
                pass

    
    # Запускаем бота
    try:
        from scheduler import setup_scheduler
        scheduler = setup_scheduler(bot)
        scheduler.start()
        
        logging.info("Starting bot")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
