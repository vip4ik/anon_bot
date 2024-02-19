from aiogram.dispatcher.filters.state import State, StatesGroup


class UserStates(StatesGroup):
    IN_SEARCH = State()
    CHAT = State()


class StartStates(StatesGroup):
    GENDER = State()


class Val(StatesGroup):
    SEND = State()

