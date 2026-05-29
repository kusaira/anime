from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession
from database import save_message_mapping

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "👋 <b>Здравствуйте!</b>\n\n"
        "Это бот службы поддержки. Опишите вашу проблему, задайте вопрос или отправьте скриншот.\n"
        "Администратор ответит вам при первой возможности."
    )
    await message.answer(text, parse_mode="HTML")

@router.message()
async def forward_to_admin(message: Message, session: AsyncSession, admin_chat_ids: list):
    # Если пишет сам админ в личку боту (не реплай), игнорируем
    if message.chat.id in admin_chat_ids:
        return
        
    # Формируем информационную шапку
    username = f"@{message.from_user.username}" if message.from_user.username else "Без юзернейма"
    info_text = (
        f"📥 <b>Новое обращение</b>\n"
        f"👤 <b>Пользователь:</b> {message.from_user.full_name} ({username})\n"
        f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
        f"──────────────"
    )
    
    # Отправляем каждому админу
    for admin_id in admin_chat_ids:
        try:
            await message.bot.send_message(admin_id, info_text, parse_mode="HTML")
            sent_msg = await message.copy_to(admin_id)
            
            # Сохраняем маппинг в БД для каждого админа
            await save_message_mapping(
                session,
                admin_msg_id=sent_msg.message_id,
                user_tg_id=message.from_user.id,
                user_msg_id=message.message_id
            )
        except Exception:
            pass
    
    await message.answer("✅ Ваше сообщение доставлено в поддержку. Ожидайте ответа.")
