from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession
from database.requests import set_premium
from keyboards.reply import get_main_menu

router = Router()

@router.callback_query(F.data == "buy_premium")
async def process_payment_stub(callback: CallbackQuery, session: AsyncSession):
    # Здесь должна быть реальная логика ЮKassa/Stars.
    # В качестве заглушки мы просто "успешно" оплачиваем.
    
    # Подписка на 30 дней
    premium_until = datetime.utcnow() + timedelta(days=30)
    await set_premium(session, callback.from_user.id, premium_until)
    
    await callback.message.edit_text("🎉 Оплата прошла успешно! Теперь вам доступно 4K качество и весь функционал бота без рекламы.")
    await callback.message.answer("Добро пожаловать в Главное Меню!", reply_markup=get_main_menu())
    await callback.answer()
