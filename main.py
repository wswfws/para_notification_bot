# -*- coding: utf-8 -*-
import locale
from datetime import date

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from config import TOKEN, EKATERINBURG_TZ
from format import format_datetime
from handle_document import handle_document, restore_reminders, storage
from handler.show_reminders import show_reminders

# Устанавливаем русскую локаль для корректного отображения дат
try:
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, 'ru_RU')


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today_events = []

    # Загружаем расписание из хранилища
    events = storage.load_schedule(user_id)

    if not events:
        await update.message.reply_text("Ты ещё не загрузил расписание. Пришли .ics файл.")
        return

    # Сортируем события по времени начала
    events = sorted(events, key=lambda e: e.begin.datetime)

    current_date = date.today()
    for event in events:
        event_date = event.begin.datetime.astimezone(EKATERINBURG_TZ).date()
        if event_date == current_date:
            time_str = format_datetime(event.begin.datetime, time_only=True)
            location = event.location or "место не указано"
            today_events.append(f"🕒 {time_str} — {event.name} ({location})")

    if not today_events:
        await update.message.reply_text("Сегодня у тебя нет пар! 🎉")
    else:
        msg = "📅 Твои пары на сегодня:\n\n" + "\n".join(today_events)
        await update.message.reply_text(msg)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для напоминания о парах.\n"
        "Просто пришли мне файл с расписанием в формате .ics\n"
        f"Текущая временная зона: Екатеринбург (Asia/Yekaterinburg)\n\n"
        "Доступные команды:\n"
        "/today - пары на сегодня\n"
        "/reminders - показать все активные напоминания\n"
        "/notifications - управление уведомлениями"
    )


if __name__ == "__main__":
    builder = ApplicationBuilder()
    builder.token(TOKEN)
    builder.post_init(restore_reminders)

    app = builder.build()

    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reminders", show_reminders))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Бот запущен с временной зоной Asia/Yekaterinburg...")
    app.run_polling()
