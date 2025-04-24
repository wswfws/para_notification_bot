import os

from pytz import timezone

# Получаем токен из переменной окружения
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Проверяем, что токен был установлен
if TOKEN is None:
    print("Ошибка: Переменная окружения TELEGRAM_BOT_TOKEN не установлена.")
    exit()  # Завершаем выполнение программы, если токен отсутствует

# Получаем часовой пояс из переменной окружения (если она задана)
EKATERINBURG_TZ = os.environ.get("TELEGRAM_TZ")

if EKATERINBURG_TZ:
    try:
        EKATERINBURG_TZ = timezone(EKATERINBURG_TZ)  # Проверяем, что timezone валидный
        print(f"Часовой пояс установлен: {EKATERINBURG_TZ}")
    except Exception as e:
        print(f"Ошибка при установке часового пояса: {e}. Используется UTC.")
        EKATERINBURG_TZ = None  # Устанавливаем в None, чтобы использовать UTC по умолчанию
else:
    print("Часовой пояс не установлен. Используется UTC.")

# Теперь TOKEN и EKATERINBURG_TZ содержат значения из переменных окружения или используются значения по умолчанию.
print(f"Telegram Token: {TOKEN}")
print(f"Ekaterinburg Timezone: {EKATERINBURG_TZ}")
