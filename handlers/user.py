import html
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from handlers.helpers import delete_previous_menu, save_menu_msg
from sqlalchemy.ext.asyncio import AsyncSession
from database.requests import get_user, create_user, get_favorites, get_history, get_all_anime, get_anime, get_all_folders, get_unlinked_anime, get_folder, get_anime_in_folder, get_4k_anime, get_user_by_username
from keyboards.reply import get_main_menu
from keyboards.inline import get_payment_keyboard, get_catalog_keyboard, get_anime_keyboard, get_history_keyboard
from datetime import datetime, timedelta
from config import ADMIN_IDS, SUPERADMIN_IDS

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext):
    user = await get_user(session, message.from_user.id)
    if not user:
        user = await create_user(session, message.from_user.id, message.from_user.username)
    
    text = (
        "🎥 <b>Добро пожаловать на Kusaira! Аниме в 4к!</b>\n\n"
        "Здесь вы можете смотреть любимые аниме в <b>оригинальном качестве</b> "
        "прямо в Telegram, без тормозов и назойливой рекламы."
    )
    await delete_previous_menu(message, state)
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")

@router.message(Command("premium"))
@router.message(F.text == "💎 Подписка")
async def cmd_premium(message: Message, session: AsyncSession, state: FSMContext, command: CommandObject = None):
    user = await get_user(session, message.from_user.id)

    # Логика для обычных юзеров
    if user and user.is_premium and user.premium_until:
        if user.premium_until > datetime.utcnow():
            days_left = (user.premium_until - datetime.utcnow()).days
            text = f"✨ <b>Ваша премиум подписка активна!</b>\n\nОсталось дней: <b>{days_left}</b>"
            await delete_previous_menu(message, state)
            return await message.answer(text, parse_mode="HTML")
        else:
            user.is_premium = False
            await session.commit()
            
    text = (
        "😔 <b>У вас нет активной подписки.</b>\n\n"
        "Оформите Premium-подписку, чтобы получить эксклюзивный доступ "
        "ко всем 4K релизам и фильмам без ограничений!"
    )
    await delete_previous_menu(message, state)
    await message.answer(text, parse_mode="HTML", reply_markup=get_payment_keyboard())

@router.message(F.text == "🆘 Поддержка")
async def cmd_support(message: Message, state: FSMContext):
    text = (
        "🆘 <b>Служба поддержки</b>\n\n"
        "Возникли проблемы с оплатой, не грузит видео или нашли баг? "
        "А может просто хотите предложить крутое аниме для добавления?\n\n"
        "Мы всегда на связи и готовы помочь! Пишите сюда: "
        "👉 https://t.me/Kusaira_anime?direct"
    )
    await delete_previous_menu(message, state)
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📚 Каталог")
async def show_catalog(message: Message, session: AsyncSession, state: FSMContext):
    folders = await get_all_folders(session, is_4k=False)
    unlinked = await get_unlinked_anime(session, is_4k=False)
    items = list(folders) + list(unlinked)
    
    if not items:
        return await message.answer("Каталог пока пуст.")
    
    await delete_previous_menu(message, state)
    msg = await message.answer(
        "📚 <b>Выберите из каталога:</b>",
        reply_markup=get_catalog_keyboard(items),
        parse_mode="HTML"
    )
    await save_menu_msg(msg.message_id, state)

from database.requests import get_4k_anime

@router.message(F.text == "📺 Каталог 4К")
async def show_4k_catalog(message: Message, session: AsyncSession, state: FSMContext):
    folders = await get_all_folders(session, is_4k=True)
    unlinked = await get_unlinked_anime(session, is_4k=True)
    items = list(folders) + list(unlinked)
    
    if not items:
        return await message.answer("Каталог 4К пока пуст.")
        
    await delete_previous_menu(message, state)
    msg = await message.answer(
        "📺 <b>Выберите аниме в 4К качестве:</b>\n<i>(Просмотр доступен только по подписке)</i>",
        reply_markup=get_catalog_keyboard(items),
        parse_mode="HTML"
    )
    await save_menu_msg(msg.message_id, state)

