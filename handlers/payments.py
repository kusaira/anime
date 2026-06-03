from datetime import datetime, timedelta
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from database.requests import set_premium
from keyboards.reply import get_main_menu
from config import YOOMONEY_TOKEN, YOOMONEY_RECEIVER, SUPERADMIN_IDS

try:
    from yoomoney import Quickpay, Client
except ImportError:
    Quickpay = None
    Client = None

router = Router()

@router.callback_query(F.data == "buy_premium")
async def process_payment_invoice(callback: CallbackQuery):
    if not YOOMONEY_TOKEN or not YOOMONEY_RECEIVER or not Quickpay:
        stub_text = (
            "💎 <b>Premium-подписка (1 месяц)</b>\n\n"
            "Эксклюзивный доступ ко всем 4K релизам и фильмам без ограничений! Качество, от которого не оторвать глаз.\n\n"
            "<i>(Это визуальная заглушка ЮMoney. Добавьте YOOMONEY_TOKEN и YOOMONEY_RECEIVER в .env для реальной оплаты)</i>"
        )
        stub_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить 150 ₽", callback_data="dummy_pay_alert")]
        ])
        await callback.message.answer(stub_text, parse_mode="HTML", reply_markup=stub_kb)
        return await callback.answer()
    
    # Генерация уникального label для платежа
    label = f"{callback.from_user.id}_{int(datetime.utcnow().timestamp())}"
    
    quickpay = Quickpay(
        receiver=YOOMONEY_RECEIVER,
        quickpay_form="shop",
        targets="Premium-подписка на 30 дней",
        paymentType="SB",
        sum=150,
        label=label
    )
    
    text = (
        "💎 <b>Оформление Premium-подписки</b>\n\n"
        "Сумма к оплате: <b>150 ₽</b>\n"
        "Срок действия: <b>30 дней</b>\n\n"
        "1️⃣ Нажмите кнопку «Перейти к оплате» ниже.\n"
        "2️⃣ Оплатите счет картой или кошельком ЮMoney.\n"
        "3️⃣ После успешной оплаты вернитесь сюда и нажмите «Проверить оплату»."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Перейти к оплате", url=quickpay.base_url)],
        [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check_pay_{label}")]
    ])
    
    await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True)
    await callback.answer()

@router.callback_query(F.data.startswith("check_pay_"))
async def process_check_payment(callback: CallbackQuery, session: AsyncSession):
    if not YOOMONEY_TOKEN or not Client:
        return await callback.answer("Ошибка: платежный шлюз не настроен.", show_alert=True)
        
    label = callback.data.replace("check_pay_", "")
    
    try:
        client = Client(YOOMONEY_TOKEN)
        history = client.operation_history(label=label)
        
        is_paid = False
        if history.operations:
            for operation in history.operations:
                if operation.status == "success":
                    is_paid = True
                    break
                    
        if is_paid:
            # Начисляем 30 дней с текущего момента
            premium_until = datetime.utcnow() + timedelta(days=30)
            await set_premium(session, callback.from_user.id, premium_until)
            
            text = (
                "🎉 <b>ПОЗДРАВЛЯЕМ! Оплата прошла успешно!</b> 💎\n\n"
                "Вы стали обладателем Premium-подписки на 30 дней.\n"
                "Теперь вам доступен весь каталог 4K-аниме и фильмов в идеальном качестве.\n\n"
                "Приятного просмотра! 🍿"
            )
            
            # Удаляем сообщение с кнопками оплаты
            try:
                await callback.message.delete()
            except:
                pass
                
            await callback.message.answer(text, parse_mode="HTML", reply_markup=get_main_menu())
            
            # Уведомляем админов
            admin_text = f"💰 <b>Новая покупка Premium! (ЮMoney)</b>\nПользователь: @{callback.from_user.username} (ID: <code>{callback.from_user.id}</code>)\nСумма: 150 RUB"
            for admin_id in SUPERADMIN_IDS:
                try:
                    await callback.bot.send_message(admin_id, admin_text, parse_mode="HTML")
                except:
                    pass
                    
            await callback.answer("Оплата успешно подтверждена!")
        else:
            await callback.answer("Платеж еще не найден. Подождите пару минут и попробуйте снова.", show_alert=True)
            
    except Exception as e:
        logging.error(f"YooMoney check error: {e}")
        await callback.answer("Ошибка при проверке платежа. Обратитесь в поддержку.", show_alert=True)

@router.callback_query(F.data == "dummy_pay_alert")
async def dummy_pay_alert_handler(callback: CallbackQuery):
    await callback.answer("Это визуальная заглушка! Добавьте YOOMONEY_TOKEN и YOOMONEY_RECEIVER в .env для реальной оплаты.", show_alert=True)
