import tempfile
from datetime import timedelta, datetime
from typing import Dict, List

from telegram import Update, Document
from telegram.ext import ContextTypes
from ics import Calendar, Event

from bd.ScheduleStorage import ScheduleStorage
from config import EKATERINBURG_TZ
from send_reminder import check_and_send_reminders

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

        # Очищаем старые события для этого пользователя
        storage.clear_user_events(user_id)

        # Добавляем новые события
        events: List[Event] = []
        for event in cal.events:
            event_dt = event.begin.datetime.astimezone(EKATERINBURG_TZ)
            events.append(event)

            now = datetime.now(EKATERINBURG_TZ)
            notify_time = event_dt - timedelta(minutes=5)
            if notify_time > now:
                reminders_count += 1

        # Сохраняем обновленные события в хранилище
        storage.save_schedule(user_id, events)

        # Если это первый раз когда пользователь загружает расписание - запускаем фоновую задачу
        if not any(job.name == "reminder_checker" for job in context.job_queue.jobs()):
            context.job_queue.run_repeating(
                callback=check_and_send_reminders,
                interval=60,  # Каждую минуту
                first=0,
                name="reminder_checker"
            )

        await update.message.reply_text(
            f"✅ Расписание успешно загружено!\n"
            f"Всего пар: {len(events)}\n"
            f"Активных напоминаний: {reminders_count}\n"
            f"Используй /reminders для просмотра всех напоминаний"
        )


async def restore_reminders(application):
    """Запускает фоновую задачу для проверки напоминаний при старте бота"""
    if not any(job.name == "reminder_checker" for job in application.job_queue.jobs()):
        application.job_queue.run_repeating(
            callback=check_and_send_reminders,
            interval=60,
            first=0,
            name="reminder_checker"
        )