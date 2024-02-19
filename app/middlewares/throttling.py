import contextlib
from typing import Union

from aiogram import types, Dispatcher
from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils import exceptions
from aiogram.utils.exceptions import Throttled


class ThrottlingMiddleware(BaseMiddleware):

    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix='antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(ThrottlingMiddleware, self).__init__()

    async def throttle(self, target: Union[types.Message, types.CallbackQuery]):
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()
        if not handler:
            return
        limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
        key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")

        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            await self.target_throttled(target, t, dispatcher, key)
            raise CancelHandler()

    @staticmethod
    async def target_throttled(target: Union[types.Message, types.CallbackQuery],
                               throttled: Throttled, dispatcher: Dispatcher, key: str):
        msg = target.message if isinstance(target, types.CallbackQuery) else target
        delta = throttled.rate - throttled.delta

        if throttled.exceeded_count == 2:
            with contextlib.suppress(exceptions.TelegramAPIError):
                await msg.reply('<b>❗️ Вы отправляете сообщения слишком часто!</b>')
            return
        elif throttled.exceeded_count == 3:
            with contextlib.suppress(exceptions.TelegramAPIError):
                await msg.reply(
                    f'<b>⚠️ Подождите</b> <i>{round(delta, 2)}</i> <b>секунд, чтобы бот снова получал от вас '
                    f'сообщения.</b>')
            return

    async def on_process_message(self, message, data):
        await self.throttle(message)

    async def on_process_callback_query(self, call, data):
        await self.throttle(call)
