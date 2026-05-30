from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    keyboard = [
        [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="📚 Каталог")],
        [KeyboardButton(text="📺 Каталог 4К"), KeyboardButton(text="⭐ Избранное")],
        [KeyboardButton(text="🕒 История"), KeyboardButton(text="💎 Подписка")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_quality_keyboard():
    keyboard = [
        [KeyboardButton(text="1080p (Обычное)"), KeyboardButton(text="4K (Высокое)")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_admin_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Управление Аниме"), KeyboardButton(text="📺 Управление Сериями")],
            [KeyboardButton(text="📁 Управление Папками"), KeyboardButton(text="👥 Список пользователей")],
            [KeyboardButton(text="📥 Экспорт базы (CSV)"), KeyboardButton(text="🔙 В главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_admin_anime_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Добавить аниме"), KeyboardButton(text="Редактировать аниме")],
            [KeyboardButton(text="Удалить аниме"), KeyboardButton(text="Список залитого аниме")],
            [KeyboardButton(text="Привязать аниме к папке"), KeyboardButton(text="Удалить аниме из папки")],
            [KeyboardButton(text="↩️ Назад в админку")]
        ],
        resize_keyboard=True
    )

def get_admin_episodes_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Добавить серию"), KeyboardButton(text="Редактировать серию")],
            [KeyboardButton(text="Удалить серию"), KeyboardButton(text="Список серий аниме")],
            [KeyboardButton(text="Редактировать озвучку"), KeyboardButton(text="Удалить озвучку")],
            [KeyboardButton(text="Масс. загрузка серий")],
            [KeyboardButton(text="↩️ Назад в админку")]
        ],
        resize_keyboard=True
    )

def get_admin_folders_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Создать папку"), KeyboardButton(text="Редактировать папку")],
            [KeyboardButton(text="Удалить папку")],
            [KeyboardButton(text="↩️ Назад в админку")]
        ],
        resize_keyboard=True
    )

def get_edit_episode_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Видео"), KeyboardButton(text="Описание")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )

def get_cancel_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_finish_upload_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Завершить загрузку")]
        ],
        resize_keyboard=True
    )
    return keyboard
