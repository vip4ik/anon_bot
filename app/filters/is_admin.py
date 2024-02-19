from typing import Union

from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from sqlalchemy.orm import sessionmaker

from app.data.config import Config


class AdminFilter(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin):
        self.is_admin = is_admin

    async def check(self, db: sessionmaker, update: Union[types.Message, types.CallbackQuery]) -> bool:
        return str(update.from_user.id) in Config.ADMINS
