from datetime import datetime, timedelta

import pytz
from ics import Calendar, Event

# Часовой пояс (замени, если нужен свой)
tz = pytz.timezone("Europe/Moscow")

calendar = Calendar()

now = datetime.now(tz)

# 🔹 Пары на сегодня
for i in range(3):
    start = now.replace(hour=9 + i * 2, minute=0, second=0, microsecond=0)
    event = Event()
    event.name = f"Пара сегодня #{i + 1}"
    event.begin = start
    event.duration = timedelta(hours=1, minutes=30)
    event.location = f"Аудитория {100 + i}"
    calendar.events.add(event)

# 🔹 быстрый тест напоминаний
for i in range(10):
    start = now + timedelta(minutes=5, seconds=10 * i + 10)
    event = Event()
    event.name = f"Тестовая пара #{i + 1} ({start.isoformat()})"
    event.begin = start
    event.duration = timedelta(minutes=30)
    event.location = f"Тест {200 + i}"
    calendar.events.add(event)

# 🔹 20 пар на завтра
tomorrow = (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
for i in range(20):
    start = tomorrow + timedelta(minutes=90 * i)
    event = Event()
    event.name = f"Пара завтра #{i + 1}"
    event.begin = start
    event.duration = timedelta(minutes=90)
    event.location = f"Аудитория {300 + i}"
    calendar.events.add(event)

# 💾 Сохраняем в файл
with open("test_schedule.ics", "w", encoding="utf-8") as f:
    f.writelines(calendar)
