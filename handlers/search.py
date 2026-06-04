from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from states.fsm import SearchStates
from database.requests import search_anime, search_folders, is_anime_in_any_folder, get_anime, get_episodes, get_user_history_for_anime, toggle_favorite, update_history, get_episode, get_user, get_watched_episodes, mark_episode_watched, get_folder_for_anime
from keyboards.inline import get_anime_keyboard, get_episodes_keyboard, get_catalog_keyboard, get_payment_keyboard, get_video_navigation_keyboard, get_voiceovers_keyboard
from datetime import datetime
from handlers.helpers import delete_previous_menu, save_menu_msg, delete_previous_video, save_video_msg

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
    # Исключаем из результатов аниме те тайтлы, папка которых уже нашлась в поиске
    folder_ids = {f.id for f in folder_results}
    filtered_anime = []
    for anime in anime_results:
        folder = await get_folder_for_anime(session, anime.id)
        if folder and folder.id in folder_ids:
            continue
        filtered_anime.append(anime)
            
    results = list(folder_results) + list(filtered_anime)
    
    if not results:
        await message.answer("По вашему запросу ничего не найдено.")
        await state.clear()
        return
    
    await state.clear()
    
    if len(results) == 1:
        item = results[0]
        if type(item).__name__ == "Folder":
            await delete_previous_menu(message, state)
            msg = await message.answer(
                "Найдена одна папка. Нажмите чтобы открыть:",
                reply_markup=get_catalog_keyboard(results)
            )
            await save_menu_msg(msg.message_id, state)
            return
            
        # Если это аниме
        anime = item
        
        user = await get_user(session, message.from_user.id)
        if not user:
            from database.requests import create_user
            user = await create_user(session, message.from_user.id, message.from_user.username)
            
        from database.requests import get_favorites
        favs = await get_favorites(session, user.id)
        is_fav = any(f.id == anime.id for f in favs) if favs else False
        
        quality_tag = "💎 " if getattr(anime, 'is_4k', False) else ""
        movie_tag = "🎥 " if getattr(anime, 'display_id', '') and str(getattr(anime, 'display_id', '')).endswith('_3') else ""
        
        await delete_previous_menu(message, state)
        msg = await message.answer_photo(
            photo=anime.photo_file_id,
            caption=f"🎬 {quality_tag}{movie_tag}<b>{anime.title}</b>\n\n{anime.description}",
            reply_markup=get_anime_keyboard(anime.id, is_fav),
            parse_mode="HTML",
            protect_content=True
        )
        await save_menu_msg(msg.message_id, state)
    else:
        await delete_previous_menu(message, state)
        msg = await message.answer(
            "Найдено несколько совпадений. Выберите нужное:",
            reply_markup=get_catalog_keyboard(results)
        )
        await save_menu_msg(msg.message_id, state)

@router.callback_query(F.data.startswith("fav_"))
async def process_favorite(callback: CallbackQuery, session: AsyncSession):
    anime_id = int(callback.data.split("_")[1])
    user = await get_user(session, callback.from_user.id)
    is_fav = await toggle_favorite(session, user.id, anime_id)
    
    text = "Добавлено в избранное!" if is_fav else "Удалено из избранного."
    await callback.answer(text)
    
    # Обновляем кнопку
    from aiogram.exceptions import TelegramBadRequest
    try:
        await callback.message.edit_reply_markup(reply_markup=get_anime_keyboard(anime_id, is_fav))
    except TelegramBadRequest:
        pass

@router.callback_query(F.data.startswith("watch_"))
async def process_watch(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    anime_id = int(callback.data.split("_")[1])
    
    from database.requests import get_voiceovers
    voiceovers = await get_voiceovers(session, anime_id)
    
    if not voiceovers:
        return await callback.answer("Озвучки или серии еще не добавлены.", show_alert=True)
        
    await delete_previous_menu(callback, state)
    msg = await callback.message.answer(
        "Выберите озвучку:",
        reply_markup=get_voiceovers_keyboard(anime_id, voiceovers)
    )
    await save_menu_msg(msg.message_id, state)
    await callback.answer()

@router.callback_query(F.data.startswith("vo_"))
async def process_voiceover(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    _, anime_id, voiceover_id = callback.data.split("_")
    anime_id = int(anime_id)
    voiceover_id = int(voiceover_id)
    
    episodes = await get_episodes(session, anime_id, voiceover_id)
    if not episodes:
        return await callback.answer("Серии для этой озвучки не найдены.", show_alert=True)
        
    user = await get_user(session, callback.from_user.id)
    watched_eps = await get_watched_episodes(session, user.id, anime_id)
    
    await delete_previous_menu(callback, state)
    msg = await callback.message.answer(
        "Выберите серию:",
        reply_markup=get_episodes_keyboard(anime_id, voiceover_id, episodes, watched_eps)
    )
    await save_menu_msg(msg.message_id, state)
    await callback.answer()

@router.callback_query(F.data.startswith("ep_"))
async def process_episode(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    _, anime_id, voiceover_id, ep_num = callback.data.split("_")
    anime_id = int(anime_id)
    voiceover_id = int(voiceover_id)
    ep_num = int(ep_num)
    
    episode = await get_episode(session, anime_id, ep_num, voiceover_id)
    if not episode:
        return await callback.answer("Ошибка: серия не найдена.", show_alert=True)
    
    anime = await get_anime(session, anime_id)
    if anime and getattr(anime, 'is_4k', False):
        user = await get_user(session, callback.from_user.id)
        now = datetime.utcnow()
        is_premium = user and user.is_premium and (not user.premium_until or user.premium_until >= now)
        is_movie = getattr(anime, 'display_id', '') and str(getattr(anime, 'display_id', '')).endswith('_3')
        is_free_preview = (not is_movie) and ep_num == 1
        
        if not is_premium and not is_free_preview:
            if is_movie:
                text = "🚫 <b>Доступ запрещен!</b>\n\nЭтот фильм загружен в 4К качестве и доступен только пользователям с Premium подпиской."
            else:
                text = "🚫 <b>Доступ запрещен!</b>\n\nСмотреть серии в 4К (начиная со второй) могут только пользователи с Premium подпиской.\n<i>(Первая серия доступна бесплатно для оценки качества!)</i>"
            return await callback.message.answer(text, reply_markup=get_payment_keyboard(), parse_mode="HTML")

    # Удаляем только предыдущее меню, видео оставляем
    await delete_previous_menu(callback, state)
    
    caption = f"Серия {ep_num}"
    if episode.description and episode.description != "-":
        caption += f"\n\n{episode.description}"
        
    vid_msg = await callback.message.answer_video(video=episode.tg_file_id, caption=caption, protect_content=True)
    
    # Сохраняем текущую серию для быстрого редактирования
    await state.update_data(viewing_episode_id=episode.id)
    
    # Обновляем историю и отмечаем серию как просмотренную
    user = await get_user(session, callback.from_user.id)
    await update_history(session, user.id, anime_id, ep_num)
    await mark_episode_watched(session, user.id, anime_id, ep_num)
    
    episodes = await get_episodes(session, anime_id, voiceover_id)
        
    # Отправляем клавиатуру навигации под видео для удобства
    menu_msg = await callback.message.answer(
        "📺 Приятного просмотра! Выберите действие:",
        reply_markup=get_video_navigation_keyboard(anime_id, voiceover_id, ep_num, episodes)
    )
    await save_menu_msg(menu_msg.message_id, state)
        
    await callback.answer()
