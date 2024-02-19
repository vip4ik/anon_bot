import asyncio
import logging

import aiopayok
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode
from aiopayok import Payok
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app import filters, middlewares, handlers
from app.data.config import Config
from app.utils.notify_admins import on_startup_notify, on_shutdown_notify
from app.utils.set_bot_commands import set_commands

logger = logging.getLogger(__name__)


def get_handled_updates_list(dp: Dispatcher) -> list:
    available_updates = (
        "callback_query_handlers", "channel_post_handlers", "chat_member_handlers",
        "chosen_inline_result_handlers", "edited_channel_post_handlers", "edited_message_handlers",
        "inline_query_handlers", "message_handlers", "my_chat_member_handlers", "poll_answer_handlers",
        "poll_handlers", "pre_checkout_query_handlers", "shipping_query_handlers", "chat_join_request_handlers"
    )
    return [item.replace("_handlers", "") for item in available_updates
            if len(dp.__getattribute__(item).handlers) > 0]


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger.error("Starting bot")

    bot = Bot(token=Config.BOT_TOKEN, parse_mode=ParseMode.HTML)

    engine = create_async_engine(
        f"postgresql+asyncpg://{Config.USER}:{Config.PASSWORD}@{Config.HOST}/{Config.DBNAME}",
        future=True,
        # echo=True,
        pool_size=50, max_overflow=50
    )

    from app.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    bot["db"]: sessionmaker = async_session_maker
    bot["config"]: Config = Config
    bot["payment"]: aiopayok = Payok(
        api_id=1031,
        api_key="75CABCAA60576FF29664341F983543FD-917EFDEBEECA65CDCC5E980715AF7170-09FEF6779E723C555A32B968C1145A2A",
        secret_key="e35e6efce36b3d629aeb72f3ac02a42a",
        shop=2152
    )

    # RedisStorage2(db=5, pool_size=50)
    dp = Dispatcher(bot, storage=MemoryStorage())

    middlewares.setup(dp)
    filters.setup(dp, async_session_maker)
    handlers.setup(dp)

    await set_commands(dp)

    try:
        await dp.skip_updates()
        await on_startup_notify(dp, Config.ADMINS)
        await dp.start_polling(dp, reset_webhook=True, allowed_updates=get_handled_updates_list(dp))
    finally:

        await on_shutdown_notify(dp, Config.ADMINS)

        await dp.storage.close()
        await dp.storage.wait_closed()
        await (await bot.get_session()).close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
