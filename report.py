import csv
import io
from datetime import date, datetime
from db import get_medicine_events_between, get_stool_events_between

def generate_csv(start_date: date, end_date: date):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Дата", "Время", "Тип", "Кто отметил", "Бристоль", "Кровь", "Слизь",
                     "Пена", "Зловоние", "Необычный цвет", "Цвет", "Консистенция",
                     "Питание/жидкость", "Детали"])

    # Лекарства
    for user_id, _, ts in get_medicine_events_between(start_date, end_date):
        dt = datetime.fromisoformat(ts)
        writer.writerow([dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S"),
                         "Лекарство", user_id, "", "", "", "", "", "", "", "", "", ""])

    # Стул
    for row in get_stool_events_between(start_date, end_date):
        user_id, ts, bristol, blood, mucus, foam, foul, unusual, color_det, consist, nutr, det = row
        dt = datetime.fromisoformat(ts)
        writer.writerow([dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S"),
                         "Стул", user_id, bristol, blood, mucus, foam, foul, unusual,
                         color_det, consist, nutr, det])

    output.seek(0)
    return output

def get_stats_text(start_date=None, end_date=None):
    if start_date and end_date:
        stools = get_stool_events_between(start_date, end_date)
        meds = get_medicine_events_between(start_date, end_date)
        period = f"{start_date} – {end_date}"
    else:
        # за всё время
        from db import get_stool_events_between, get_medicine_events_between
        stools = get_stool_events_between(date(2000,1,1), date.today())
        meds = get_medicine_events_between(date(2000,1,1), date.today())
        period = "всё время"

    stool_count = len(stools)
    medicine_count = len(meds)

    # Частота по дням
    days_set = set()
    bristol_sum = 0
    blood_count = mucus_count = foam_count = foul_count = unusual_color_count = 0
    for r in stools:
        ts = r[1]
        day = ts[:10]
        days_set.add(day)
        bristol_sum += r[2]
        blood_count += r[3]
        mucus_count += r[4]
        foam_count += r[5]
        foul_count += r[6]
        unusual_color_count += r[7]
    total_days = len(days_set)
    avg_stool = stool_count / total_days if total_days else 0
    avg_bristol = bristol_sum / stool_count if stool_count else 0

    text = f"📊 Статистика за {period}:\n"
    text += f"• Дней с записями: {total_days}\n"
    text += f"• Стулов: {stool_count} (в среднем {avg_stool:.1f} в день)\n"
    text += f"• Средний тип по Бристольской шкале: {avg_bristol:.1f}\n"
    text += f"• Лекарств принято: {medicine_count}\n\n"

    if stool_count > 0:
        text += "Признаки:\n"
        text += f"  Кровь: {blood_count} раз\n"
        text += f"  Слизь: {mucus_count} раз\n"
        text += f"  Пена: {foam_count} раз\n"
        text += f"  Зловонный запах: {foul_count} раз\n"
        text += f"  Необычный цвет: {unusual_color_count} раз\n"

    return text
