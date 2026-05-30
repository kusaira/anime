import sqlite3

DB_PATH = 'database.db'

def main():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Создаем таблицу voiceovers
        print("Создание таблицы voiceovers...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voiceovers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anime_id INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                FOREIGN KEY(anime_id) REFERENCES anime(id) ON DELETE CASCADE
            )
        """)
        
        # 2. Проверяем, существует ли уже колонка voiceover_id в episodes
        cursor.execute("PRAGMA table_info(episodes);")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'voiceover_id' not in columns:
            print("Добавление колонки 'voiceover_id' в таблицу 'episodes'...")
            cursor.execute("ALTER TABLE episodes ADD COLUMN voiceover_id INTEGER REFERENCES voiceovers(id) ON DELETE CASCADE;")
            conn.commit()
            print("Успешно добавлено!")
        else:
            print("Колонка 'voiceover_id' уже существует.")
            
        # 3. Для всех уникальных anime_id в episodes создаем дефолтную озвучку "Оригинал" (если ее нет)
        print("Создание дефолтных озвучек для существующих аниме...")
        cursor.execute("SELECT DISTINCT anime_id FROM episodes WHERE voiceover_id IS NULL")
        anime_ids_with_null_voiceovers = [row[0] for row in cursor.fetchall()]
        
        for anime_id in anime_ids_with_null_voiceovers:
            # Ищем озвучку "Оригинал" для этого аниме
            cursor.execute("SELECT id FROM voiceovers WHERE anime_id = ? AND name = 'Оригинал'", (anime_id,))
            row = cursor.fetchone()
            if row:
                voiceover_id = row[0]
            else:
                cursor.execute("INSERT INTO voiceovers (anime_id, name) VALUES (?, 'Оригинал')", (anime_id,))
                voiceover_id = cursor.lastrowid
                
            # Обновляем все серии этого аниме, у которых нет озвучки
            cursor.execute("UPDATE episodes SET voiceover_id = ? WHERE anime_id = ? AND voiceover_id IS NULL", (voiceover_id, anime_id))
            
        conn.commit()
        print("Миграция озвучек завершена успешно!")
            
    except Exception as e:
        print(f"Ошибка при обновлении базы данных: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
