from datetime import datetime, timedelta

from config import EKATERINBURG_TZ

RUS_WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
RUS_MONTHS = [
    "янв", "фев", "мар", "апр", "мая", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек"
]


def format_datetime(dt: datetime, time_only: bool = False) -> str:
    """Форматирует datetime в удобочитаемый вид с учётом временной зоны Екатеринбурга"""
    dt = dt.astimezone(EKATERINBURG_TZ)
    if time_only:
        return dt.strftime("%H:%M")

    weekday = RUS_WEEKDAYS[dt.weekday()]
    month = RUS_MONTHS[dt.month - 1]
    return f"{weekday}, {dt.day} {month} {dt.year} в {dt.strftime('%H:%M')}"


def format_timedelta(td: timedelta) -> str:
    """Форматирует timedelta в понятный интервал"""
    hours, remainder = divmod(td.seconds, 3600)
    minutes = remainder // 60
    return f"{hours} ч {minutes} мин" if hours else f"{minutes} мин"
