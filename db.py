import sqlite3
from datetime import datetime, date

DB_NAME = "diary.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Общая таблица событий (только для лекарств и старых записей стула)
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    # Детальная таблица для стула
    c.execute('''CREATE TABLE IF NOT EXISTS stool_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        bristol_type INTEGER NOT NULL,
        blood INTEGER DEFAULT 0,
        mucus INTEGER DEFAULT 0,
        foam INTEGER DEFAULT 0,
        foul_smell INTEGER DEFAULT 0,
        unusual_color INTEGER DEFAULT 0,
        color_detail TEXT DEFAULT '',
        consistency TEXT DEFAULT '',
        nutrition TEXT DEFAULT '',
        details TEXT DEFAULT ''
    )''')
    conn.commit()
    conn.close()

def add_medicine_event(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO events (user_id, event_type, created_at) VALUES (?, 'medicine', ?)",
              (user_id, datetime.now().isoformat(' ', timespec='seconds')))
    conn.commit()
    conn.close()

def add_stool_event(user_id: int, bristol: int, blood: bool, mucus: bool, foam: bool,
                    foul_smell: bool, unusual_color: bool, color_detail: str,
                    consistency: str, nutrition: str, details: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO stool_details 
                 (user_id, created_at, bristol_type, blood, mucus, foam, foul_smell,
                  unusual_color, color_detail, consistency, nutrition, details)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (user_id, datetime.now().isoformat(' ', timespec='seconds'), bristol,
               int(blood), int(mucus), int(foam), int(foul_smell),
               int(unusual_color), color_detail, consistency, nutrition, details))
    conn.commit()
    conn.close()

def get_last_stool_date():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("SELECT created_at FROM stool_details WHERE date(created_at)=? LIMIT 1", (today,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_medicine_events_between(start_date: date, end_date: date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT user_id, event_type, created_at FROM events 
                 WHERE event_type='medicine' AND date(created_at) BETWEEN ? AND ?
                 ORDER BY created_at""", (start_date.isoformat(), end_date.isoformat()))
    rows = c.fetchall()
    conn.close()
    return rows

def get_stool_events_between(start_date: date, end_date: date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT user_id, created_at, bristol_type, blood, mucus, foam,
                 foul_smell, unusual_color, color_detail, consistency, nutrition, details
                 FROM stool_details
                 WHERE date(created_at) BETWEEN ? AND ?
                 ORDER BY created_at""", (start_date.isoformat(), end_date.isoformat()))
    rows = c.fetchall()
    conn.close()
    return rows
