from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime, date
import db
import report
from config import ALLOWED_USERS
from states import StoolForm

router = Router()

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💩 Стул"), KeyboardButton(text="💊 Лекарство")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📋 Отчёт")]
    ],
    resize_keyboard=True
)

def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USERS

# ========== Главное меню ==========
@router.message(Command("start"))
async def cmd_start(message: Message):
    if not is_allowed(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    await message.answer("Дневник Гриши. Выберите действие:", reply_markup=MAIN_KEYBOARD)

# ========== Лекарство ==========
@router.message(F.text == "💊 Лекарство")
@router.message(Command("medicine"))
async def medicine(message: Message):
    if not is_allowed(message.from_user.id):
        return
    db.add_medicine_event(message.from_user.id)
    now = datetime.now().strftime("%H:%M")
    await message.answer(f"💊 Лекарство принято в {now}", reply_markup=MAIN_KEYBOARD)

# ========== Стул (FSM) ==========
@router.message(F.text == "💩 Стул")
@router.message(Command("stool"))
async def stool_start(message: Message, state: FSMContext):
    if not is_allowed(message.from_user.id):
        return
    await state.set_state(StoolForm.bristol)
    # Инлайн-клавиатура с типами Бристольской шкалы
    builder = types.InlineKeyboardBuilder()
    types_list = [
        ("1 – Отдельные твёрдые комки (орехи)", "bristol_1"),
        ("2 – Колбасовидный, но комковатый", "bristol_2"),
        ("3 – Колбасовидный с трещинами на поверхности", "bristol_3"),
        ("4 – Гладкий и мягкий (идеал)", "bristol_4"),
        ("5 – Мягкие комки с чёткими краями", "bristol_5"),
        ("6 – Пушистые рваные кусочки, кашицеобразный", "bristol_6"),
        ("7 – Водянистый, без твёрдых частиц", "bristol_7"),
    ]
    for text, cb in types_list:
        builder.button(text=text, callback_data=cb)
    builder.adjust(1)
    await message.answer("Выберите тип стула по Бристольской шкале:",
                         reply_markup=builder.as_markup())

@router.callback_query(StoolForm.bristol, F.data.startswith("bristol_"))
async def process_bristol(callback: CallbackQuery, state: FSMContext):
    bristol_type = int(callback.data.split("_")[1])
    await state.update_data(bristol=bristol_type)
    await state.set_state(StoolForm.flags)

    # Клавиатура с флагами (множественный выбор)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🩸 Кровь", callback_data="flag_blood")],
        [types.InlineKeyboardButton(text="💧 Слизь", callback_data="flag_mucus")],
        [types.InlineKeyboardButton(text="🫧 Пена", callback_data="flag_foam")],
        [types.InlineKeyboardButton(text="🤢 Зловонный запах", callback_data="flag_foul")],
        [types.InlineKeyboardButton(text="🎨 Необычный цвет", callback_data="flag_color")],
        [types.InlineKeyboardButton(text="✅ Готово", callback_data="flags_done")]
    ])
    await state.update_data(flags=[])
    await callback.message.edit_text("Отметьте дополнительные признаки (можно несколько), затем нажмите «Готово»:",
                                     reply_markup=kb)
    await callback.answer()

@router.callback_query(StoolForm.flags, F.data.startswith("flag_"))
async def toggle_flag(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    flags = data.get("flags", [])
    flag_name = callback.data[5:]  # blood, mucus, foam, foul, color
    if flag_name in flags:
        flags.remove(flag_name)
    else:
        flags.append(flag_name)
    await state.update_data(flags=flags)

    # Обновим текст на кнопках, добавив галочки
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=f"🩸 Кровь {'✅' if 'blood' in flags else ''}", callback_data="flag_blood")],
        [types.InlineKeyboardButton(text=f"💧 Слизь {'✅' if 'mucus' in flags else ''}", callback_data="flag_mucus")],
        [types.InlineKeyboardButton(text=f"🫧 Пена {'✅' if 'foam' in flags else ''}", callback_data="flag_foam")],
        [types.InlineKeyboardButton(text=f"🤢 Зловонный запах {'✅' if 'foul' in flags else ''}", callback_data="flag_foul")],
        [types.InlineKeyboardButton(text=f"🎨 Необычный цвет {'✅' if 'color' in flags else ''}", callback_data="flag_color")],
        [types.InlineKeyboardButton(text="✅ Готово", callback_data="flags_done")]
    ])
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()

@router.callback_query(StoolForm.flags, F.data == "flags_done")
async def flags_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    flags = data.get("flags", [])
    if "color" in flags:
        await state.set_state(StoolForm.color)
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔴 Красный/кровянистый", callback_data="color_красный")],
            [types.InlineKeyboardButton(text="⚫ Чёрный", callback_data="color_чёрный")],
            [types.InlineKeyboardButton(text="🟢 Зелёный", callback_data="color_зелёный")],
            [types.InlineKeyboardButton(text="⚪ Белый/глинистый", callback_data="color_белый")],
            [types.InlineKeyboardButton(text="🟡 Другой (указать позже)", callback_data="color_другой")],
        ])
        await callback.message.edit_text("Уточните необычный цвет:", reply_markup=kb)
    else:
        await state.update_data(color_detail="")
        await go_to_consistency(callback, state)
    await callback.answer()

