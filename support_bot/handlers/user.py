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
async def forward_to_admin(message: Message, session: AsyncSession, admin_chat_id: int):
    # Если пишет сам админ в админском чате (не реплай), игнорируем
    if message.chat.id == admin_chat_id:
        return
        
    # Формируем информационную шапку
    username = f"@{message.from_user.username}" if message.from_user.username else "Без юзернейма"
    info_text = (
        f"📥 <b>Новое обращение</b>\n"
        f"👤 <b>Пользователь:</b> {message.from_user.full_name} ({username})\n"
        f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
        f"──────────────"
    )
    
    # Отправляем шапку
    await message.bot.send_message(admin_chat_id, info_text, parse_mode="HTML")
    
    # Копируем само сообщение пользователя
    sent_msg = await message.copy_to(admin_chat_id)
    
    # Сохраняем маппинг в БД, чтобы знать, куда отвечать
    await save_message_mapping(
        session,
        admin_msg_id=sent_msg.message_id,
        user_tg_id=message.from_user.id,
        user_msg_id=message.message_id
    )
    
    await message.answer("✅ Ваше сообщение доставлено в поддержку. Ожидайте ответа.")
