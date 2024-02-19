import re
import time
from typing import Optional

from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from sqlalchemy import update
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from app.models.link import Link
from app.models.user import User


class ACLMiddleware(BaseMiddleware):
    @staticmethod
    async def setup_chat(data: dict, user: types.User, language: str, message: types.Message,
                         chat: Optional[types.Chat] = None):
        user_id = int(user.id)
        db: sessionmaker = chat.bot["db"]

        async with db() as session:
            async with session.begin():

                result = await session.execute(select(User).where(User.UserId == user_id))
                parse_user = result.scalars().all()
                val = None

                if len(parse_user) == 0:

                    unix_time = int(time.time())
                    args = message.get_args()
                    ref_link = None
                    if args:
                        ref_link = args.split(" ")[0]
                        if re.match(re.compile(r'^val-\d+$'), ref_link):
                            user_id_val = int(ref_link.split("-")[1])
                            user_val = await session.scalar(select(User).where(User.UserId == user_id_val))
                            if user_val:
                                val = user_id_val
                            ref_link = 'valentinka'

                        else:

                            result_link = await session.execute(select(Link).where(Link.LinkTitle == ref_link))
                            parse_link = result_link.scalars().all()
                            if len(parse_link) > 0:
                                await session.execute(update(Link).where(Link.Id == parse_link[0].Id).values(
                                    NewJoins=Link.NewJoins + 1,
                                    LastJoin=unix_time
                                ))

                    user = User(UserId=user_id, CreatedAt=unix_time, LanguageCode=language, Subscription=0,
                                RefLink=ref_link)
                    session.add(user)

                    await session.commit()

                    data["user"]: User = user
                    data["val"] = val
                    data["now_register"]: bool = True

                else:

                    data["user"]: User = parse_user[0]
                    data["val"] = val
                    data["now_register"]: bool = False

    async def on_pre_process_message(self, message: types.Message, data: dict):
        await self.setup_chat(data, message.from_user, message.from_user.language_code, message, message.chat)

    async def on_pre_process_callback_query(self, query: types.CallbackQuery, data: dict):
        # with suppress(Exception):
        #     if query.data == "start":
        #         db = query.bot["db"]
        #         async with db() as session:
        #             await session.execute("UPDATE stats_button SET clicks=clicks+1 WHERE id=1;")
        #             await session.commit()
        await self.setup_chat(data, query.from_user, query.from_user.language_code, query.message,
                              query.message.chat if query.message else None)

    async def post_process(self, obj, data, *args):
        del data["user"]