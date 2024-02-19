from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from aiogram.dispatcher.handler import ctx_data


class NotMemberFilter(BoundFilter):
    key = 'is_not_member'

    def __init__(self, is_not_member):
        self.is_not_member = is_not_member

    async def check(self, message: types.Message):

        sub_data = ctx_data.get()
        sub_info = sub_data.get("sub_info")

        return len(sub_info)
