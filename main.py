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
from pytz import timezone
import locale

from config import TOKEN

# Устанавливаем русскую локаль для корректного отображения дат
try:
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, 'ru_RU')

user_schedules = {}
EKATERINBURG_TZ = timezone('Asia/Yekaterinburg')  # Временная зона Екатеринбурга


def format_datetime(dt: datetime, time_only: bool = False) -> str:
    """Форматирует datetime в удобочитаемый вид с учётом временной зоны Екатеринбурга"""
    dt = dt.astimezone(EKATERINBURG_TZ)
    if time_only:
        return dt.strftime("%H:%M")
    return dt.strftime("%a, %d %b %Y в %H:%M")


def format_timedelta(td: timedelta) -> str:
    """Форматирует timedelta в понятный интервал"""
    hours, remainder = divmod(td.seconds, 3600)
    minutes = remainder // 60
    return f"{hours} ч {minutes} мин" if hours else f"{minutes} мин"


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today_events = []

    if user_id not in user_schedules:
        await update.message.reply_text("Ты ещё не загрузил расписание. Пришли .ics файл.")
        return

    events = sorted(user_schedules[user_id], key=lambda e: e.begin.datetime)

    for event in events:
        event_date = event.begin.datetime.astimezone(EKATERINBURG_TZ).date()
        if event_date == date.today():
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


async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    text = (
        f"⏰ Скоро пара!\n"
        f"📚 {job.data['event_name']}\n"
        f"📍 {job.data['location'] or 'место не указано'}\n"
        f"🕒 Начало в {job.data['start_time']}\n"
        f"📅 {job.data['full_time']}"
    )
    try:
        await context.bot.send_message(chat_id=job.user_id, text=text)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")


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
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reminders", show_reminders))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Бот запущен с временной зоной Asia/Yekaterinburg...")
    app.run_polling()