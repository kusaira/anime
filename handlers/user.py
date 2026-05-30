import html
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database.requests import get_user, create_user, get_favorites, get_history, get_all_anime, get_anime, get_all_folders, get_unlinked_anime, get_folder, get_anime_in_folder, get_4k_anime, get_user_by_username
from keyboards.reply import get_main_menu
from keyboards.inline import get_payment_keyboard, get_catalog_keyboard, get_anime_keyboard, get_history_keyboard
from datetime import datetime, timedelta
from config import ADMIN_IDS

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    user = await get_user(session, message.from_user.id)
    if not user:
        user = await create_user(session, message.from_user.id, message.from_user.username)
    
    text = (
        "🎥 <b>Добро пожаловать на Kusaira! Аниме в 4к!</b>\n\n"
        "Здесь вы можете смотреть любимые аниме в <b>оригинальном качестве</b> "
        "прямо в Telegram, без тормозов и назойливой рекламы."
    )
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")

@router.message(Command("premium"))
@router.message(F.text == "💎 Подписка")
async def cmd_premium(message: Message, session: AsyncSession, command: CommandObject = None):
    user = await get_user(session, message.from_user.id)
    
    # Обработка /premium gift для админов
    if command and command.args and command.args.startswith("gift") and message.from_user.id in ADMIN_IDS:
        args = command.args.split()
        if len(args) == 3:
            days = args[1]
            target_username = args[2]
            if days.isdigit():
                target_user = await get_user_by_username(session, target_username)
                if target_user:
                    now = datetime.utcnow()
                    if target_user.is_premium and target_user.premium_until and target_user.premium_until > now:
                        new_until = target_user.premium_until + timedelta(days=int(days))
                    else:
                        new_until = now + timedelta(days=int(days))
                    
                    target_user.is_premium = True
                    target_user.premium_until = new_until
                    await session.commit()
                    
                    await message.answer(f"✅ Пользователю {target_username} выдана подписка на {days} дней!")
                    try:
                        await message.bot.send_message(
                            target_user.telegram_id, 
                            f"🎉 <b>Вам подарили премиум подписку!</b>\n\nДлительность: <b>{days} дней</b>.\nНаслаждайтесь просмотром!", 
                            parse_mode="HTML"
                        )
                    except:
                        pass
                else:
                    await message.answer("❌ Пользователь с таким юзернеймом не найден в базе.")
            else:
                await message.answer("❌ Количество дней должно быть числом.")
        else:
            await message.answer("❌ Формат: /premium gift [дни] [@username]")
        return

    # Логика для обычных юзеров
    if user and user.is_premium and user.premium_until:
        if user.premium_until > datetime.utcnow():
            days_left = (user.premium_until - datetime.utcnow()).days
            text = f"✨ <b>Ваша премиум подписка активна!</b>\n\nОсталось дней: <b>{days_left}</b>"
            return await message.answer(text, parse_mode="HTML")
        else:
            user.is_premium = False
            await session.commit()
            
    text = (
        "😔 <b>У вас нет активной подписки.</b>\n\n"
        "Для оформления подписки и получения доступа к эксклюзивным "
        "функциям, напишите в саппорт: @yto4ka39"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📚 Каталог")
async def show_catalog(message: Message, session: AsyncSession):
    folders = await get_all_folders(session)
    unlinked = await get_unlinked_anime(session, is_4k=False)
    items = list(folders) + list(unlinked)
    
    if not items:
        return await message.answer("Каталог пока пуст.")
    
    await message.answer(
        "📚 <b>Выберите из каталога:</b>",
        reply_markup=get_catalog_keyboard(items),
        parse_mode="HTML"
    )

from database.requests import get_4k_anime

@router.message(F.text == "📺 Каталог 4К")
async def show_4k_catalog(message: Message, session: AsyncSession):
    user = await get_user(session, message.from_user.id)
    now = datetime.utcnow()
    
    if not user or not user.is_premium or (user.premium_until and user.premium_until < now):
        if user and user.is_premium:
            user.is_premium = False
            await session.commit()
        await message.answer(
            "🚫 <b>Каталог 4К доступен только по подписке!</b>\n\nОформите премиум, чтобы смотреть аниме в максимальном качестве.",
            reply_markup=get_payment_keyboard(),
            parse_mode="HTML"
        )
        return
        
    items = await get_4k_anime(session)
    
    if not items:
        return await message.answer("Каталог 4К пока пуст.")
    
    await message.answer(
        "📺 <b>Выберите аниме в 4К качестве:</b>",
        reply_markup=get_catalog_keyboard(items),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("show_folder_"))
async def show_folder_card(callback: CallbackQuery, session: AsyncSession):
    folder_id = int(callback.data.split("_")[2])
    folder = await get_folder(session, folder_id)
    if not folder:
        return await callback.answer("Папка не найдена.", show_alert=True)
        
    anime_list = await get_anime_in_folder(session, folder_id)
    keyboard = get_catalog_keyboard(anime_list) if anime_list else None
        
    text = f"📁 <b>{folder.title}</b>\n\n{folder.description}\n\nВыберите аниме:"
    
    if folder.photo_file_id:
        await callback.message.answer_photo(
            photo=folder.photo_file_id,
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(F.data.startswith("show_anime_"))
async def show_anime_card(callback: CallbackQuery, session: AsyncSession):
    anime_id = int(callback.data.split("_")[2])
    anime = await get_anime(session, anime_id)
    if not anime:
        return await callback.answer("Аниме не найдено.", show_alert=True)
    
    is_fav = False # Для упрощения пока False, можно добавить проверку если нужно
    
    title = html.escape(anime.title)
    desc = html.escape(anime.description) if anime.description else "Нет описания."
    caption = f"🎬 <b>{title}</b>\n\n{desc}"
    
    # Ограничение Telegram на длину caption для фото — 1024 символа
    if len(caption) > 1024:
        # 1024 - 3 (для "...") = 1021
        allowed_len = 1021 - len(f"🎬 <b>{title}</b>\n\n")
        caption = f"🎬 <b>{title}</b>\n\n{desc[:allowed_len]}..."
    
    await callback.message.answer_photo(
        photo=anime.photo_file_id,
        caption=caption,
        reply_markup=get_anime_keyboard(anime.id, is_fav),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(F.text == "⭐ Избранное")
async def show_favorites(message: Message, session: AsyncSession):
    user = await get_user(session, message.from_user.id)
    favs = await get_favorites(session, user.id)
    if not favs:
        return await message.answer("Ваш список избранного пуст.")
    
    await message.answer(
        "⭐ <b>Ваше избранное:</b>",
        reply_markup=get_catalog_keyboard(favs),
        parse_mode="HTML"
    )

@router.message(F.text == "🕒 История")
async def show_history(message: Message, session: AsyncSession):
    user = await get_user(session, message.from_user.id)
    hist = await get_history(session, user.id)
    if not hist:
        return await message.answer("Вы еще ничего не смотрели.")
    
    await message.answer(
        "🕒 <b>Последние просмотренные:</b>",
        reply_markup=get_history_keyboard(hist),
        parse_mode="HTML"
    )
