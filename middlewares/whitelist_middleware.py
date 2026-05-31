import json
import os
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from config import ADMIN_IDS, SUPERADMIN_IDS

def is_whitelist_enabled():
    if not os.path.exists('whitelist_config.json'):
        return False
    try:
        with open('whitelist_config.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('enabled', False)
    except:
        return False

class WhitelistMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Extract user_id from the event
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        elif hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id
            
        if user_id and is_whitelist_enabled():
            if user_id not in ADMIN_IDS and user_id not in SUPERADMIN_IDS:
                if isinstance(event, Message):
                    await event.answer("⚠️ <b>Техническое обслуживание</b>\n\nБот временно недоступен в связи с техническими работами по улучшению базы данных. Пожалуйста, попробуйте позже.", parse_mode="HTML")
                elif isinstance(event, CallbackQuery):
                    await event.answer("Техническое обслуживание. Попробуйте позже.", show_alert=True)
                return # Block execution
                
        return await handler(event, data)
