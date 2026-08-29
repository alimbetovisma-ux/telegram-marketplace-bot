from aiogram.fsm.state import State, StatesGroup


class TopupStates(StatesGroup):
    entering_amount_card = State()
    waiting_receipt = State()
    entering_amount_stars = State()


class AdminAddItemStates(StatesGroup):
    choosing_category = State()
    entering_title = State()
    entering_price = State()
    entering_description = State()
    entering_photo = State()
