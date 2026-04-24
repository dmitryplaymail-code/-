from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, date
import db
import report
from config import ALLOWED_USERS

router = Router()

def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USERS

@router.message(Command("start"))
async def cmd_start(message: Message):
    if not is_allowed(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="💩 Стул", callback_data="stool")
    builder.button(text="💊 Лекарство", callback_data="medicine")
    builder.adjust(2)
    await message.answer("Дневник Гриши. Выберите действие:", reply_markup=builder.as_markup())

@router.message(Command("stool"))
async def cmd_stool(message: Message):
    if not is_allowed(message.from_user.id):
        return
    db.add_event(message.from_user.id, "stool")
    now = datetime.now().strftime("%H:%M")
    await message.answer(f"✅ Стул Гриши отмечен в {now}")

@router.message(Command("medicine"))
async def cmd_medicine(message: Message):
    if not is_allowed(message.from_user.id):
        return
    db.add_event(message.from_user.id, "medicine")
    now = datetime.now().strftime("%H:%M")
    await message.answer(f"💊 Лекарство принято в {now}")

@router.callback_query(F.data == "stool")
async def cb_stool(callback: CallbackQuery):
    if not is_allowed(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    db.add_event(callback.from_user.id, "stool")
    now = datetime.now().strftime("%H:%M")
    await callback.message.edit_text(f"✅ Стул отмечен в {now}")
    await callback.answer()

@router.callback_query(F.data == "medicine")
async def cb_medicine(callback: CallbackQuery):
    if not is_allowed(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    db.add_event(callback.from_user.id, "medicine")
    now = datetime.now().strftime("%H:%M")
    await callback.message.edit_text(f"💊 Лекарство отмечено в {now}")
    await callback.answer()

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_allowed(message.from_user.id):
        return
    text = report.get_stats_text()
    await message.answer(text)

@router.message(Command("report"))
async def cmd_report(message: Message):
    if not is_allowed(message.from_user.id):
        return
    args = message.text.split()
    if len(args) == 3:
        try:
            start = date.fromisoformat(args[1])
            end = date.fromisoformat(args[2])
        except ValueError:
            await message.answer("Формат: /report ГГГГ-ММ-ДД ГГГГ-ММ-ДД")
            return
    else:
        start = date(2000, 1, 1)
        end = date.today()
    csv_file = report.generate_csv(start, end)
    await message.answer_document(
        document=types.BufferedInputFile(csv_file.getvalue().encode('utf-8'),
                                         filename=f"Гриша_дневник_{start}_{end}.csv")
    )
    stats = report.get_stats_text(start, end)
    await message.answer(stats)
