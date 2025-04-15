import pickle
import sqlite3
from typing import Dict, List

from ics import Event


class ScheduleStorage:
    def __init__(self):
        self.conn = sqlite3.connect('schedules.db', check_same_thread=False)
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS user_schedules
                              (user_id INTEGER PRIMARY KEY, events BLOB)''')

    def save_schedule(self, user_id: int, events: List[Event]):
        with self.conn:
            self.conn.execute(
                "REPLACE INTO user_schedules VALUES (?, ?)",
                (user_id, pickle.dumps(events))
            )

    def load_schedule(self, user_id: int) -> List[Event]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT events FROM user_schedules WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        return pickle.loads(row[0]) if row else []

    def get_all_users(self) -> Dict[int, List[Event]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id, events FROM user_schedules")
        return {row[0]: pickle.loads(row[1]) for row in cursor.fetchall()}

    def close(self):
        self.conn.close()
