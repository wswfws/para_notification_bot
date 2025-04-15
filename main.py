import os
from telegram import Update, Document
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from ics import Calendar
from datetime import datetime, timedelta, date
import tempfile

from config import TOKEN

user_schedules = {}


# Команда /сегодня — показать пары на сегодня
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today_events = []

    if user_id not in user_schedules:
        await update.message.reply_text("Ты ещё не загрузил расписание. Пришли .ics файл.")
        return

    events = sorted(user_schedules[user_id], key=lambda e: e.begin.datetime)

    for event in events:
        event_date = event.begin.datetime.astimezone().date()
        if event_date == date.today():
            time_str = event.begin.to('local').format('HH:mm')
            today_events.append(f"🕒 {time_str} — {event.name} ({event.location or 'место не указано'})")

    if not today_events:
        await update.message.reply_text("Сегодня у тебя нет пар! 🎉")
    else:
        msg = "📅 Твои пары на сегодня:\n\n" + "\n".join(today_events)
        await update.message.reply_text(msg)


# Обработка старта
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли мне .ics файл с расписанием пар.")


# Обработка ics файла
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

        for event in cal.events:
            user_schedules[user_id].append(event)

            # Уведомление за 5 минут до начала
            notify_time = event.begin.datetime - timedelta(minutes=5)

            if notify_time > datetime.now(notify_time.tzinfo):
                context.job_queue.run_once(
                    callback=send_reminder,
                    when=notify_time,
                    user_id=user_id,
                    data={
                        "event_name": event.name,
                        "location": event.location,
                        "start_time": event.begin.to('local').format('HH:mm')
                    },
                )

        await update.message.reply_text(f"Успешно загружено {len(user_schedules[user_id])} пар!")


# Отправка уведомления
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    text = (
        f"⏰ Скоро пара!\n"
        f"📚 {job.data['event_name']}\n"
        f"📍 {job.data['location'] or 'место не указано'}\n"
        f"🕒 Начало в {job.data['start_time']}"
    )
    try:
        await context.bot.send_message(chat_id=job.user_id, text=text)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")


# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Бот запущен...")
    app.run_polling()