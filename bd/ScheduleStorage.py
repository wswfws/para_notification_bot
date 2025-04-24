import sqlite3
import pickle
from typing import List, Optional
from datetime import datetime
from ics import Event


class ScheduleStorage:
    def __init__(self, db_path: str = 'schedules.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        with self.conn:
            # Таблица для хранения расписаний
            self.conn.execute('''CREATE TABLE IF NOT EXISTS schedules
                                 (
                                     user_id INTEGER PRIMARY KEY,
                                     events  BLOB
                                 )''')

            # Таблица для хранения информации о последних уведомлениях
            self.conn.execute('''CREATE TABLE IF NOT EXISTS notifications
                                 (
                                     user_id       INTEGER,
                                     event_name    TEXT,
                                     event_time    TEXT,
                                     last_notified TEXT,
                                     PRIMARY KEY (user_id, event_name, event_time)
                                 )''')

    def save_schedule(self, user_id: int, events: List[Event]):
        """Сохраняет список событий для пользователя"""
        with self.conn:
            self.conn.execute(
                "REPLACE INTO schedules VALUES (?, ?)",
                (user_id, pickle.dumps(events))
            )

    def load_schedule(self, user_id: int) -> List[Event]:
        """Загружает список событий пользователя"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT events FROM schedules WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        return pickle.loads(row[0]) if row else []

    def get_all_schedules(self) -> dict:
        """Возвращает все расписания (для восстановления напоминаний)"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id, events FROM schedules")
        return {row[0]: pickle.loads(row[1]) for row in cursor.fetchall()}

    def clear_user_events(self, user_id: int):
        """Очищает расписание пользователя"""
        with self.conn:
            self.conn.execute("DELETE FROM schedules WHERE user_id=?", (user_id,))
            self.conn.execute("DELETE FROM notifications WHERE user_id=?", (user_id,))

    def get_last_notified(self, user_id: int, event_name: str, event_time: datetime) -> Optional[datetime]:
        """Получает время последнего уведомления для события"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT last_notified FROM notifications WHERE user_id=? AND event_name=? AND event_time=?",
            (user_id, event_name, event_time.isoformat())
        )
        row = cursor.fetchone()
        return datetime.fromisoformat(row[0]) if row else None

    def update_last_notified(self, user_id: int, event_name: str, event_time: datetime, notified_time: datetime):
        """Обновляет время последнего уведомления для события"""
        with self.conn:
            self.conn.execute(
                '''INSERT OR REPLACE INTO notifications 
                (user_id, event_name, event_time, last_notified) 
                VALUES (?, ?, ?, ?)''',
                (user_id, event_name, event_time.isoformat(), notified_time.isoformat())
            )

    def close(self):
        """Закрывает соединение с БД"""
        self.conn.close()