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
async def process_payment_invoice(callback: CallbackQuery, session: AsyncSession):
    if not YOOMONEY_TOKEN:
        return await callback.answer("Ошибка: YOOMONEY_TOKEN не найден в .env", show_alert=True)
    if not YOOMONEY_RECEIVER:
        return await callback.answer("Ошибка: YOOMONEY_RECEIVER не найден в .env", show_alert=True)
        
    from database.requests import get_settings
    settings = await get_settings(session)
    price = settings.premium_price
    duration = settings.premium_duration_days
    
    # Генерация уникального label для платежа
    label = f"{callback.from_user.id}_{int(datetime.utcnow().timestamp())}"
    
    import urllib.parse
    base_url = "https://yoomoney.ru/quickpay/confirm.xml"
    params = {
        "receiver": YOOMONEY_RECEIVER,
        "quickpay-form": "shop",
        "targets": f"Premium-подписка на {duration} дней",
        "paymentType": "SB",
        "sum": price,
        "label": label
    }
    payment_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    text = (
        "💎 <b>Оформление Premium-подписки</b>\n\n"
        f"Сумма к оплате: <b>{price} ₽</b>\n"
        f"Срок действия: <b>{duration} дней</b>\n\n"
        "1️⃣ Нажмите кнопку «Перейти к оплате» ниже.\n"
        "2️⃣ Оплатите счет картой или кошельком ЮMoney.\n"
        "3️⃣ После успешной оплаты вернитесь сюда и нажмите «Проверить оплату»."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Перейти к оплате", url=payment_url)],
        [InlineKeyboardButton(text="🎟 Ввести промокод", callback_data="enter_promo")],
        [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check_pay_{label}")]
    ])
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True)
    await callback.answer()

from aiogram.fsm.context import FSMContext
from states.fsm import UserUsePromo

@router.callback_query(F.data == "enter_promo")
async def enter_promo_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Пожалуйста, введите ваш промокод в чат:")
    await state.set_state(UserUsePromo.waiting_for_code)
    await callback.answer()

@router.message(UserUsePromo.waiting_for_code)
async def process_promo_code(message: Message, state: FSMContext, session: AsyncSession, bot):
    code = message.text.strip().upper()
    from database.requests import get_promo_code, has_user_used_promo, use_promo_code, get_settings
    
    promo = await get_promo_code(session, code)
    if not promo:
        return await message.answer("❌ Промокод не найден или введен неверно.")
        
    if promo.max_uses > 0 and promo.uses_count >= promo.max_uses:
        return await message.answer("❌ Этот промокод больше не действителен (исчерпан лимит использований).")
        
    if await has_user_used_promo(session, message.from_user.id, promo.id):
        return await message.answer("❌ Вы уже использовали этот промокод.")
        
    await use_promo_code(session, message.from_user.id, promo)
    settings = await get_settings(session)
    duration = settings.premium_duration_days
    price = settings.premium_price
    
    if promo.discount_type == 'free_days':
        days = promo.discount_value
        from database.requests import get_user
        user = await get_user(session, message.from_user.id)
        if user and user.is_premium and user.premium_until and user.premium_until > datetime.utcnow():
            premium_until = user.premium_until + timedelta(days=days)
        else:
            premium_until = datetime.utcnow() + timedelta(days=days)
            
        await set_premium(session, message.from_user.id, premium_until)
        await message.answer(f"🎉 Промокод активирован! Вы получили <b>{days} дней</b> Premium-подписки бесплатно!", parse_mode="HTML")
        # Уведомляем админов
        for admin_id in SUPERADMIN_IDS:
            try:
                await bot.send_message(admin_id, f"🎟 Пользователь <code>{message.from_user.id}</code> активировал промокод <b>{code}</b> на {days} бесплатных дней.", parse_mode="HTML")
            except:
                pass
    elif promo.discount_type == 'discount':
        new_price = max(1, price - promo.discount_value) # Цена не может быть меньше 1 рубля
        
        label = f"{message.from_user.id}_{int(datetime.utcnow().timestamp())}"
        import urllib.parse
        base_url = "https://yoomoney.ru/quickpay/confirm.xml"
        params = {
            "receiver": YOOMONEY_RECEIVER,
            "quickpay-form": "shop",
            "targets": f"Premium-подписка на {duration} дней (по промокоду {code})",
            "paymentType": "SB",
            "sum": new_price,
            "label": label
        }
        payment_url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        text = (
            "🎉 <b>Промокод успешно применен!</b>\n\n"
            f"Сумма к оплате со скидкой: <b>{new_price} ₽</b> (вместо {price} ₽)\n"
            f"Срок действия: <b>{duration} дней</b>\n\n"
            "Нажмите кнопку ниже для оплаты:"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Оплатить со скидкой", url=payment_url)],
            [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check_pay_{label}")]
        ])
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        
    await state.clear()

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
            from database.requests import get_settings, get_user
            settings = await get_settings(session)
            duration = settings.premium_duration_days
            price = settings.premium_price
            
            # Начисляем дни с текущего момента или добавляем к существующей подписке
            user = await get_user(session, callback.from_user.id)
            if user and user.is_premium and user.premium_until and user.premium_until > datetime.utcnow():
                premium_until = user.premium_until + timedelta(days=duration)
            else:
                premium_until = datetime.utcnow() + timedelta(days=duration)
                
            await set_premium(session, callback.from_user.id, premium_until)
            
            text = (
                "🎉 <b>ПОЗДРАВЛЯЕМ! Оплата прошла успешно!</b> 💎\n\n"
                f"Вы стали обладателем Premium-подписки на {duration} дней.\n"
                "Теперь вам доступен весь каталог 4K-аниме и фильмов в идеальном качестве.\n\n"
                "Приятного просмотра! 🍿"
            )
            
            # Удаляем сообщение с кнопками оплаты
            try:
                await callback.message.delete()
            except:
                pass
                
            from keyboards.reply import get_main_menu
            await callback.message.answer(text, parse_mode="HTML", reply_markup=get_main_menu())
            
            # Уведомляем админов
            admin_text = f"💰 <b>Новая покупка Premium! (ЮMoney)</b>\nПользователь: @{callback.from_user.username} (ID: <code>{callback.from_user.id}</code>)\nДлительность: {duration} дней"
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
