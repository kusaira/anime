import re

with open("handlers/admin.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add get_anime_by_index helper
helper = """
async def get_anime_by_index(session, index_str: str):
    if not index_str.isdigit(): return None
    idx = int(index_str) - 1
    if idx < 0: return None
    from database.requests import get_all_anime
    animes = await get_all_anime(session)
    if idx >= len(animes): return None
    return animes[idx]
"""

if "def get_anime_by_index" not in content:
    content = content.replace("router = Router()", "router = Router()\n" + helper)

# Replace "Введите ID аниме" with "Введите номер аниме из списка"
content = content.replace("Введите ID аниме", "Введите номер аниме из списка")

# Fix admin_list_anime display
old_list = """    text = "📚 <b>Список залитого аниме:</b>\\n\\n"
    for a in animes:
        folder = await get_folder_for_anime(session, a.id)
        folder_text = f" (Папка ID {folder.id})" if folder else " (Без папки)"
        text += f"ID {a.id}: {a.title}{folder_text}\\n"
"""
new_list = """    text = "📚 <b>Список залитого аниме:</b>\\n\\n"
    for idx, a in enumerate(animes, 1):
        folder = await get_folder_for_anime(session, a.id)
        folder_text = f" (Папка ID {folder.id})" if folder else ""
        star = " 🌟" if a.is_4k else ""
        text += f"{idx}. [ID: {a.id}] {a.title}{star}{folder_text}\\n"
"""
content = content.replace(old_list, new_list)

# Fix AdminAddEpisode.waiting_for_anime_id (it doesn't have session)
content = content.replace(
"""@router.message(AdminAddEpisode.waiting_for_anime_id)
async def add_episode_anime_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Номер должен быть числом. Попробуйте еще раз:")
    await state.update_data(anime_id=int(message.text))""",
"""@router.message(AdminAddEpisode.waiting_for_anime_id)
async def add_episode_anime_id(message: Message, state: FSMContext, session: AsyncSession):
    anime = await get_anime_by_index(session, message.text)
    if not anime:
        return await message.answer("Аниме с таким номером не найдено. Попробуйте еще раз:")
    await state.update_data(anime_id=anime.id)"""
)

# Fix AdminMassUpload.waiting_for_anime_id
content = content.replace(
"""@router.message(AdminMassUpload.waiting_for_anime_id)
async def mass_upload_anime_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    await state.update_data(anime_id=int(message.text))""",
"""@router.message(AdminMassUpload.waiting_for_anime_id)
async def mass_upload_anime_id(message: Message, state: FSMContext, session: AsyncSession):
    anime = await get_anime_by_index(session, message.text)
    if not anime:
        return await message.answer("Аниме с таким номером не найдено.")
    await state.update_data(anime_id=anime.id)"""
)

# Fix AdminLinkAnime.waiting_for_anime_id
content = content.replace(
"""@router.message(AdminLinkAnime.waiting_for_anime_id)
async def link_anime_id(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    
    anime_id = int(message.text)
    anime = await get_anime(session, anime_id)""",
"""@router.message(AdminLinkAnime.waiting_for_anime_id)
async def link_anime_id(message: Message, state: FSMContext, session: AsyncSession):
    anime = await get_anime_by_index(session, message.text)
    if not anime:
        return await message.answer("Аниме с таким номером не найдено.")
    anime_id = anime.id"""
)

# Fix AdminUnlinkAnime.waiting_for_anime_to_unlink
content = content.replace(
"""@router.message(AdminUnlinkAnime.waiting_for_anime_to_unlink)
async def unlink_anime_id(message: Message, state: FSMContext, session: AsyncSession):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
    
    anime_id = int(message.text)
    anime = await get_anime(session, anime_id)""",
"""@router.message(AdminUnlinkAnime.waiting_for_anime_to_unlink)
async def unlink_anime_id(message: Message, state: FSMContext, session: AsyncSession):
    anime = await get_anime_by_index(session, message.text)
    if not anime:
        return await message.answer("Аниме с таким номером не найдено.")
    anime_id = anime.id"""
)

# Generic block replacement for the others
pattern = r"""    if not message.text.isdigit\(\):
        return await message.answer\("ID должен быть числом."\)
    anime_id = int\(message.text\)
    anime = await get_anime\(session, anime_id\)
    if not anime:
        await message.answer\("Аниме с таким ID не найдено.", reply_markup=get_admin_menu\(\)\)
        return await state.clear\(\)"""
        
replacement = """    anime = await get_anime_by_index(session, message.text)
    if not anime:
        await message.answer("Аниме с таким номером не найдено.", reply_markup=get_admin_menu())
        return await state.clear()
    anime_id = anime.id"""

content = re.sub(pattern, replacement, content)

# Fix AdminListEpisodes.waiting_for_anime_id (it doesn't have the state.clear())
pattern2 = r"""    if not message.text.isdigit\(\):
        return await message.answer\("ID должен быть числом."\)
    
    anime_id = int\(message.text\)
    anime = await get_anime\(session, anime_id\)
    if not anime:
        return await message.answer\("Аниме с таким ID не найдено."\)"""

replacement2 = """    anime = await get_anime_by_index(session, message.text)
    if not anime:
        return await message.answer("Аниме с таким номером не найдено.")
    anime_id = anime.id"""

content = re.sub(pattern2, replacement2, content)


with open("handlers/admin.py", "w", encoding="utf-8") as f:
    f.write(content)
