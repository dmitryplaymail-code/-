from aiogram.fsm.state import State, StatesGroup

class StoolForm(StatesGroup):
    bristol = State()
    flags = State()
    color = State()
    consistency = State()
    nutrition = State()
    details = State()