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
            [KeyboardButton(text="Создать папку"), KeyboardButton(text="Удалить папку")],
            [KeyboardButton(text="Редактировать папку"), KeyboardButton(text="Удалить аниме из папки")],
            [KeyboardButton(text="Привязать аниме к папке")],
            [KeyboardButton(text="Добавить аниме"), KeyboardButton(text="Удалить аниме")],
            [KeyboardButton(text="Редактировать аниме")],
            [KeyboardButton(text="Добавить серию"), KeyboardButton(text="Удалить серию")],
            [KeyboardButton(text="Масс. загрузка серий")],
            [KeyboardButton(text="Список залитого аниме"), KeyboardButton(text="Список серий аниме")],
            [KeyboardButton(text="Список пользователей"), KeyboardButton(text="🔙 В главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard

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
