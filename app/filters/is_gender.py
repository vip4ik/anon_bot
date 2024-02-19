from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from aiogram.dispatcher.handler import ctx_data

from app.models.user import User


class NotGenderFilter(BoundFilter):
    key = 'is_not_gender'

    def __init__(self, is_not_gender):
        self.is_not_gender = is_not_gender

    async def check(self, message: types.Message):

        data = ctx_data.get()
        upload: User = data.get("user")

        return not upload.Gender
