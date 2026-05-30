import re

with open("handlers/admin.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update imports
content = content.replace("get_anime_in_folder, get_episode", "get_anime_in_folder, get_episode, get_anime_by_display_id")

# 2. Update list displays
content = content.replace('f"ID {a.id}: {a.title}', 'f"ID {a.display_id}: {a.title}')
content = content.replace('f"{a.id}. {a.title}', 'f"{a.display_id}. {a.title}')

# 3. Update input handlers
# Old logic:
# if not message.text.isdigit(): return await message.answer("ID должен быть числом.")
# anime_id = int(message.text)
# anime = await get_anime(session, anime_id)

pattern = r"""    if not message.text\.isdigit\(\):
        return await message\.answer\("ID должен быть числом\.(?: Попробуйте еще раз:)?"\)
(?:    \n)?    anime_id = int\(message\.text\)
    anime = await get_anime\(session, anime_id\)"""

replacement = """    display_id = message.text.strip()
    anime = await get_anime_by_display_id(session, display_id)"""

content = re.sub(pattern, replacement, content)

# 4. AdminAddAnime workflow
content = content.replace(
"""@router.message(AdminAddAnime.waiting_for_title)
async def add_anime_title(message: Message, state: FSMContext, session: AsyncSession):
    title = message.text.strip()
    await state.update_data(title=title)
    await message.answer("Введите описание аниме:")
    await state.set_state(AdminAddAnime.waiting_for_description)""",
"""@router.message(AdminAddAnime.waiting_for_title)
async def add_anime_title(message: Message, state: FSMContext):
    title = message.text.strip()
    await state.update_data(title=title)
    await message.answer("Введите кастомный ID для этого аниме (например 4_1, 4_2 или просто число):", reply_markup=get_cancel_menu())
    await state.set_state(AdminAddAnime.waiting_for_display_id)

@router.message(AdminAddAnime.waiting_for_display_id)
async def add_anime_display_id(message: Message, state: FSMContext, session: AsyncSession):
    display_id = message.text.strip()
    existing = await get_anime_by_display_id(session, display_id)
    if existing:
        return await message.answer("Аниме с таким кастомным ID уже существует. Введите другой ID:")
    await state.update_data(display_id=display_id)
    await message.answer("Введите описание аниме:")
    await state.set_state(AdminAddAnime.waiting_for_description)"""
)

# 5. In add_anime_finish, pass display_id
content = content.replace(
"""    await add_anime(session, data['title'], data['description'], data['photo_file_id'], is_4k)""",
"""    await add_anime(session, data['title'], data['description'], data['photo_file_id'], is_4k, data.get('display_id'))"""
)

with open("handlers/admin.py", "w", encoding="utf-8") as f:
    f.write(content)
