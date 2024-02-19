import asyncio
import time
from contextlib import suppress
from typing import Optional, List

from aiogram import types
from aiogram.bot.api import make_request
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import ChatMemberStatus
from aiogram.utils import exceptions
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from app.models.channel import Channel
from app.models.channels_subs import ChannelSubs


class SUBMiddleware(BaseMiddleware):
    @staticmethod
    async def setup_chat(data: dict, user: types.User, chat: Optional[types.Chat] = None):
        user_id = int(user.id)
        db: sessionmaker = chat.bot["db"]

        async with db() as session:
            result = await session.execute(select(Channel))
            result = result.all()

        if not len(result):
            data["sub_info"]: List[Channel] = []
            return

        sub_info: List[Channel] = []
        channels_sub: List[Channel] = []
        for channel in result:
            if not channel[0].IsBot:
                with suppress(exceptions.TelegramAPIError):
                    if (await chat.bot.get_chat_member(channel[0].ChannelId, user_id)).status in [ChatMemberStatus.LEFT,
                                                                                                  None]:
                        sub_info.append(channel)
                        channels_sub.append(channel)
            else:
                try:
                    if not (await make_request((await chat.bot.get_session()), chat.bot.server, channel[0].BotToken,
                                               "sendChatAction", {
                                                   'chat_id': user.id,
                                                   'action': 'typing'
                                               })):
                        sub_info.append(channel)
                except:
                    sub_info.append(channel)

        if len(channels_sub) > 0:
            asyncio.create_task(update_sub_counter(db, channels_sub, user_id))

        data["sub_info"]: List[Channel] = sub_info

    async def on_pre_process_message(self, message: types.Message, data: dict):
        await self.setup_chat(data, message.from_user, message.chat)

    async def on_pre_process_callback_query(self, query: types.CallbackQuery, data: dict):
        await self.setup_chat(data, query.from_user, query.message.chat if query.message else None)

    async def post_process(self, obj, data, *args):
        del data["sub_info"]


async def update_sub_counter(db: sessionmaker, channels_sub, user_id):
    async with db() as session:
        session: AsyncSession

        for channel in channels_sub:
            res: ChannelSubs = await session.scalar(select(ChannelSubs).where(ChannelSubs.SubId == channel[0].Id,
                                                                              ChannelSubs.Userid == user_id))

            if res and (res.Status == 0 or res.Status == 2):
                res.Status = 0
                res.Updated_at = int(time.time())
                await session.merge(res)

            if not res:
                session.add(ChannelSubs(SubId=channel[0].Id,
                                        ChannelId=channel[0].ChannelId,
                                        Userid=user_id))
        await session.commit()
