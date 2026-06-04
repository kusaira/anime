import asyncio
from datetime import datetime, timedelta
from database.engine import AsyncSessionLocal, init_db
from database.models import User
from sqlalchemy import update
from aiogram import Bot
from config import BOT_TOKEN, SUPERADMIN_IDS
from scheduler import check_expiring_subscriptions

async def test_notification():
    # 1. Сначала меняем тебе время в базе на "осталось 23 часа"
    async with AsyncSessionLocal() as session:
        # Берем твой ID (первый из списка админов)
        my_id = SUPERADMIN_IDS[0]
        
        target_time = datetime.utcnow() + timedelta(hours=23)
        await session.execute(
            update(User)
            .where(User.telegram_id == my_id)
            .values(is_premium=True, premium_until=target_time, notified_expiration=False)
        )
        await session.commit()
        print(f"✅ База обновлена! Для ID {my_id} установлено 23 часа до конца подписки.")

    # 2. Инициализируем бота и вручную дергаем функцию планировщика (чтобы не ждать час)
    bot = Bot(token=BOT_TOKEN)
    print("⏳ Запускаем проверку подписок (как это делает планировщик каждый час)...")
    
    try:
        await check_expiring_subscriptions(bot)
        print("✅ Проверка завершена! Сообщение должно было прилететь тебе в ТГ.")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test_notification())
