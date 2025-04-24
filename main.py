# -*- coding: utf-8 -*-
import locale
from datetime import datetime, date

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from config import TOKEN, EKATERINBURG_TZ
from format import format_datetime, format_timedelta
from handle_document import handle_document, restore_reminders, storage

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
        "/reminders - показать все активные напоминания"
    )


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
