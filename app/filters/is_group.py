from typing import Union

from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message, CallbackQuery, ChatType


class GroupFilter(BoundFilter):
    key = 'is_group'

    def __init__(self, is_group):
        self.is_group = is_group

    async def check(self, update: Union[Message, CallbackQuery]) -> bool:
        if isinstance(update, Message):
            chat = update.chat
        else:
            chat = update.message.chat
        if chat.type != ChatType.PRIVATE:
            return True
        return False
