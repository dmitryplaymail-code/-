import csv
import io
from datetime import date, datetime
from db import get_events_between, get_all_events

def generate_csv(start_date: date, end_date: date):
    events = get_events_between(start_date, end_date)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Дата", "Время", "Тип события", "Кто отметил (user_id)"])
    for user_id, event_type, created_at in events:
        dt = datetime.fromisoformat(created_at)
        writer.writerow([dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S"),
                         "Стул" if event_type == 'stool' else "Лекарство", user_id])
    output.seek(0)
    return output

def get_stats_text(start_date: date = None, end_date: date = None):
    if start_date and end_date:
        events = get_events_between(start_date, end_date)
        period = f"{start_date} – {end_date}"
    else:
        events = get_all_events()
        period = "всё время"
    stool_count = sum(1 for _, e, _ in events if e == 'stool')
    medicine_count = sum(1 for _, e, _ in events if e == 'medicine')
    # Простая статистика по дням
    days = {}
    for _, e, ts in events:
        d = ts[:10]
        days.setdefault(d, {'stool': 0, 'medicine': 0})
        days[d][e] += 1
    total_days = len(days)
    avg_stool = stool_count / total_days if total_days else 0
    text = f"📊 Статистика за {period}:\n"
    text += f"• Дней с записями: {total_days}\n"
    text += f"• Стулов всего: {stool_count} (в среднем {avg_stool:.1f} в день)\n"
    text += f"• Приёмов лекарства: {medicine_count}\n\n"
    if days:
        text += "По дням (стул / лекарство):\n"
        for d in sorted(days.keys()):
            text += f"{d}: стул {days[d]['stool']}, лек. {days[d]['medicine']}\n"
    return text