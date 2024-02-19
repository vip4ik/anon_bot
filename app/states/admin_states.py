from aiogram.dispatcher.filters.state import State, StatesGroup


class AddChannelAdmin(StatesGroup):
    CHANNEL_FORWARD = State()
    CHANNEL_LINK = State()
    BOT_TOKEN = State()
    BOT_LINK = State()


class AddChannelRequest(StatesGroup):
    CHANNEL_FORWARD = State()
    MESSAGE = State()


class LinkAdmin(StatesGroup):
    REF_LINK = State()
    SET_PRICE = State()


class ManageAdmins(StatesGroup):
    ADMIN_ID = State()


class Debug(StatesGroup):
    JSON = State()


class MailState(StatesGroup):
    Type = State()
    Image = State()
    Text = State()
    Buttons = State()
    Forward = State()
    FullCopy = State()


class MailShow(StatesGroup):
    Id = State()


class MailStart(StatesGroup):
    Id = State()
    Accept = State()


class EditStart(StatesGroup):
    Text = State()
    Button = State()


class AddShow(StatesGroup):
    Text = State()
    Count = State()


class AdminReports(StatesGroup):
    admin_report = State()


class AdminGiveVip(StatesGroup):
    user_id = State()
    get_time = State()
