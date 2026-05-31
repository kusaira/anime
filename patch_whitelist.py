import os

handler_code = """
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Вайтлист (Техническое обслуживание) ---
@router.message(Command("whitelist"))
async def whitelist_cmd(message: Message, command: CommandObject):
    if not is_superadmin(message.from_user.id): return
    
    if command.args == "on":
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Подтверждаю (Включить)", callback_data="whitelist_confirm_on")]])
        await message.answer("⚠️ Вы уверены, что хотите включить режим технических работ? Обычные пользователи не смогут пользоваться ботом!", reply_markup=kb)
    elif command.args == "off":
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Подтверждаю (Выключить)", callback_data="whitelist_confirm_off")]])
        await message.answer("Вы уверены, что хотите выключить режим технических работ? Бот станет доступен всем.", reply_markup=kb)
    else:
        await message.answer("Используйте: /whitelist on или /whitelist off")

@router.callback_query(F.data == "whitelist_confirm_on")
async def whitelist_confirm_on(callback: CallbackQuery):
    if not is_superadmin(callback.from_user.id): return
    import json
    with open('whitelist_config.json', 'w', encoding='utf-8') as f:
        json.dump({"enabled": True}, f)
    await callback.message.edit_text("✅ Режим технических работ ВКЛЮЧЕН. Бот доступен только админами.")
    await callback.answer()

@router.callback_query(F.data == "whitelist_confirm_off")
async def whitelist_confirm_off(callback: CallbackQuery):
    if not is_superadmin(callback.from_user.id): return
    import json
    with open('whitelist_config.json', 'w', encoding='utf-8') as f:
        json.dump({"enabled": False}, f)
    await callback.message.edit_text("❌ Режим технических работ ВЫКЛЮЧЕН. Бот доступен всем пользователям.")
    await callback.answer()
"""

with open("handlers/admin.py", "a", encoding="utf-8") as f:
    f.write(handler_code)
