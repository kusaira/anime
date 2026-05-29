from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database.requests import get_user, create_user, get_favorites, get_history, get_all_anime, get_anime, get_all_folders, get_unlinked_anime, get_folder, get_anime_in_folder
from keyboards.reply import get_main_menu
from keyboards.inline import get_payment_keyboard, get_catalog_keyboard, get_anime_keyboard, get_history_keyboard

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
    
    await callback.message.answer_photo(
        photo=anime.photo_file_id,
        caption=f"🎬 <b>{anime.title}</b>\n\n{anime.description}",
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
