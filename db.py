import sqlite3
from datetime import datetime, date

DB_NAME = "diary.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,  -- 'stool' или 'medicine'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def add_event(user_id: int, event_type: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO events (user_id, event_type, created_at) VALUES (?, ?, ?)",
              (user_id, event_type, datetime.now().isoformat(' ', timespec='seconds')))
    conn.commit()
    conn.close()

def get_events_between(start_date: date, end_date: date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT user_id, event_type, created_at FROM events 
                 WHERE date(created_at) BETWEEN ? AND ?
                 ORDER BY created_at""", (start_date.isoformat(), end_date.isoformat()))
    rows = c.fetchall()
    conn.close()
    return rows

def get_last_stool_date():
    """Проверяет, был ли сегодня стул (любой пользователь)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("SELECT created_at FROM events WHERE event_type='stool' AND date(created_at)=? LIMIT 1", (today,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_all_events():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id, event_type, created_at FROM events ORDER BY created_at")
    rows = c.fetchall()
    conn.close()
    return rows
