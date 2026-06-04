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
    yoomoney_error = None
except Exception as e:
    Quickpay = None
    Client = None
    yoomoney_error = str(e)
    import logging
    logging.error(f"Failed to import yoomoney: {e}")

router = Router()

@router.callback_query(F.data == "buy_premium")
async def process_payment_invoice(callback: CallbackQuery):
    if not YOOMONEY_TOKEN:
        return await callback.answer("Ошибка: YOOMONEY_TOKEN не найден в .env", show_alert=True)
    if not YOOMONEY_RECEIVER:
        return await callback.answer("Ошибка: YOOMONEY_RECEIVER не найден в .env", show_alert=True)
    
    # Генерация уникального label для платежа
    label = f"{callback.from_user.id}_{int(datetime.utcnow().timestamp())}"
    
    import urllib.parse
    base_url = "https://yoomoney.ru/quickpay/confirm.xml"
    params = {
        "receiver": YOOMONEY_RECEIVER,
        "quickpay-form": "shop",
        "targets": "Premium-подписка на 30 дней",
        "paymentType": "SB",
        "sum": 150,
        "label": label
    }
    payment_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    text = (
        "💎 <b>Оформление Premium-подписки</b>\n\n"
        "Сумма к оплате: <b>150 ₽</b>\n"
        "Срок действия: <b>30 дней</b>\n\n"
        "1️⃣ Нажмите кнопку «Перейти к оплате» ниже.\n"
        "2️⃣ Оплатите счет картой или кошельком ЮMoney.\n"
        "3️⃣ После успешной оплаты вернитесь сюда и нажмите «Проверить оплату»."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Перейти к оплате", url=payment_url)],
        [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check_pay_{label}")]
    ])
    
    await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True)
    await callback.answer()

@router.callback_query(F.data.startswith("check_pay_"))
async def process_check_payment(callback: CallbackQuery, session: AsyncSession):
    if not YOOMONEY_TOKEN:
        return await callback.answer("Ошибка: платежный шлюз не настроен (нет токена).", show_alert=True)
    if not Client:
        return await callback.answer(f"Ошибка загрузки yoomoney: {yoomoney_error}", show_alert=True)
        
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
        error_str = str(e).lower()
        logging.error(f"YooMoney check error: {e}")
        if "timed out" in error_str or "timeout" in error_str:
            await callback.answer("⏳ Сервер ЮMoney долго отвечает. Подождите 5 секунд и нажмите кнопку еще раз!", show_alert=True)
        elif "validation error for history" in error_str or "401" in error_str:
            await callback.answer("❌ Ошибка авторизации кошелька (401). Токен ЮMoney недействителен. Обратитесь к админу.", show_alert=True)
        else:
            await callback.answer("Ошибка при проверке платежа. Обратитесь в поддержку.", show_alert=True)

@router.callback_query(F.data == "dummy_pay_alert")
async def dummy_pay_alert_handler(callback: CallbackQuery):
    await callback.answer("Это визуальная заглушка! Добавьте YOOMONEY_TOKEN и YOOMONEY_RECEIVER в .env для реальной оплаты.", show_alert=True)
