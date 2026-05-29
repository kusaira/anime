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
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
