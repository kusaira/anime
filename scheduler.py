import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.requests import get_users_to_notify, mark_user_notified
from database.engine import AsyncSessionLocal

async def check_expiring_subscriptions(bot: Bot):
    try:
        async with AsyncSessionLocal() as session:
            users_to_notify = await get_users_to_notify(session)
            
            for user in users_to_notify:
                text = (
                    "⚠️ <b>Внимание!</b>\n\n"
                    "Ваша Premium-подписка истекает менее чем через <b>24 часа</b>.\n\n"
                    "Продлите подписку сейчас, чтобы не потерять доступ к эксклюзивным 4K аниме и фильмам!"
                )
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💎 Продлить подписку", callback_data="buy_premium")]
                ])
                
                try:
                    await bot.send_message(
                        chat_id=user.telegram_id, 
                        text=text, 
                        parse_mode="HTML", 
                        reply_markup=keyboard
                    )
                    await mark_user_notified(session, user.telegram_id)
                    logging.info(f"Sent expiration reminder to user {user.telegram_id}")
                except Exception as e:
                    logging.error(f"Failed to send reminder to user {user.telegram_id}: {e}")
                    
    except Exception as e:
        logging.error(f"Scheduler check_expiring_subscriptions error: {e}")

def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    # Run every 1 hour
    scheduler.add_job(check_expiring_subscriptions, "interval", hours=1, args=[bot])
    return scheduler
