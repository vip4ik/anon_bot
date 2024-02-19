from aiogram import Dispatcher
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware
from aiogram.types.base import TelegramObject
from sqlalchemy.orm import sessionmaker


class DatabaseMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ['update']

    def __init__(self):
        super(DatabaseMiddleware, self).__init__()

    async def pre_process(self, obj: TelegramObject, data: dict, *args):
        dp = Dispatcher.get_current()
        data["db"]: sessionmaker = obj.bot["db"]
        data["storage"] = dp.storage
