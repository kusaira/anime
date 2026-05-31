import re

with open("handlers/admin.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Remove get_anime_by_index helper
helper_pattern = r"async def get_anime_by_index\(session, index_str: str\):\n(?:    .*\n)*?    return animes\[idx\]\n"
content = re.sub(helper_pattern, "", content)

# 2. Revert strings
content = content.replace("Введите номер аниме из списка", "Введите ID аниме")
content = content.replace("Аниме с таким номером не найдено", "Аниме с таким ID не найдено")
content = content.replace("Номер должен быть числом", "ID должен быть числом")

# 3. Revert admin_list_anime
old_list = """    text = "📚 <b>Список залитого аниме:</b>\\n\\n"
    for idx, a in enumerate(animes, 1):
        folder = await get_folder_for_anime(session, a.id)
        folder_text = f" (Папка ID {folder.id})" if folder else ""
        star = " 🌟" if a.is_4k else ""
        text += f"{idx}. [ID: {a.id}] {a.title}{star}{folder_text}\\n"
"""
new_list = """    text = "📚 <b>Список залитого аниме:</b>\\n\\n"
    for a in animes:
        folder = await get_folder_for_anime(session, a.id)
        folder_text = f" (Папка ID {folder.id})" if folder else " (Без папки)"
        star = " 🌟" if getattr(a, 'is_4k', False) else ""
        text += f"ID {a.id}: {a.title}{star}{folder_text}\\n"
"""
if old_list in content:
    content = content.replace(old_list, new_list)
else:
    print("Warning: old_list not found")

# 4. Fix AdminAddEpisode
content = content.replace(
"""@router.message(AdminAddEpisode.waiting_for_anime_id)
async def add_episode_anime_id(message: Message, state: FSMContext, session: AsyncSession):
    anime = await get_anime_by_index(session, message.text)
    if not anime:
        return await message.answer("Аниме с таким ID не найдено. Попробуйте еще раз:")
    await state.update_data(anime_id=anime.id)""",
"""@router.message(AdminAddEpisode.waiting_for_anime_id)
async def add_episode_anime_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом. Попробуйте еще раз:")
    await state.update_data(anime_id=int(message.text))"""
)

# 5. Fix AdminMassUpload
content = content.replace(
"""@router.message(AdminMassUpload.waiting_for_anime_id)
async def mass_upload_anime_id(message: Message, state: FSMContext, session: AsyncSession):
    anime = await get_anime_by_index(session, message.text)
    if not anime:
        return await message.answer("Аниме с таким ID не найдено.")
    await state.update_data(anime_id=anime.id)""",
"""@router.message(AdminMassUpload.waiting_for_anime_id)
async def mass_upload_anime_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    await state.update_data(anime_id=int(message.text))"""
)

# 6. Fix generic blocks
pattern = r"""    anime = await get_anime_by_index\(session, message.text\)
    if not anime:
        await message.answer\("Аниме с таким ID не найдено.", reply_markup=get_admin_menu\(\)\)
        return await state.clear\(\)
    anime_id = anime.id"""

replacement = """    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    anime_id = int(message.text)
    anime = await get_anime(session, anime_id)
    if not anime:
        await message.answer("Аниме с таким ID не найдено.", reply_markup=get_admin_menu())
        return await state.clear()"""

content = re.sub(pattern, replacement, content)

# 7. Fix AdminListEpisodes and Link/Unlink (which don't have state.clear())
pattern2 = r"""    anime = await get_anime_by_index\(session, message.text\)
    if not anime:
        return await message.answer\("Аниме с таким ID не найдено."\)
    anime_id = anime.id"""

replacement2 = """    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    
    anime_id = int(message.text)
    anime = await get_anime(session, anime_id)
    if not anime:
        return await message.answer("Аниме с таким ID не найдено.")"""

content = re.sub(pattern2, replacement2, content)

with open("handlers/admin.py", "w", encoding="utf-8") as f:
    f.write(content)
