from telegram.ext import ContextTypes


async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    text = (
        f"⏰ Скоро пара!\n"
        f"📚 {job.data['event_name']}\n"
        f"📍 {job.data['location'] or 'место не указано'}\n"
        f"🕒 Начало в {job.data['event_time']}\n"
    )
    try:
        await context.bot.send_message(chat_id=job.user_id, text=text)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")
