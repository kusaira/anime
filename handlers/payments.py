from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession
from database.requests import set_premium
from keyboards.reply import get_main_menu

router = Router()

@router.callback_query(F.data == "buy_premium")
async def process_payment_stub(callback: CallbackQuery, session: AsyncSession):
    text = (
        "😔 <b>У вас нет активной подписки.</b>\n\n"
        "Для оформления подписки и получения доступа к эксклюзивным "
        "функциям, напишите в саппорт: https://t.me/Kusaira_anime?direct"
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()
