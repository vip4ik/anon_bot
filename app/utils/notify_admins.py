from aiogram import Dispatcher

from app.data.config import Config


async def on_startup_notify(dp: Dispatcher, admin_ids):
    # for admin in admin_ids:
    pass
    #     try:
    #         await dp.bot.send_message(admin, "✅ Bot successful started")
    #     except Exception as err:
    #         logging.exception(err)
    # await dp.bot.send_message(f"@{Config.LOGS_DOMAIN}", "🟢 Бот был включен")


async def on_shutdown_notify(dp: Dispatcher, admin_ids):
    pass
    # for admin in admin_ids:
    #     try:
    #         await dp.bot.send_message(admin, "⛔ Bot shutdown")
    #     except Exception as err:
    #         logging.exception(err)
    # await dp.bot.send_message(f"@{Config.LOGS_DOMAIN}", "🔴 Бот был выключен")
