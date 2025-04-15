import tempfile
from datetime import timedelta, datetime

from telegram import Update, Document
from telegram.ext import ContextTypes
from ics import Calendar

from config import EKATERINBURG_TZ
from send_reminder import send_reminder

user_schedules = {}

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc: Document = update.message.document
    if not doc.file_name.endswith(".ics"):
        await update.message.reply_text("Пожалуйста, пришли файл с расширением .ics")
        return

    file = await context.bot.get_file(doc.file_id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ics") as temp_file:
        await file.download_to_drive(temp_file.name)

        with open(temp_file.name, 'r', encoding='utf-8') as f:
            cal = Calendar(f.read())

        user_id = update.effective_user.id
        user_schedules[user_id] = []
        reminders_count = 0

        # Удаляем старые напоминания для этого пользователя
        current_jobs = [job for job in context.job_queue.jobs() if str(user_id) in job.name]
        for job in current_jobs:
            job.schedule_removal()

        for event in cal.events:
            event_dt = event.begin.datetime.astimezone(EKATERINBURG_TZ)
            user_schedules[user_id].append(event)

            notify_time = event_dt - timedelta(minutes=5)
            now = datetime.now(EKATERINBURG_TZ)

            if notify_time > now:
                context.job_queue.run_once(
                    callback=send_reminder,
                    when=(notify_time - now),
                    user_id=user_id,
                    data={
                        "event_name": event.name,
                        "location": event.location,
                        "event_time": event_dt,  # Сохраняем datetime объект
                        "notify_time": notify_time  # Время напоминания
                    },
                    name=f"{user_id}_{event.name}_{event_dt.timestamp()}"
                )
                reminders_count += 1

        await update.message.reply_text(
            f"✅ Расписание успешно загружено!\n"
            f"Всего пар: {len(user_schedules[user_id])}\n"
            f"Активных напоминаний: {reminders_count}\n"
            f"Используй /reminders для просмотра всех напоминаний"
        )