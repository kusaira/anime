import re

handler_code = """
@router.message(F.text == "📥 Экспорт базы (CSV)")
async def admin_export_csv(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id): return
    animes = await get_all_anime(session)
    if not animes:
        return await message.answer("База данных аниме пуста.")
        
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["ID", "Название", "Качество", "ID Папки"])
    
    for a in animes:
        folder = await get_folder_for_anime(session, a.id)
        folder_id = folder.id if folder else "Без папки"
        quality = "4K" if getattr(a, 'is_4k', False) else "1080p"
        
        # Записываем display_id если он есть, иначе обычный id
        anime_id = getattr(a, 'display_id', a.id) or a.id
        writer.writerow([anime_id, a.title, quality, folder_id])
        
    csv_bytes = output.getvalue().encode('utf-8-sig') # utf-8-sig for excel compatibility
    file = BufferedInputFile(csv_bytes, filename="anime_database.csv")
    
    await message.answer_document(
        document=file,
        caption="📥 <b>Экспорт базы данных аниме</b>\\n\\nФайл в формате CSV. Отлично открывается в Excel или Google Sheets (разделитель - точка с запятой).",
        parse_mode="HTML"
    )

"""

with open("handlers/admin.py", "r", encoding="utf-8") as f:
    content = f.read()

# Insert before @router.message(F.text == "👥 Список пользователей")
content = content.replace(
    '@router.message(F.text == "👥 Список пользователей")',
    handler_code + '@router.message(F.text == "👥 Список пользователей")'
)

with open("handlers/admin.py", "w", encoding="utf-8") as f:
    f.write(content)
