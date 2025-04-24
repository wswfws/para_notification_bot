from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from config import EKATERINBURG_TZ
from format import format_datetime, format_timedelta


async def show_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        # Ищем все задачи пользователя
        user_jobs = [job for job in context.job_queue.jobs() if str(user_id) in job.name]

        if not user_jobs:
            await update.message.reply_text("У вас нет активных напоминаний")
            return

        reminders = []
        now = datetime.now(EKATERINBURG_TZ)

        for job in sorted(user_jobs, key=lambda j: j.data["event_time"]):
            try:
                event_time = job.data["event_time"]
                notify_time = job.data["notify_time"]
                time_left = notify_time - now

                if time_left.total_seconds() > 0:
                    reminders.append(
                        f"📌 {job.data.get('event_name', 'Без названия')}\n"
                        f"⏰ Напоминание в: {format_datetime(notify_time)}\n"
                        f"🕒 Начало пары: {format_datetime(event_time)}\n"
                        f"⏱ Осталось: {format_timedelta(time_left)}\n"
                        f"📍 {job.data.get('location', 'место не указано')}\n"
                    )
            except Exception as e:
                print(f"Ошибка обработки напоминания: {e}")
                continue

        if not reminders:
            await update.message.reply_text("Активных напоминаний нет или они уже сработали")
        else:
            # Разбиваем вывод на части, если слишком много напоминаний
            for i in range(0, len(reminders), 5):
                chunk = reminders[i:i + 5]
                await update.message.reply_text(
                    "📋 Ваши активные напоминания:\n\n" +
                    "\n".join(chunk)
                )

    except Exception as e:
        print(f"Ошибка в show_reminders: {e}")
        await update.message.reply_text("Произошла ошибка при получении напоминаний")