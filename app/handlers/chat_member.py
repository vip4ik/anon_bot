import logging
import time

from aiogram import Dispatcher
from aiogram.types import ChatMemberUpdated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.channel import Channel
from app.models.channels_subs import ChannelSubs


async def chat_member_handler(update: ChatMemberUpdated, db: sessionmaker):
    async with db() as session:
        session: AsyncSession
        channel = await session.scalar(select(Channel).where(Channel.ChannelId == update.chat.id))

        if not channel:
            return

        channels_subs = await session.scalar(
            select(ChannelSubs).where(ChannelSubs.SubId == channel.Id,
                                      ChannelSubs.Userid == update.new_chat_member.user.id))

        if not channels_subs:
            return

        logging.error(f"Subs - status: {channels_subs.Status}, channel: {update.chat.title}")

        if not update.new_chat_member.is_chat_member():
            if channels_subs.Status == 1:
                channels_subs.Status = 2
        else:
            if channels_subs.Status == 0 and channels_subs.Updated_at > int(time.time()) - 600:
                channels_subs.Status = 1

        logging.error(f"Subs - status: {channels_subs.Status}, channel: {update.chat.title}")

        await session.merge(channels_subs)
        await session.commit()


def setup_chat_member(dp: Dispatcher):
    dp.register_chat_member_handler(chat_member_handler)
