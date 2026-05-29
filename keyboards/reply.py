from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="📚 Каталог")],
            [KeyboardButton(text="⭐ Избранное"), KeyboardButton(text="🕒 История")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_admin_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Создать папку"), KeyboardButton(text="Удалить папку")],
            [KeyboardButton(text="Привязать аниме к папке")],
            [KeyboardButton(text="Добавить аниме"), KeyboardButton(text="Удалить аниме")],
            [KeyboardButton(text="Добавить серию"), KeyboardButton(text="Удалить серию")],
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
