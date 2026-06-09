import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5):
        """
        :param rate_limit: минимальное время между запросами в секундах
        """
        self.rate_limit = rate_limit
        self.users: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if user_id is not None:
            now = time.time()
            last_time = self.users.get(user_id, 0)
            
            if now - last_time < self.rate_limit:
                # Запрос отклоняется, если пришел слишком быстро
                if isinstance(event, CallbackQuery):
                    try:
                        await event.answer("Подождите немного...", show_alert=False)
                    except:
                        pass
                return
                
            self.users[user_id] = now
            
            # Простая очистка кэша, чтобы не росла память
            if len(self.users) > 10000:
                self.users.clear()
            
        return await handler(event, data)
