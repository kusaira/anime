import sqlite3

def main():
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        print("Добавляем колонку is_4k в таблицу anime...")
        try:
            cursor.execute("ALTER TABLE anime ADD COLUMN is_4k BOOLEAN DEFAULT 0;")
            conn.commit()
            print("✅ Колонка is_4k успешно добавлена!")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✅ Колонка is_4k уже существует.")
            else:
                print(f"❌ Ошибка SQL: {e}")
                
        print("Создаем таблицу watched_episodes...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watched_episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                anime_id INTEGER NOT NULL,
                episode_number INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(anime_id) REFERENCES anime(id) ON DELETE CASCADE
            );
        """)
        conn.commit()
        print("✅ Таблица watched_episodes готова!")
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