@router.callback_query(StoolForm.color, F.data.startswith("color_"))
async def process_color(callback: CallbackQuery, state: FSMContext):
    color = callback.data.split("_", 1)[1]
    await state.update_data(color_detail=color)
    await go_to_consistency(callback, state)
    await callback.answer()

async def go_to_consistency(callback: CallbackQuery, state: FSMContext):
    await state.set_state(StoolForm.consistency)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🧱 Твёрдая", callback_data="cons_твёрдая")],
        [types.InlineKeyboardButton(text="😊 Нормальная", callback_data="cons_нормальная")],
        [types.InlineKeyboardButton(text="💧 Жидкая", callback_data="cons_жидкая")],
    ])
    await callback.message.edit_text("Выберите консистенцию:", reply_markup=kb)

@router.callback_query(StoolForm.consistency, F.data.startswith("cons_"))
async def process_consistency(callback: CallbackQuery, state: FSMContext):
    cons = callback.data.split("_", 1)[1]
    await state.update_data(consistency=cons)
    await state.set_state(StoolForm.nutrition)
    await callback.message.edit_text("Опишите питание и объём жидкости за последние сутки (одним сообщением):")
    await callback.answer()

@router.message(StoolForm.nutrition)
async def process_nutrition(message: Message, state: FSMContext):
    await state.update_data(nutrition=message.text)
    await state.set_state(StoolForm.details)
    await message.answer("Дополнительные детали (недержание, привычное время, что-то ещё).\n"
                         "Если нечего добавить, напишите «нет»:", reply_markup=types.ReplyKeyboardRemove())

@router.message(StoolForm.details)
async def process_details(message: Message, state: FSMContext):
    details = message.text
    data = await state.get_data()

    # Сохраняем в БД
    db.add_stool_event(
        user_id=message.from_user.id,
        bristol=data["bristol"],
        blood="blood" in data.get("flags", []),
        mucus="mucus" in data.get("flags", []),
        foam="foam" in data.get("flags", []),
        foul_smell="foul" in data.get("flags", []),
        unusual_color="color" in data.get("flags", []),
        color_detail=data.get("color_detail", ""),
        consistency=data.get("consistency", ""),
        nutrition=data.get("nutrition", ""),
        details=details
    )

    # Подтверждение
    flags_text = ", ".join(data.get("flags", [])) or "нет"
    summary = (
        f"✅ Стул записан!\n"
        f"⏰ Время: {datetime.now().strftime('%H:%M')}\n"
        f"💩 Тип: {data['bristol']}\n"
        f"🔍 Признаки: {flags_text}\n"
        f"🎨 Цвет: {data.get('color_detail') or 'не указан'}\n"
        f"🧪 Консистенция: {data.get('consistency')}\n"
        f"🍽 Питание: {data.get('nutrition')}\n"
        f"📝 Детали: {details}"
    )
    await message.answer(summary, reply_markup=MAIN_KEYBOARD)
    await state.clear()

# Команда отмены FSM
@router.message(Command("cancel"))
async def cancel_fsm(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять.", reply_markup=MAIN_KEYBOARD)
        return
    await state.clear()
    await message.answer("Ввод стула отменён.", reply_markup=MAIN_KEYBOARD)

# ========== Статистика и отчёт ==========
@router.message(F.text == "📊 Статистика")
@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_allowed(message.from_user.id):
        return
    text = report.get_stats_text()
    await message.answer(text, reply_markup=MAIN_KEYBOARD)

@router.message(F.text == "📋 Отчёт")
@router.message(Command("report"))
async def cmd_report(message: Message):
    if not is_allowed(message.from_user.id):
        return
    args = message.text.split()
    if len(args) == 2:  # /report или кнопка без дат
        start, end = date(2000,1,1), date.today()
    elif len(args) == 3:
        try:
            start = date.fromisoformat(args[1])
            end = date.fromisoformat(args[2])
        except ValueError:
            await message.answer("Формат: /report ГГГГ-ММ-ДД ГГГГ-ММ-ДД", reply_markup=MAIN_KEYBOARD)
            return
    else:
        await message.answer("Используйте: /report ГГГГ-ММ-ДД ГГГГ-ММ-ДД", reply_markup=MAIN_KEYBOARD)
        return

    csv_file = report.generate_csv(start, end)
    await message.answer_document(
        document=types.BufferedInputFile(csv_file.getvalue().encode('utf-8'),
                                         filename=f"Гриша_дневник_{start}_{end}.csv"),
        caption="📊 Ваш отчёт"
    )
    stats = report.get_stats_text(start, end)
    await message.answer(stats, reply_markup=MAIN_KEYBOARD)
