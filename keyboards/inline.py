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
            builder.button(text=f"📁 {item.title}", callback_data=f"show_folder_{item.id}")
        else:
            builder.button(text=item.title, callback_data=f"show_anime_{item.id}")
    builder.adjust(1) # По 1 кнопке в ряд (списком)
    return builder.as_markup()

def get_episodes_keyboard(anime_id: int, episodes: list, watched_episodes: list = None):
    builder = InlineKeyboardBuilder()
    watched_set = set(watched_episodes) if watched_episodes else set()
    for ep in episodes:
        text = str(ep.episode_number)
        if ep.episode_number in watched_set:
            text = f"{text} ✅"
        builder.button(text=text, callback_data=f"ep_{anime_id}_{ep.episode_number}")
    builder.adjust(5) # По 5 кнопок в ряд
    return builder.as_markup()

def get_history_keyboard(history_list: list):
    builder = InlineKeyboardBuilder()
    for history_entry, anime in history_list:
        text = f"🎬 {anime.title} — Серия {history_entry.last_episode_number}"
        builder.button(text=text, callback_data=f"show_anime_{anime.id}")
    builder.adjust(1)
    return builder.as_markup()
