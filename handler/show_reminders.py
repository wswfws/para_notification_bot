from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from bd.ScheduleStorage import ScheduleStorage
from config import EKATERINBURG_TZ
from format import format_datetime, format_timedelta

storage = ScheduleStorage()


async def show_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        # Получаем события пользователя из хранилища
        events = storage.load_schedule(user_id)

        if not events:
            await update.message.reply_text("У вас нет сохраненных событий")
            return

        reminders = []
        now = datetime.now(EKATERINBURG_TZ)

        for event in sorted(events, key=lambda e: e.begin.datetime):
            try:
                event_dt = event.begin.datetime.astimezone(EKATERINBURG_TZ)
                notify_time = event_dt - timedelta(minutes=5)
                time_left = notify_time - now

                # Показываем только будущие события
                if event_dt > now:
                    reminders.append(
                        f"📌 {event.name or 'Без названия'}\n"
                        f"⏰ Напоминание в: {format_datetime(notify_time)}\n"
                        f"🕒 Начало пары: {format_datetime(event_dt)}\n"
                        f"⏱ Осталось: {format_timedelta(time_left)}\n"
                        f"📍 {event.location or 'место не указано'}\n"
                    )
            except Exception as e:
                print(f"Ошибка обработки события: {e}")
                continue

        if not reminders:
            await update.message.reply_text("Активных напоминаний нет (все события уже прошли)")
        else:
            # Разбиваем вывод на части, если слишком много напоминаний
            for i in range(0, len(reminders), 5):
                chunk = reminders[i:i + 5]
                await update.message.reply_text(
                    "📋 Ваши предстоящие события:\n\n" +
                    "\n".join(chunk)
                )

    except Exception as e:
        print(f"Ошибка в show_reminders: {e}")
        await update.message.reply_text("Произошла ошибка при получении напоминаний")
