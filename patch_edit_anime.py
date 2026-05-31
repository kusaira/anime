import re

with open("handlers/admin.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace transition from edit_anime_id
content = content.replace(
"""    await state.update_data(anime_id=anime_id)
    await message.answer(f"Текущее название: <b>{anime.title}</b>\\nВведите новое название (или отправьте '-', чтобы оставить текущее):", parse_mode="HTML")
    await state.set_state(AdminEditAnime.waiting_for_new_title)""",
"""    await state.update_data(anime_id=anime_id)
    await message.answer(f"Текущий кастомный ID: <b>{anime.display_id}</b>\\nВведите новый кастомный ID (или отправьте '-', чтобы оставить текущий):", parse_mode="HTML")
    await state.set_state(AdminEditAnime.waiting_for_new_display_id)"""
)

# Insert the new handler
new_handler = """
@router.message(AdminEditAnime.waiting_for_new_display_id)
async def edit_anime_display_id(message: Message, state: FSMContext, session: AsyncSession):
    new_id = message.text.strip()
    if new_id != "-":
        existing = await get_anime_by_display_id(session, new_id)
        if existing:
            return await message.answer("Аниме с таким кастомным ID уже существует. Введите другой ID (или '-' чтобы пропустить):")
        await state.update_data(new_display_id=new_id)
    
    data = await state.get_data()
    anime = await get_anime(session, data['anime_id'])
    await message.answer(f"Текущее название: <b>{anime.title}</b>\\nВведите новое название (или отправьте '-', чтобы оставить текущее):", parse_mode="HTML")
    await state.set_state(AdminEditAnime.waiting_for_new_title)
"""

content = content.replace(
"""@router.message(AdminEditAnime.waiting_for_new_title)""",
new_handler + "\n@router.message(AdminEditAnime.waiting_for_new_title)"
)

# Update the final saving step in edit_anime_desc
content = content.replace(
"""    title = data.get('new_title')
    
    success = await update_anime(session, anime_id, title=title, description=desc)""",
"""    title = data.get('new_title')
    display_id = data.get('new_display_id')
    
    success = await update_anime(session, anime_id, title=title, description=desc, display_id=display_id)"""
)

with open("handlers/admin.py", "w", encoding="utf-8") as f:
    f.write(content)
