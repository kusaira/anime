from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_mapping_by_admin_msg

router = Router()

@router.message(F.reply_to_message)
async def reply_to_user(message: Message, session: AsyncSession, admin_chat_ids: list):
    # Работаем только в чатах админов
    if message.chat.id not in admin_chat_ids:
        return
        
    admin_msg_id = message.reply_to_message.message_id
    
    # Ищем, кому принадлежит сообщение, на которое ответил админ
    mapping = await get_mapping_by_admin_msg(session, admin_msg_id)
    
    if not mapping:
        # Возможно это реплай на шапку, попробуем поискать (шапка обычно отправляется перед сообщением, 
        # но надежнее реплаить на само пересланное сообщение).
        # Если не нашли в БД - игнорируем или пишем ошибку.
        return
        
    try:
        # Копируем ответ админа пользователю (с reply на оригинальное сообщение юзера)
        await message.copy_to(
            chat_id=mapping.user_telegram_id,
            reply_to_message_id=mapping.user_message_id
        )
        await message.react([{"type": "emoji", "emoji": "👍"}])
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: пользователь заблокировал бота или удалил чат.\nКод: {e}")
