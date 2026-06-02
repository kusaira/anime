from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_payment_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Купить подписку", callback_data="buy_premium")]
    ])
    return keyboard

def get_anime_keyboard(anime_id: int, is_favorite: bool):
    fav_text = "❌ Убрать из избранного" if is_favorite else "⭐ В избранное"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Смотреть", callback_data=f"watch_{anime_id}")],
        [InlineKeyboardButton(text=fav_text, callback_data=f"fav_{anime_id}")]
    ])
    return keyboard

def get_catalog_keyboard(items: list):
    builder = InlineKeyboardBuilder()
    for item in items:
        if type(item).__name__ == "Folder":
            is_4k = getattr(item, 'is_4k', False)
            is_movie = getattr(item, 'display_id', '') and str(getattr(item, 'display_id', '')).endswith('_3')
            movie = '🎥 ' if is_movie else ''
            title = f"📁 {'💎 ' if is_4k else ''}{movie}{item.title}"
            builder.button(text=title, callback_data=f"show_folder_{item.id}")
        else:
            is_4k = getattr(item, 'is_4k', False)
            is_movie = getattr(item, 'display_id', '') and str(getattr(item, 'display_id', '')).endswith('_3')
            movie = '🎥 ' if is_movie else ''
            title = f"{'💎 ' if is_4k else ''}{movie}{item.title}"
            builder.button(text=title, callback_data=f"show_anime_{item.id}")
    builder.adjust(1) # По 1 кнопке в ряд (списком)
    return builder.as_markup()

def get_voiceovers_keyboard(anime_id: int, voiceovers: list):
    builder = InlineKeyboardBuilder()
    for vo in voiceovers:
        builder.button(text=vo.name, callback_data=f"vo_{anime_id}_{vo.id}")
    builder.adjust(1)
    return builder.as_markup()

def get_episodes_keyboard(anime_id: int, voiceover_id: int, episodes: list, watched_episodes: list = None):
    builder = InlineKeyboardBuilder()
    watched_set = set(watched_episodes) if watched_episodes else set()
    for ep in episodes:
        text = str(ep.episode_number)
        if ep.episode_number in watched_set:
            text = f"{text} ✅"
        builder.button(text=text, callback_data=f"ep_{anime_id}_{voiceover_id}_{ep.episode_number}")
    builder.adjust(5) # По 5 кнопок в ряд
    
    # Кнопка назад к озвучкам
    builder.row(InlineKeyboardButton(text="⬅️ Назад к озвучкам", callback_data=f"watch_{anime_id}"))
    return builder.as_markup()

def get_video_navigation_keyboard(anime_id: int, voiceover_id: int, current_ep: int, episodes: list):
    builder = InlineKeyboardBuilder()
    
    episodes_sorted = sorted(episodes, key=lambda x: x.episode_number)
    prev_ep = None
    next_ep = None
    
    for i, ep in enumerate(episodes_sorted):
        if ep.episode_number == current_ep:
            if i > 0:
                prev_ep = episodes_sorted[i-1].episode_number
            if i < len(episodes_sorted) - 1:
                next_ep = episodes_sorted[i+1].episode_number
            break
            
    nav_buttons = []
    if prev_ep is not None:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Прошлая серия", callback_data=f"ep_{anime_id}_{voiceover_id}_{prev_ep}"))
    if next_ep is not None:
        nav_buttons.append(InlineKeyboardButton(text="След серия ➡️", callback_data=f"ep_{anime_id}_{voiceover_id}_{next_ep}"))
        
    if nav_buttons:
        builder.row(*nav_buttons)
        
    builder.row(InlineKeyboardButton(text="Список серий", callback_data=f"vo_{anime_id}_{voiceover_id}"))
    return builder.as_markup()

def get_history_keyboard(history_list: list):
    builder = InlineKeyboardBuilder()
    for history_entry, anime in history_list:
        text = f"🎬 {anime.title} — Серия {history_entry.last_episode_number}"
        builder.button(text=text, callback_data=f"show_anime_{anime.id}")
    builder.adjust(1)
    return builder.as_markup()

def get_folder_animes_keyboard(folder_id: int, animes: list):
    builder = InlineKeyboardBuilder()
    for anime in animes:
        builder.button(text=f"❌ {anime.title}", callback_data=f"unlink_{folder_id}_{anime.id}")
    builder.adjust(1)
    return builder.as_markup()
