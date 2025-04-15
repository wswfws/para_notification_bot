import sqlite3
import pickle
from typing import List
from ics import Event


class ScheduleStorage:
    def __init__(self, db_path: str = 'schedules.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS schedules
                              (user_id INTEGER PRIMARY KEY, events BLOB)''')

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

    def close(self):
        """Закрывает соединение с БД"""
        self.conn.close()