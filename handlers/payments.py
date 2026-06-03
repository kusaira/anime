from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database.requests import set_premium
from keyboards.reply import get_main_menu
from config import PAYMENT_TOKEN, SUPERADMIN_IDS

router = Router()

@router.callback_query(F.data == "buy_premium")
async def process_payment_invoice(callback: CallbackQuery):
    if not PAYMENT_TOKEN or PAYMENT_TOKEN == "123456789:TEST:dummy":
        # Визуальная заглушка (выглядит как инвойс)
        stub_text = (
            "💎 <b>Premium-подписка (1 месяц)</b>\n\n"
            "Эксклюзивный доступ ко всем 4K релизам и фильмам без ограничений! Качество, от которого не оторвать глаз.\n\n"
            "<i>(Это тестовая визуальная заглушка. Чтобы кнопка вела на реальную оплату, добавьте PAYMENT_TOKEN в .env)</i>"
        )
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        stub_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить 150 ₽", callback_data="dummy_pay_alert")]
        ])
        await callback.message.answer(stub_text, parse_mode="HTML", reply_markup=stub_kb)
        return await callback.answer()
    
    # Отправляем инвойс
    prices = [LabeledPrice(label="Premium на 30 дней", amount=15000)] # 150.00 RUB
    
    await callback.message.answer_invoice(
        title="💎 Premium-подписка (1 месяц)",
        description="Эксклюзивный доступ ко всем 4K релизам и фильмам без ограничений! Качество, от которого не оторвать глаз.",
        payload="premium_30_days",
        provider_token=PAYMENT_TOKEN,
        currency="RUB",
        prices=prices,
        photo_url="https://i.imgur.com/gA33aHw.jpeg", # Stylish anime banner placeholder
        photo_width=800,
        photo_height=450,
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False,
    )
    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message, session: AsyncSession):
    payment_info = message.successful_payment
    
    if payment_info.invoice_payload == "premium_30_days":
        # Начисляем 30 дней с текущего момента
        premium_until = datetime.utcnow() + timedelta(days=30)
        await set_premium(session, message.from_user.id, premium_until)
        
        text = (
            "🎉 <b>ПОЗДРАВЛЯЕМ! Оплата прошла успешно!</b> 💎\n\n"
            "Вы стали обладателем Premium-подписки на 30 дней.\n"
            "Теперь вам доступен весь каталог 4K-аниме и фильмов в идеальном качестве.\n\n"
            "Приятного просмотра! 🍿"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu())
        
        # Уведомляем админов
        admin_text = f"💰 <b>Новая покупка Premium!</b>\nПользователь: @{message.from_user.username} (ID: <code>{message.from_user.id}</code>)\nСумма: {payment_info.total_amount / 100} {payment_info.currency}"
        for admin_id in SUPERADMIN_IDS:
            try:
                await message.bot.send_message(admin_id, admin_text, parse_mode="HTML")
            except:
                pass

@router.callback_query(F.data == "dummy_pay_alert")
async def dummy_pay_alert_handler(callback: CallbackQuery):
    await callback.answer("Это визуальная заглушка! Добавьте PAYMENT_TOKEN в .env для реальной оплаты.", show_alert=True)
