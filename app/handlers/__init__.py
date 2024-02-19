from aiogram import Dispatcher

from app.handlers.admins import setup_admin
from app.handlers.chat_member import setup_chat_member
from app.handlers.errors import setup_errors
from app.handlers.groups.all_group import setup_group_all
from app.handlers.users import setup_users


def setup(dp: Dispatcher):
    setup_admin(dp)
    setup_group_all(dp)
    setup_users(dp)
    setup_errors(dp)
    setup_chat_member(dp)
