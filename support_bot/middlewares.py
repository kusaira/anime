from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
import time

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit_seconds: int = 1):
        self.limit_seconds = limit_seconds
        self.users = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        current_time = time.time()
        
        # Разрешаем админам писать без лимитов (чтобы не блокировать ответы)
        if user_id == data.get("admin_chat_id"):
            return await handler(event, data)

        if user_id in self.users:
            last_time = self.users[user_id]
            if current_time - last_time < self.limit_seconds:
                return # Игнорируем сообщение (защита от флуда)

        self.users[user_id] = current_time
        return await handler(event, data)

class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool):
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        async with self.session_pool() as session:
            data['session'] = session
            return await handler(event, data)
