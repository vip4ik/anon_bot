import asyncio

from aiogram import Dispatcher, Bot
from aiogram.types import Message
from aiogram.utils import exceptions
from sqlalchemy import update, select
from sqlalchemy.orm import sessionmaker

from app.models.user import User


async def check_live_users(m: Message, db: sessionmaker):
    async with db() as s:
        users = await s.scalars(select(User.UserId).where(User.Deactivated == False))
        users = users.all()

    len_users = len(users)

    await m.answer(text=f'Найдено {len_users} пользователей')

    users_part_1 = users[:len_users // 2]
    users_part_2 = users[len_users // 2:]

    task_1 = asyncio.create_task(start_thread(users_part_1, db, m.bot))
    task_2 = asyncio.create_task(start_thread(users_part_2, db, m.bot))

    await asyncio.gather(task_1, task_2)

    await m.answer(text=f'Проверка завершена')


async def start_thread(users: list, db: sessionmaker, bot: Bot):
    dead_users = []

    for user in users:

        res = await check_user(user, bot)

        if res:
            continue

        dead_users.append(user)

        if len(dead_users) == 100:
            async with db() as s:
                for dead in dead_users:
                    await s.execute(update(User).where(User.UserId == dead).values(Deactivated=True))
                await s.commit()
            dead_users = []

    if dead_users:
        async with db() as s:
            for dead in dead_users:
                await s.execute(update(User).where(User.UserId == dead).values(Deactivated=True))
            await s.commit()


async def check_user(user_id: int, bot: Bot):
    try:
        await bot.send_chat_action(user_id, 'typing')
    except exceptions.RetryAfter as e:
        await asyncio.sleep(e.timeout)
        return await check_user(user_id, bot)

    except exceptions.Unauthorized:
        return False
    except exceptions.BadRequest:
        return False
    except exceptions.TelegramAPIError:
        return False
    else:
        return True


def setup_check_live(dp: Dispatcher):
    dp.register_message_handler(check_live_users, commands='reload_db', is_admin=True, state="*")
