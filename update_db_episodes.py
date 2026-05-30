import sqlite3

DB_PATH = 'database.db' # Make sure this points to the correct DB path used by sqlalchemy in config.py (usually 'database.db' or similar relative to root)

def main():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем, существует ли уже колонка (на случай повторного запуска)
        cursor.execute("PRAGMA table_info(episodes);")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'description' not in columns:
            print("Добавление колонки 'description' в таблицу 'episodes'...")
            cursor.execute("ALTER TABLE episodes ADD COLUMN description VARCHAR;")
            conn.commit()
            print("Успешно добавлено!")
        else:
            print("Колонка 'description' уже существует.")
            
    except Exception as e:
        print(f"Ошибка при обновлении базы данных: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
