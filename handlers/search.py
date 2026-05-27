from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from states.fsm import SearchStates
from database.requests import search_anime, search_folders, is_anime_in_any_folder, get_anime, get_episodes, get_user_history_for_anime, toggle_favorite, update_history, get_episode, get_user
from keyboards.inline import get_anime_keyboard, get_episodes_keyboard, get_catalog_keyboard

router = Router()

@router.message(F.text == "🔍 Поиск")
async def start_search(message: Message, state: FSMContext):
    await message.answer("Введите название аниме для поиска:")
    await state.set_state(SearchStates.waiting_for_query)

@router.message(SearchStates.waiting_for_query, F.text)
async def process_search(message: Message, state: FSMContext, session: AsyncSession):
    query = message.text
    anime_results = await search_anime(session, query)
    folder_results = await search_folders(session, query)
    
    # Filter anime_results to only show unlinked anime
    unlinked_anime = []
    for a in anime_results:
        if not await is_anime_in_any_folder(session, a.id):
            unlinked_anime.append(a)
            
    results = list(folder_results) + list(unlinked_anime)
    
    if not results:
        await message.answer("По вашему запросу ничего не найдено.")
        await state.clear()
        return
    
    await state.clear()
    
    if len(results) == 1:
        item = results[0]
        if type(item).__name__ == "Folder":
            text = f"📁 <b>{item.title}</b>\n\n{item.description}\n\nОткройте каталог для просмотра серий (в разработке)."
            # Or ideally we could call the callback handler logic, but simple message is fine or redirect to catalog view
            # Since we have get_catalog_keyboard, we can just show it directly.
            # But we don't have anime list for this folder here. It's better to show the choice even for 1 folder.
            pass
            
        # If it's anime
        anime = item
        is_fav = False
        
        # Check if it's actually anime (has photo_file_id but no type check, but let's assume if it's 1 it might be anime)
        if type(item).__name__ == "Folder":
             await message.answer(
                "Найдена одна папка. Нажмите чтобы открыть:",
                reply_markup=get_catalog_keyboard(results)
            )
             return
        
        await message.answer_photo(
            photo=anime.photo_file_id,
            caption=f"🎬 <b>{anime.title}</b>\n\n{anime.description}",
            reply_markup=get_anime_keyboard(anime.id, is_fav),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "Найдено несколько совпадений. Выберите нужное:",
            reply_markup=get_catalog_keyboard(results)
        )

@router.callback_query(F.data.startswith("fav_"))
async def process_favorite(callback: CallbackQuery, session: AsyncSession):
    anime_id = int(callback.data.split("_")[1])
    user = await get_user(session, callback.from_user.id)
    is_fav = await toggle_favorite(session, user.id, anime_id)
    
    text = "Добавлено в избранное!" if is_fav else "Удалено из избранного."
    await callback.answer(text)
    
    # Обновляем кнопку
    await callback.message.edit_reply_markup(reply_markup=get_anime_keyboard(anime_id, is_fav))

@router.callback_query(F.data.startswith("watch_"))
async def process_watch(callback: CallbackQuery, session: AsyncSession):
    anime_id = int(callback.data.split("_")[1])
    episodes = await get_episodes(session, anime_id)
    
    if not episodes:
        return await callback.answer("Серии еще не добавлены.", show_alert=True)
    
    user = await get_user(session, callback.from_user.id)
    history = await get_user_history_for_anime(session, user.id, anime_id)
    last_ep = history.last_episode_number if history else None
    
    await callback.message.answer(
        "Выберите серию:",
        reply_markup=get_episodes_keyboard(anime_id, episodes, last_ep)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("ep_"))
async def process_episode(callback: CallbackQuery, session: AsyncSession):
    _, anime_id, ep_num = callback.data.split("_")
    anime_id = int(anime_id)
    ep_num = int(ep_num)
    
    episode = await get_episode(session, anime_id, ep_num)
    if not episode:
        return await callback.answer("Ошибка: серия не найдена.", show_alert=True)
    
    await callback.message.answer_video(video=episode.tg_file_id, caption=f"Серия {ep_num}")
    
    # Обновляем историю
    user = await get_user(session, callback.from_user.id)
    await update_history(session, user.id, anime_id, ep_num)
    await callback.answer()
