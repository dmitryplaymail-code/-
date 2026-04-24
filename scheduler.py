from aiogram import Bot, types
from datetime import date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import db
import report
from config import ALLOWED_USERS, REMINDER_HOUR, REMINDER_MINUTE, REPORT_DAY_OF_WEEK, REPORT_HOUR, REPORT_MINUTE

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")  # укажите свой часовой пояс, если нужно

async def send_reminder(bot: Bot):
    """Ежедневное напоминание всем разрешённым."""
    for uid in ALLOWED_USERS:
        stool_today = db.get_last_stool_date()
        if stool_today:
            text = ("⏰ Напоминание: дайте Грише лекарство!\n"
                    "Сегодня стул уже был ✅, но проверьте дневник.")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💊 Лекарство принято", callback_data="medicine")]
            ])
        else:
            text = ("⏰ Напоминание: дайте Грише лекарство и отметьте стул!\n"
                    "Стул сегодня ещё не отмечен.")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💩 Стул", callback_data="stool"),
                 InlineKeyboardButton(text="💊 Лекарство", callback_data="medicine")]
            ])
        try:
            await bot.send_message(uid, text, reply_markup=keyboard)
        except Exception as e:
            print(f"Не удалось отправить напоминание пользователю {uid}: {e}")

async def send_weekly_report(bot: Bot):
    """Еженедельный отчёт в воскресенье."""
    today = date.today()
    start = today.subtract(days=7)
    end = today
    csv_file = report.generate_csv(start, end)
    stats = report.get_stats_text(start, end)
    for uid in ALLOWED_USERS:
        try:
            await bot.send_document(
                uid,
                document=types.BufferedInputFile(csv_file.getvalue().encode('utf-8'),
                                                 filename=f"Гриша_неделя_{start}_{end}.csv"),
                caption="📊 Еженедельный отчёт"
            )
            await bot.send_message(uid, stats)
        except Exception as e:
            print(f"Ошибка отправки отчёта пользователю {uid}: {e}")

def setup_scheduler(bot: Bot):
    scheduler.add_job(
        send_reminder,
        CronTrigger(hour=REMINDER_HOUR, minute=REMINDER_MINUTE),
        args=[bot],
        id="daily_reminder"
    )
    scheduler.add_job(
        send_weekly_report,
        CronTrigger(day_of_week=REPORT_DAY_OF_WEEK, hour=REPORT_HOUR, minute=REPORT_MINUTE),
        args=[bot],
        id="weekly_report"
    )
    scheduler.start()