@router.callback_query(F.data.startswith("show_folder_"))
async def show_folder_card(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    folder_id = int(callback.data.split("_")[2])
    folder = await get_folder(session, folder_id)
    if not folder:
        return await callback.answer("Папка не найдена.", show_alert=True)
        
    anime_list = await get_anime_in_folder(session, folder_id)
    keyboard = get_catalog_keyboard(anime_list) if anime_list else None
        
    import html
    title_esc = html.escape(folder.title)
    desc_esc = html.escape(folder.description) if folder.description else ""
    text = f"📁 <b>{title_esc}</b>\n\n<pre>{desc_esc}</pre>\n\nВыберите аниме:"
    if len(text) > 1024:
        allowed_len = 1021 - len(f"📁 <b>{title_esc}</b>\n\n<pre></pre>\n\nВыберите аниме:")
        text = f"📁 <b>{title_esc}</b>\n\n<pre>{desc_esc[:allowed_len]}...</pre>\n\nВыберите аниме:"
    
    await delete_previous_menu(callback, state)
    
    if folder.photo_file_id:
        msg = await callback.message.answer_photo(
            photo=folder.photo_file_id,
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML",
            protect_content=True
        )
    else:
        msg = await callback.message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    await save_menu_msg(msg.message_id, state)
    await callback.answer()

@router.callback_query(F.data.startswith("show_anime_"))
async def show_anime_card(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    anime_id = int(callback.data.split("_")[2])
    anime = await get_anime(session, anime_id)
    if not anime:
        return await callback.answer("Аниме не найдено.", show_alert=True)
    
    is_fav = False # Для упрощения пока False, можно добавить проверку если нужно
    
    title = html.escape(anime.title)
    desc = html.escape(anime.description) if anime.description else "Нет описания."
    quality_tag = "💎 " if getattr(anime, 'is_4k', False) else ""
    movie_tag = "🎥 " if getattr(anime, 'display_id', '') and str(getattr(anime, 'display_id', '')).endswith('_3') else ""
    desc_esc = html.escape(desc) if desc else ""
    caption = f"🎬 {quality_tag}{movie_tag}<b>{title}</b>\n\n<pre>{desc_esc}</pre>"
    
    # Ограничение Telegram на длину caption для фото — 1024 символа
    if len(caption) > 1024:
        # 1024 - 3 (для "...") = 1021
        allowed_len = 1021 - len(f"🎬 {quality_tag}{movie_tag}<b>{title}</b>\n\n<pre></pre>")
        caption = f"🎬 {quality_tag}{movie_tag}<b>{title}</b>\n\n<pre>{desc_esc[:allowed_len]}...</pre>"
    
    await delete_previous_menu(callback, state)
    msg = await callback.message.answer_photo(
        photo=anime.photo_file_id,
        caption=caption,
        reply_markup=get_anime_keyboard(anime.id, is_fav),
        parse_mode="HTML"
    )
    await save_menu_msg(msg.message_id, state)
    await callback.answer()

@router.message(F.text == "⭐ Избранное")
async def show_favorites(message: Message, session: AsyncSession, state: FSMContext):
    user = await get_user(session, message.from_user.id)
    favs = await get_favorites(session, user.id)
    if not favs:
        return await message.answer("Ваш список избранного пуст.")
    
    await delete_previous_menu(message, state)
    msg = await message.answer(
        "⭐ <b>Ваше избранное:</b>",
        reply_markup=get_catalog_keyboard(favs),
        parse_mode="HTML"
    )
    await save_menu_msg(msg.message_id, state)

@router.message(F.text == "🕒 История")
async def show_history(message: Message, session: AsyncSession, state: FSMContext):
    user = await get_user(session, message.from_user.id)
    hist = await get_history(session, user.id)
    if not hist:
        return await message.answer("Вы еще ничего не смотрели.")
    
    await delete_previous_menu(message, state)
    msg = await message.answer(
        "🕒 <b>Последние просмотренные:</b>",
        reply_markup=get_history_keyboard(hist),
        parse_mode="HTML"
    )
    await save_menu_msg(msg.message_id, state)
