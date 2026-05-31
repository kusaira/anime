import sys

with open("handlers/admin.py", "r", encoding="utf-8") as f:
    c = f.read()

# 1. Anime list with folder
c = c.replace(
    'text += f"ID {a.display_id}: {a.title}{star}{folder_text}\\n"',
    'text += f"<code>{a.display_id}</code>. {a.title}{star}{folder_text}\\n"'
)

# 2. Anime list without folder (used in add_episode, delete_anime, edit_anime etc)
c = c.replace(
    'text = "Доступные аниме:\\n" + "\\n".join([f"ID {a.display_id}: {a.title}{\' 🌟\' if getattr(a, \'is_4k\', False) else \'\'}" for a in animes])',
    'text = "Доступные аниме:\\n" + "\\n".join([f"<code>{a.display_id}</code>. {a.title}{\' 🌟\' if getattr(a, \'is_4k\', False) else \'\'}" for a in animes])'
)

# 3. Episode list
c = c.replace(
    'text += f"Уникальный ID {ep.id} — Серия {ep.episode_number}\\n"',
    'text += f"<code>{ep.id}</code>. Серия {ep.episode_number}\\n"'
)

# 4. Voiceover list
c = c.replace(
    'text += f"ID: {vo.id} - {vo.name}\\n"',
    'text += f"<code>{vo.id}</code>. {vo.name}\\n"'
)

# 5. Folder list
c = c.replace(
    'text = "Доступные папки:\\n" + "\\n".join([f"{f.id}. {f.title}" for f in folders])',
    'text = "Доступные папки:\\n" + "\\n".join([f"<code>{f.id}</code>. {f.title}" for f in folders])'
)
c = c.replace(
    'text = "Выберите папку для удаления:\\n" + "\\n".join([f"ID: {f.id} - {f.title}" for f in folders])',
    'text = "Выберите папку для удаления:\\n" + "\\n".join([f"<code>{f.id}</code>. {f.title}" for f in folders])'
)
c = c.replace(
    'text = "Выберите папку для редактирования:\\n" + "\\n".join([f"ID: {f.id} - {f.title}" for f in folders])',
    'text = "Выберите папку для редактирования:\\n" + "\\n".join([f"<code>{f.id}</code>. {f.title}" for f in folders])'
)

# 6. Folder label in anime list
c = c.replace(
    'folder_text = f" (Папка ID {folder.id})" if folder else " (Без папки)"',
    'folder_text = f" (Папка <code>{folder.id}</code>)" if folder else " (Без папки)"'
)

with open("handlers/admin.py", "w", encoding="utf-8") as f:
    f.write(c)

print("Done.")
