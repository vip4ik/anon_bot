import contextlib
import datetime
import re
import time

import pytz
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram.utils import exceptions
from sqlalchemy import update, select
from sqlalchemy.orm import sessionmaker

from app.keyboards.inline import CancelKb
from app.keyboards.reply import AdminMarkup
from app.models.user import User
from app.states.admin_states import AdminGiveVip


async def give_vip_run(m: Message):
    text = 'Введите user_id пользователя, которому хотите подарить вип'
    await m.answer(text=text, reply_markup=CancelKb().get())
    await AdminGiveVip.user_id.set()


async def get_user_id_for_give_vip(m: Message, db: sessionmaker, state: FSMContext):
    if not m.text.isdigit():
        text = 'user id must be a number'

        return await m.answer(text=text, reply_markup=CancelKb().get())
    user_id = int(m.text)

    async with db() as s:
        user = await s.scalar(select(User).where(User.UserId == user_id))

    if not user:
        text = 'такой user_id не найдет\n\nВозможно юзер ни разу не активировал бота'
        return await m.answer(text=text, reply_markup=CancelKb().get())

    await state.update_data(user_id=user_id)

    text = 'Введите время на которое хотите выдать вип\n\n' \
           '5 или 5d или 5д - вип на 5 дней\n' \
           '3h или 3ч - вип на 3 часа\n\nРегистр не важен'
    await m.answer(text=text, reply_markup=CancelKb().get())

    await AdminGiveVip.get_time.set()


async def get_time_for_give_vip(m: Message, state: FSMContext, db: sessionmaker):
    data_state = await state.get_data()
    user_id = data_state.get('user_id', None)

    text = m.text
    text = text.lower()
    if not user_id:
        return await m.answer(text='Ошибка, попробуйте начать заново')

    bad_text = 'Вы ввели что-то не понятное'

    if re.match(r'^\d+[dд]*$', text):
        if text.isdigit():
            up_time = 3600 * 24 * int(text)
        else:
            text = text[:-1]
            if text.isdigit():
                up_time = 3600 * 24 * int(text)
            else:
                return await m.answer(text=bad_text, reply_markup=CancelKb().get())
    elif re.match(r'^\d+[hч]+$', text):
        if text.isdigit():
            up_time = 3600 * int(text)
        else:
            text = text[:-1]
            if text.isdigit():
                up_time = 3600 * int(text)
            else:
                return await m.answer(text=bad_text, reply_markup=CancelKb().get())

    else:
        return await m.answer(text=bad_text, reply_markup=CancelKb().get())

    current_time = int(time.time())

    async with db() as s:
        user = await s.scalar(select(User).where(User.UserId == user_id))
        set_vip_time = current_time + up_time if user.Subscription <= current_time else user.Subscription + up_time
        await s.execute(update(User).where(User.UserId == user_id).values(
            Subscription=set_vip_time
        ))
        await s.commit()

    date = datetime.datetime.fromtimestamp(set_vip_time, tz=pytz.timezone('Europe/Moscow'))
    date_text = date.strftime('%H:%M %d.%m.%Y по MCK')
    with contextlib.suppress(exceptions.TelegramAPIError):
        await m.bot.send_message(chat_id=user_id, text=f'Вам выдали вип\n\nДо {date_text}')

    await m.answer(text=f'Успешно выдан вип до {date_text}')
    await state.finish()


def setup_give_vip(dp: Dispatcher):
    dp.register_message_handler(give_vip_run, text=AdminMarkup.give_vip, state="*", is_admin=True)
    dp.register_message_handler(get_user_id_for_give_vip, state=AdminGiveVip.user_id, is_admin=True)
    dp.register_message_handler(get_time_for_give_vip, state=AdminGiveVip.get_time, is_admin=True)
