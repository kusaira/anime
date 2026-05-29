import asyncio
import os
from aiogram import Bot
from aiogram.types import FSInputFile
from dotenv import load_dotenv
from database.engine import AsyncSessionLocal, init_db
from database.models import Anime, Episode, Folder
from sqlalchemy import select

load_dotenv()

OLD_TOKEN = os.getenv("BOT_TOKEN")
NEW_TOKEN = "8601703607:AAH0pqn6AI7pOIDy9qeGcjZmO_Dgr9h0sOg"
DEST_CHAT_ID = 5551306116 # Ваш ID (Сюда будут скидываться файлы без звука уведомлений)

async def main():
    print("Инициализация базы данных...")
    await init_db()
    
    old_bot = Bot(token=OLD_TOKEN)
    new_bot = Bot(token=NEW_TOKEN)
    
    async with AsyncSessionLocal() as session:
        # 1. Миграция аниме (постеры)
        print("\n--- Миграция Аниме ---")
        animes = (await session.execute(select(Anime))).scalars().all()
        for anime in animes:
            try:
                print(f"Скачиваем постер для аниме ID {anime.id}...")
                await old_bot.download(anime.photo_file_id, destination="temp_poster.jpg")
                
                print(f"Загружаем постер для аниме ID {anime.id} новым ботом...")
                msg = await new_bot.send_photo(chat_id=DEST_CHAT_ID, photo=FSInputFile("temp_poster.jpg"), disable_notification=True)
                
                anime.photo_file_id = msg.photo[-1].file_id
                await session.commit()
                print(f"✅ Аниме ID {anime.id} обновлено.")
            except Exception as e:
                print(f"❌ Ошибка с аниме ID {anime.id}: {e}")
                
        # 2. Миграция папок (постеры)
        print("\n--- Миграция Папок ---")
        folders = (await session.execute(select(Folder))).scalars().all()
        for folder in folders:
            try:
                print(f"Скачиваем постер для папки ID {folder.id}...")
                await old_bot.download(folder.photo_file_id, destination="temp_poster.jpg")
                
                print(f"Загружаем постер для папки ID {folder.id} новым ботом...")
                msg = await new_bot.send_photo(chat_id=DEST_CHAT_ID, photo=FSInputFile("temp_poster.jpg"), disable_notification=True)
                
                folder.photo_file_id = msg.photo[-1].file_id
                await session.commit()
                print(f"✅ Папка ID {folder.id} обновлена.")
            except Exception as e:
                print(f"❌ Ошибка с папкой ID {folder.id}: {e}")

        # 3. Миграция серий (видео)
        print("\n--- Миграция Серий ---")
        episodes = (await session.execute(select(Episode))).scalars().all()
        for ep in episodes:
            try:
                print(f"Скачиваем видео для серии ID {ep.id} (Эпизод {ep.episode_number})...")
                await old_bot.download(ep.tg_file_id, destination="temp_video.mp4")
                
                print(f"Загружаем видео для серии ID {ep.id} новым ботом (может занять время)...")
                msg = await new_bot.send_video(chat_id=DEST_CHAT_ID, video=FSInputFile("temp_video.mp4"), disable_notification=True)
                
                ep.tg_file_id = msg.video.file_id
                await session.commit()
                print(f"✅ Серия ID {ep.id} обновлена.")
            except Exception as e:
                print(f"❌ Ошибка с серией ID {ep.id}: {e}")
                
    await old_bot.session.close()
    await new_bot.session.close()
    if os.path.exists("temp_poster.jpg"): os.remove("temp_poster.jpg")
    if os.path.exists("temp_video.mp4"): os.remove("temp_video.mp4")
    
    print("\n🎉 Миграция успешно завершена! Все новые ID сохранены в базе данных.")

if __name__ == "__main__":
    asyncio.run(main())
