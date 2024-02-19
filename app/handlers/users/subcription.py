import contextlib
from typing import List

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram.utils import exceptions

from app.keyboards.inline import SubscriptionKb, SetGenderKb
from app.keyboards.reply import MainMenuMarkup
from app.models.channel import Channel
from app.models.user import User


async def subscription_success(call: types.CallbackQuery, user: User):
    await call.answer("Вы подписаны на все каналы!", show_alert=True)
    await call.message.answer("<i>Нажми</i> /next <i>и начинай общение!</i>", reply_markup=MainMenuMarkup().get())

    if user.Gender == 0:
        await call.message.answer("✈️ Давай определимся с полом", reply_markup=SetGenderKb().get())

    with contextlib.suppress(exceptions.TelegramAPIError):
        await call.message.delete()


async def subscription_fail(call: types.CallbackQuery):
    await call.answer("Вы подписаны не на все каналы!", show_alert=True)


async def get_subscription_msg(m: Message, sub_info: List[Channel]):
    await m.answer("""
<b>Чтобы пользоваться ботом, необходимо подписаться на</b> наши каналы

<code>После подписки Вы сможете пользоваться анонимным чатом.</code>""",
                   reply_markup=SubscriptionKb().get(sub_info), parse_mode=types.ParseMode.HTML)


async def get_subscription_msg_cb(call: types.CallbackQuery, sub_info: List[Channel]):
    await call.message.answer("""
<b>Чтобы пользоваться ботом, необходимо подписаться на</b> наши каналы

<code>После подписки Вы сможете пользоваться анонимным чатом.</code>""",
                              reply_markup=SubscriptionKb().get(sub_info), parse_mode=types.ParseMode.HTML)


def setup_subscription(dp: Dispatcher):
    dp.register_callback_query_handler(get_subscription_msg_cb, is_not_member=True)
    dp.register_message_handler(get_subscription_msg, is_not_member=True)
    dp.register_callback_query_handler(subscription_fail, text="check_sub", is_not_member=False)
    dp.register_callback_query_handler(subscription_success, text="check_sub")
