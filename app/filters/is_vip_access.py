import time

from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.handler import ctx_data

from app.models.user import User


class IsVipFilter(BoundFilter):
    key = 'is_vip_access'

    def __init__(self, is_vip_access):
        self.is_vip_access = is_vip_access

    async def check(self, message: types.Message):
        data = ctx_data.get()
        upload: User = data.get("user")
        vip_until = upload.Subscription
        unix_t = int(time.time())
        if vip_until:
            if vip_until > unix_t:
                return True

        return False
