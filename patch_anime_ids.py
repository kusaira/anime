import re

with open('handlers/admin.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace block 1: simple update_data
pattern1 = r'''    if not message\.text\.isdigit\(\):\n        return await message\.answer\("[^"]+"\)\n    await state\.update_data\(anime_id=int\(message\.text\)\)'''
replacement1 = '''    display_id = message.text.strip()
    anime = await get_anime_by_display_id(session, display_id)
    if not anime:
        return await message.answer("Аниме с таким ID не найдено. Попробуйте еще раз:")
    await state.update_data(anime_id=anime.id)'''
c = re.sub(pattern1, replacement1, c)

# Replace block 2: anime_id = int(message.text) with get_anime check
pattern2 = r'''    if not message\.text\.isdigit\(\):\n        return await message\.answer\("[^"]+"\)\n    anime_id = int\(message\.text\)\n    anime = await get_anime\(session, anime_id\)\n    if not anime:\n        return await message\.answer\("[^"]+"\)\n'''
replacement2 = '''    display_id = message.text.strip()
    anime = await get_anime_by_display_id(session, display_id)
    if not anime:
        return await message.answer("Аниме с таким ID не найдено. Попробуйте еще раз:")
    anime_id = anime.id\n'''
c = re.sub(pattern2, replacement2, c)

# Specific patches for any other missing waiting_for_anime_id handlers
# AdminDeleteVoiceover
pattern_del_vo = r'''    if not message\.text\.isdigit\(\):\n        return await message\.answer\("ID должен быть числом\."\)\n    anime_id = int\(message\.text\)'''
repl_del_vo = '''    display_id = message.text.strip()
    anime = await get_anime_by_display_id(session, display_id)
    if not anime:
        return await message.answer("Аниме не найдено.")
    anime_id = anime.id'''
c = re.sub(pattern_del_vo, repl_del_vo, c)

with open('handlers/admin.py', 'w', encoding='utf-8') as f:
    f.write(c)
