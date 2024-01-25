from aiogram.fsm.state import StatesGroup, State

class CreatingTracking(StatesGroup):
    city_from = State()
    city_to = State()
    date = State()
    max_price = State()
