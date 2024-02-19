from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from aiogram.dispatcher.handler import ctx_data

from app.models.user import User


class NotAgeFilter(BoundFilter):
    key = 'is_not_age'

    def __init__(self, is_not_age):
        self.is_not_age = is_not_age

    async def check(self, message: types.Message):

        data = ctx_data.get()
        upload: User = data.get("user")

        return not upload.Age
