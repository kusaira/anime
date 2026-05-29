import sqlite3

def main():
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        print("Обнуляем подписки у всех пользователей...")
        cursor.execute("UPDATE users SET is_premium = 0, premium_until = NULL;")
        conn.commit()
        
        print(f"✅ Успешно обнулено подписок: {cursor.rowcount}")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
