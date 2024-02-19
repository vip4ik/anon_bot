from aiogram import Dispatcher
from aiogram.types import Message, ContentType


async def all_message(m: Message):
    return


def setup_group_all(dp: Dispatcher):
    dp.register_message_handler(all_message, content_types=ContentType.ANY, is_group=True, state='*')
