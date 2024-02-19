import time

from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from aiogram.dispatcher.handler import ctx_data

from app.models.user import User


class IsBanFilter(BoundFilter):
    key = 'is_banned'

    def __init__(self, is_banned):
        self.is_banned = is_banned

    async def check(self, message: types.Message):
        data = ctx_data.get()
        user: User = data.get("user")
        if user.is_banned:
            return True

        return False
