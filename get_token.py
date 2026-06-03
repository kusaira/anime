from yoomoney import Authorize

# ВСТАВЬ СВОЙ CLIENT ID СЮДА (внутри кавычек):
CLIENT_ID = "ТВОЙ_CLIENT_ID_ЗДЕСЬ"

print("Запуск генерации токена ЮMoney...")
try:
    Authorize(
        client_id=CLIENT_ID,
        redirect_uri="https://google.com/",
        scopes=[
            "account-info", 
            "operation-history", 
            "operation-details", 
            "incoming-transfers", 
            "payment-p2p", 
            "payment-shop"
        ]
    )
except Exception as e:
    print(f"\nОшибка: {e}")
    print("Убедись, что ты правильно вставил Client ID и что библиотека yoomoney установлена.")
