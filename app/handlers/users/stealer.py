import contextlib
import json
import time
from pathlib import Path

import aiofiles
import aiofiles.os
import aiofiles.ospath
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram.utils import exceptions
from aiogram.utils.exceptions import TelegramAPIError
from sqlalchemy import select
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from app.data.config import Config
from app.models.channel_request import ChannelRequest
from app.models.groups import Group
from app.models.user import User


async def steal_traffic(request: types.ChatJoinRequest):
    user_id = request.from_user.id
    db: sessionmaker = request.bot.get("db")
    ref_link = "stealer"
    print(0)

    async with db() as session:
        res: ChannelRequest = await session.scalar(
            select(ChannelRequest).where(ChannelRequest.ChannelId == request.chat.id))

    with contextlib.suppress(exceptions.TelegramAPIError):
        await request.approve()

    try:

        async with aiofiles.open('blacklist.txt', mode='r') as f:
            contents = await f.read()
            data = contents.split("\n")

            if user_id in data:
                async with db() as session:
                    await session.execute('UPDATE request_channels SET '
                                          'count_join=count_join+1,'
                                          'count_black_list=count_black_list+1'
                                          f'where channel_id={request.chat.id}')
                    await session.commit()
                return

    except Exception:
        return
    print(6)

    path = Path(Config.stiller_message_file)

    async with db() as session:
        print(1)
        user = await session.scalar(select(User).where(User.UserId == user_id).limit(1))
        if user:
            await session.execute('UPDATE request_channels SET '
                                  'count_join=count_join+1,'
                                  'count_old_user=count_old_user+1'
                                  f'where channel_id={request.chat.id}')
            await session.commit()
            return
        print(2)

        if not res:
            try:
                await request.bot.send_chat_action(user_id, 'typing')
            except TelegramAPIError:
                await session.execute('UPDATE request_channels SET '
                                      'count_join=count_join+1,'
                                      'count_error=count_error+1'
                                      f'where channel_id={request.chat.id}')
            else:
                await session.execute('UPDATE request_channels SET '
                                      'count_join=count_join+1,'
                                      'count_new_user=count_new_user+1'
                                      f'where channel_id={request.chat.id}')
                unix_time = int(time.time())
                user = User(UserId=user_id, CreatedAt=unix_time, LanguageCode=request.from_user.language_code,
                            Subscription=0, RefLink=ref_link, StealerFrom=request.chat.id)

                session.add(user)
            await session.commit()
            return
        print(3)

        ref_link = f'{res.Id}:{res.ChannelId}'
        if not (path.exists() and path.is_file()):
            try:
                await request.bot.send_chat_action(user_id, 'typing')
            except TelegramAPIError:
                await session.execute('UPDATE request_channels SET '
                                      'count_join=count_join+1,'
                                      'count_error=count_error+1'
                                      f'where channel_id={request.chat.id}')
            else:
                await session.execute('UPDATE request_channels SET '
                                      'count_join=count_join+1,'
                                      'count_new_user=count_new_user+1'
                                      f'where channel_id={request.chat.id}')
                unix_time = int(time.time())
                user = User(UserId=user_id, CreatedAt=unix_time, LanguageCode=request.from_user.language_code,
                            Subscription=0, RefLink=ref_link, StealerFrom=request.chat.id)

                session.add(user)
            await session.commit()
            return
        print(4)

        try:
            with open(Config.stiller_message_file, 'r') as f:
                mes = json.load(f)
                m: Message = Message.to_object(mes)
            await m.send_copy(user_id, disable_web_page_preview=True)

        except TelegramAPIError:
            await session.execute('UPDATE request_channels SET '
                                  'count_join=count_join+1,'
                                  'count_error=count_error+1'
                                  f'where channel_id={request.chat.id}')
        except Exception:
            try:
                await request.bot.send_chat_action(user_id, 'typing')
            except TelegramAPIError:
                await session.execute('UPDATE request_channels SET '
                                      'count_join=count_join+1,'
                                      'count_error=count_error+1'
                                      f'where channel_id={request.chat.id}')
            else:
                await session.execute('UPDATE request_channels SET '
                                      'count_join=count_join+1,'
                                      'count_new_user=count_new_user+1'
                                      f'where channel_id={request.chat.id}')
                unix_time = int(time.time())
                user = User(UserId=user_id, CreatedAt=unix_time, LanguageCode=request.from_user.language_code,
                            Subscription=0, RefLink=ref_link, StealerFrom=request.chat.id)

                session.add(user)
            await session.commit()
            return
        else:
            await session.execute('UPDATE request_channels SET '
                                  'count_join=count_join+1,'
                                  'count_new_user=count_new_user+1'
                                  f'where channel_id={request.chat.id}')
            unix_time = int(time.time())
            user = User(UserId=user_id, CreatedAt=unix_time, LanguageCode=request.from_user.language_code,
                        Subscription=0, RefLink=ref_link, StealerFrom=request.chat.id)

            session.add(user)
        await session.commit()
        print(5)


async def bot_blocked(chat_member: types.ChatMemberUpdated, db: sessionmaker, state: FSMContext):
    if chat_member.chat.type in [types.ChatType.SUPERGROUP, types.ChatType.GROUP]:
        status = chat_member.new_chat_member.is_chat_admin()
        async with db() as s:
            await s.merge(Group(Id=chat_member.chat.id, ChatTitle=chat_member.chat.title, status=status))
            await s.commit()
        return

    if chat_member.chat.type not in [types.ChatType.PRIVATE]:
        return

    if chat_member.new_chat_member.status in [types.ChatMemberStatus.LEFT,
                                              types.ChatMemberStatus.KICKED,
                                              types.ChatMemberStatus.BANNED]:
        async with db() as session:
            await session.execute(
                f"UPDATE Users SET deactivated = true WHERE id = {chat_member.chat.id}")
            await session.commit()
    else:
        async with db() as session:
            await session.execute(
                f"UPDATE Users SET deactivated = false WHERE id = {chat_member.chat.id}")
            await session.commit()


def setup_stealer(dp: Dispatcher):
    dp.register_chat_join_request_handler(steal_traffic)
    dp.register_my_chat_member_handler(bot_blocked, state="*")



