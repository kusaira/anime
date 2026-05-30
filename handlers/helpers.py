from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

async def delete_previous_menu(message_or_callback, state: FSMContext):
    data = await state.get_data()
    last_msg_id = data.get('last_menu_msg_id')
    if last_msg_id:
        try:
            await message_or_callback.bot.delete_message(
                chat_id=message_or_callback.from_user.id,
                message_id=last_msg_id
            )
        except Exception:
            pass
        await state.update_data(last_menu_msg_id=None)

async def save_menu_msg(msg_id: int, state: FSMContext):
    await state.update_data(last_menu_msg_id=msg_id)

async def delete_previous_video(message_or_callback, state: FSMContext):
    data = await state.get_data()
    last_msg_id = data.get('last_video_msg_id')
    if last_msg_id:
        try:
            await message_or_callback.bot.delete_message(
                chat_id=message_or_callback.from_user.id,
                message_id=last_msg_id
            )
        except Exception:
            pass
        await state.update_data(last_video_msg_id=None)

async def save_video_msg(msg_id: int, state: FSMContext):
    await state.update_data(last_video_msg_id=msg_id)
