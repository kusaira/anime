import os

handler_code = """
# --- Быстрое редактирование описания серии (/edit) ---
@router.message(Command("edit"))
async def quick_edit_episode(message: Message, state: FSMContext, session: AsyncSession):
    from config import ADMIN_IDS, SUPERADMIN_IDS
    if not is_admin(message.from_user.id): return
    data = await state.get_data()
    ep_id = data.get('viewing_episode_id')
    if not ep_id:
        return await message.answer("Сначала откройте какую-нибудь серию в каталоге или поиске, чтобы отредактировать её описание.")
        
    from database.requests import get_episode_by_id
    ep = await get_episode_by_id(session, ep_id)
    if not ep:
        return await message.answer("Ошибка: серия не найдена в базе.")
        
    desc = ep.description if ep.description else "Нет описания"
    await message.answer(f"Вы редактируете описание серии {ep.episode_number}.\\nТекущее описание:\\n<i>{desc}</i>\\n\\nВведите новое описание (или отправьте '-', чтобы очистить):", parse_mode="HTML", reply_markup=get_cancel_menu())
    await state.set_state(AdminQuickEditEpisode.waiting_for_new_description)

@router.message(AdminQuickEditEpisode.waiting_for_new_description)
async def process_quick_edit_episode(message: Message, state: FSMContext, session: AsyncSession):
    new_desc = message.text.strip()
    if new_desc == "-":
        new_desc = None
        
    data = await state.get_data()
    ep_id = data.get('viewing_episode_id')
    
    from database.requests import get_episode_by_id
    ep = await get_episode_by_id(session, ep_id)
    if ep:
        ep.description = new_desc
        await session.commit()
        await message.answer("Описание серии успешно обновлено! Новое описание будет видно при следующем открытии этой серии.", reply_markup=get_admin_menu())
    else:
        await message.answer("Ошибка сохранения.", reply_markup=get_admin_menu())
        
    await state.clear()
"""

with open("handlers/admin.py", "a", encoding="utf-8") as f:
    f.write(handler_code)
