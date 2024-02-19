from contextlib import suppress

from aiogram import types, Dispatcher, exceptions
from aiogram.types import BotCommandScope, BotCommandScopeChat
from app.data.config import Config


async def set_commands(dp: Dispatcher):
    commands_list = [
        types.BotCommand("start", "Перезапустить бота"),
        types.BotCommand("valentinka", "💖 Валентинки"),
        types.BotCommand("next", "Поиск собеседника"),
        types.BotCommand("stop", "Остановить диалог"),
        # types.BotCommand("profile", "Профиль"),
        # types.BotCommand("prem", "Premium - подписка"),
    ]
    await dp.bot.set_my_commands(
        commands_list
    )

    commands_list.insert(0, types.BotCommand("admin", "Админ панель"))
    for admin in Config.ADMINS:
        with suppress(exceptions.TelegramAPIError):
            await dp.bot.set_my_commands(commands_list,
                                         scope=BotCommandScopeChat(chat_id=admin))

