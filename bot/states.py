from aiogram.fsm.state import State, StatesGroup


class TopupStates(StatesGroup):
    entering_amount_card = State()
    waiting_receipt = State()
    entering_amount_stars = State()
    entering_amount_crypto = State()


class AdminAddItemStates(StatesGroup):
    choosing_category = State()
    entering_title = State()
    entering_price = State()
    entering_duration = State()
    entering_description = State()
    entering_photo = State()


class AdminAddAssetStates(StatesGroup):
    choosing_item = State()
    entering_payload = State()


class ListingStates(StatesGroup):
    choosing_type = State()
    entering_title = State()
    entering_price = State()
    entering_description = State()


class P2PDisputeStates(StatesGroup):
    entering_reason = State()
