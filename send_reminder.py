from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from ics import Event
from config import EKATERINBURG_TZ
from bd.ScheduleStorage import ScheduleStorage

storage = ScheduleStorage()


async def check_and_send_reminders(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(EKATERINBURG_TZ)

    for user_id, events in storage.get_all_schedules().items():
        for event in events:
            event_dt = event.begin.datetime.astimezone(EKATERINBURG_TZ)
            notify_time = event_dt - timedelta(minutes=5)

            # Проверяем нужно ли отправить напоминание сейчас
            if notify_time <= now < event_dt:
                # Проверяем не было ли уже отправлено напоминание
                last_notified = storage.get_last_notified(user_id, event.name, event_dt)
                if last_notified is None or last_notified < notify_time:
                    text = (
                        f"⏰ Скоро пара!\n"
                        f"📚 {event.name}\n"
                        f"📍 {event.location or 'место не указано'}\n"
                        f"🕒 Начало в {event_dt.strftime('%H:%M')}\n"
                    )
                    try:
                        await context.bot.send_message(chat_id=user_id, text=text)
                        # Обновляем время последнего уведомления
                        storage.update_last_notified(user_id, event.name, event_dt, now)
                    except Exception as e:
                        print(f"Ошибка отправки сообщения: {e}")