import tempfile
from datetime import timedelta, datetime
from typing import Dict, List

from telegram import Update, Document
from telegram.ext import ContextTypes
from ics import Calendar, Event

from bd.ScheduleStorage import ScheduleStorage
from config import EKATERINBURG_TZ
from send_reminder import send_reminder

# Инициализация хранилища
storage = ScheduleStorage()

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
        reminders_count = 0

        # Удаляем старые напоминания для этого пользователя
        current_jobs = [job for job in context.job_queue.jobs() if str(user_id) in job.name]
        for job in current_jobs:
            job.schedule_removal()

        # Загружаем события из хранилища
        events: List[Event] = storage.load_schedule(user_id)
        events.clear()  # Очищаем старые события

        for event in cal.events:
            event_dt = event.begin.datetime.astimezone(EKATERINBURG_TZ)
            events.append(event)  # Добавляем в список событий

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
                        "event_time": event_dt,
                        "notify_time": notify_time
                    },
                    name=f"{user_id}_{event.name}_{event_dt.timestamp()}"
                )
                reminders_count += 1

        # Сохраняем обновленные события в хранилище
        storage.save_schedule(user_id, events)

        await update.message.reply_text(
            f"✅ Расписание успешно загружено!\n"
            f"Всего пар: {len(events)}\n"
            f"Активных напоминаний: {reminders_count}\n"
            f"Используй /reminders для просмотра всех напоминаний"
        )


async def restore_reminders(application):
    """Восстанавливает все активные напоминания при запуске бота"""
    for user_id, events in storage.get_all_schedules().items():
        for event in events:
            event_dt = event.begin.datetime.astimezone(EKATERINBURG_TZ)
            notify_time = event_dt - timedelta(minutes=5)
            now = datetime.now(EKATERINBURG_TZ)

            if notify_time > now:
                application.job_queue.run_once(
                    callback=send_reminder,
                    when=(notify_time - now),
                    user_id=user_id,
                    data={
                        "event_name": event.name,
                        "location": event.location,
                        "event_time": event_dt,
                        "notify_time": notify_time
                    },
                    name=f"{user_id}_{event.name}_{event_dt.timestamp()}"
                )