import contextlib
import re
from typing import List

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils import exceptions
from aiogram.utils.exceptions import TelegramAPIError
from sqlalchemy import update
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from app.keyboards.inline import SetGenderKb, AnswerKb, SubscriptionForVal, AnswerVal
from app.keyboards.reply import MainMenuMarkup
from app.models.channel import Channel
from app.models.link import Link
from app.models.user import User
from app.states.user_states import Val

val_text = '✨ Здесь ты можешь анонимно рассказать о своих чувствах к человеку,' \
           ' который опубликовал эту ссылку.' \
           '\n\n' \
           'Напиши сюда всё, что о нем думаешь в одном сообщении и' \
           ' через несколько мгновений он его получит,' \
           ' но не будет знать от кого оно.' \
           '\n\n' \
           '<b>📌 Для того чтобы получить свою личную ссылку - сначала напиши что нибудь!</b>'


async def get_start_command(message: types.Message, db: sessionmaker, user: User, val, state: FSMContext):
    if user.Gender != 0:
        if user.Deactivated:
            async with db() as session:
                await session.execute(
                    f"UPDATE Users SET deactivated = false WHERE id = {message.chat.id}")
                await session.commit()

        async with db() as session:
            args = message.get_args()
            if args:
                ref_link = args.split(" ")[0]
                if re.match(re.compile(r'^val-\d+$'), ref_link):
                    user_id_val = int(ref_link.split("-")[1])
                    user_val = await session.scalar(select(User).where(User.UserId == user_id_val))
                    if user_val and user_id_val != message.chat.id:

                        await state.set_state(Val.SEND)
                        await state.update_data(user_val=user_id_val)

                        await message.answer(text=val_text)
                    else:
                        await message.answer("<i>Нажми</i> /next <i>и начинай общение!</i>",
                                             reply_markup=MainMenuMarkup().get())
                else:
                    await message.answer("<i>Нажми</i> /next <i>и начинай общение!</i>",
                                         reply_markup=MainMenuMarkup().get())

                    result_link = await session.execute(select(Link).where(Link.LinkTitle == ref_link))
                    parse_link = result_link.scalars().all()
                    if len(parse_link) > 0:
                        await session.execute(update(Link).where(Link.Id == parse_link[0].Id).values(
                            OldJoins=Link.OldJoins + 1
                        ))
                await session.commit()
            else:
                await message.answer("<i>Нажми</i> /next <i>и начинай общение!</i>",
                                     reply_markup=MainMenuMarkup().get())
        return
    if val:
        await state.set_state(Val.SEND)
        await state.update_data(user_val=val)
        await message.answer(text=val_text)
        return

    elif args := message.get_args():
        ref_link = args.split(" ")[0]
        if re.match(re.compile(r'^val-\d+$'), ref_link):
            user_id_val = int(ref_link.split("-")[1])
            async with db() as session:
                user_val = await session.scalar(select(User).where(User.UserId == user_id_val))

            if user_val and user_id_val != message.chat.id:
                await state.set_state(Val.SEND)
                await state.update_data(user_val=user_id_val)
                await message.answer(text=val_text)
                return

    if user.Gender == 0:

        await message.answer("✈️ Давай определимся с полом", reply_markup=SetGenderKb().get())

    elif user.Age == 0:

        await message.answer("✈️ Введи свой возраст\n\n<i>Пример ответа: 18</i>")


async def get_subscription_msg(m: types.Message, sub_info: List[Channel], state: FSMContext):
    await state.update_data(message=m.parse_entities(as_html=True))
    text = 'Для того чтобы твое сообщение отправилось, тебе нужно подписаться на спонсоров\n\n' \
           'Подпишись на канал и нажми "Я подписался"'
    await m.answer(text=text,
                   reply_markup=SubscriptionForVal().get(sub_info), parse_mode=types.ParseMode.HTML)


async def subscription_fail(call: types.CallbackQuery):
    await call.answer("Вы подписаны не на все каналы!", show_alert=True)


async def subscription_success(call: types.CallbackQuery, user: User, state: FSMContext):
    await call.answer("Вы подписаны на все каналы!", show_alert=True)
    data_state = await state.get_data()
    user_val = data_state["user_val"]
    message = data_state["message"]
    with contextlib.suppress(TelegramAPIError):
        await call.bot.send_message(chat_id=user_val,
                                    text='<b>✨ У тебя новое анонимное послание:</b>\n\n' + message,
                                    reply_markup=AnswerVal().get(call.from_user.id))
    bot = await call.bot.get_me()

    from aiogram.utils.markdown import hide_link
    hide = hide_link('http://telegra.ph//file/1d180d530a18ed5c36b4f.mp4')

    text = f'{hide}✅ Готово, твое сообщение отправлено!\n\n' \
           'А если ты тоже хочешь получать анонимные послания от своих друзей, ' \
           'размести в инстаграме свою персональную ссылку.\n\n' \
           f'<b>🔗 Твоя ссылка:</b> https://t.me/{bot.username}?start={call.from_user.id}'
    await call.message.edit_text(text=text)
    await state.finish()
    if user.Gender == 0:

        await call.message.answer("✈️ Давай определимся с полом", reply_markup=SetGenderKb().get())

    elif user.Age == 0:

        await call.message.answer("✈️ Введи свой возраст\n\n<i>Пример ответа: 18</i>")
    else:
        await call.message.answer(text="✈️ Выберите действие:",
                                  reply_markup=MainMenuMarkup().get())


async def state_send_message(m: types.Message, state: FSMContext, user: User):
    data_state = await state.get_data()
    user_val = data_state["user_val"]
    with contextlib.suppress(TelegramAPIError):
        await m.bot.send_message(chat_id=user_val,
                                 text='<b>✨ У тебя новое анонимное послание:</b>\n\n' + m.parse_entities(as_html=True),

                                 reply_markup=AnswerVal().get(m.chat.id))
    bot = await m.bot.get_me()

    from aiogram.utils.markdown import hide_link
    hide = hide_link('http://telegra.ph//file/1d180d530a18ed5c36b4f.mp4')

    text = f'{hide}✅ Готово, твое сообщение отправлено!\n\n' \
           'А если ты тоже хочешь получать анонимные послания от своих друзей, ' \
           'размести в инстаграме свою персональную ссылку.\n\n' \
           f'<b>🔗 Твоя ссылка:</b> https://t.me/{bot.username}?start={m.chat.id}'
    await m.answer(text=text)
    await state.finish()
    if user.Gender == 0:

        await m.answer("✈️ Давай определимся с полом", reply_markup=SetGenderKb().get())

    elif user.Age == 0:

        await m.answer("✈️ Введи свой возраст\n\n<i>Пример ответа: 18</i>")
    else:
        await m.answer(text="✈️ Выберите действие:",
                       reply_markup=MainMenuMarkup().get())


async def set_start_gender(call: types.CallbackQuery, state: FSMContext, db: sessionmaker, callback_data: dict,
                           user: User):
    gender = callback_data.get("gender")

    async with db() as session:
        await session.execute(update(User).where(User.UserId == user.UserId).values(
            Gender=int(gender)
        ))
        await session.commit()

    with contextlib.suppress(exceptions.TelegramAPIError):
        await state.reset_state()
        await call.message.delete()
        await call.message.answer("✈️ Введи свой возраст\n\n<i>Пример ответа: 18</i>")


async def set_start_age(message: types.Message, db: sessionmaker, user: User):
    age = message.text
    try:
        age = int(age)
        if age < 0 or age > 100:
            await message.answer("✈️ Введи свой возраст\n\n<i>Пример ответа: 18</i>")
        else:
            async with db() as session:
                await session.execute(update(User).where(User.UserId == user.UserId).values(
                    Age=int(age)
                ))
                await session.commit()

            with contextlib.suppress(exceptions.TelegramAPIError):
                # await message.delete()
                await message.answer(text="✈️ Выберите действие:",
                                     reply_markup=MainMenuMarkup().get())

            return

    except ValueError:
        await message.answer("✈️ Введи свой возраст\n\n<i>Пример ответа: 18</i>")


async def get_start_command_cb(call: types.CallbackQuery, user: User):
    with contextlib.suppress(TelegramAPIError):
        await call.message.delete()
    if user.Gender != 0:
        await call.message.answer("<i>Нажми</i> /next <i>и начинай общение!</i>", reply_markup=MainMenuMarkup().get())

    elif user.Gender == 0:

        await call.message.answer("✈️ Давай определимся с полом", reply_markup=SetGenderKb().get())

    elif user.Age == 0:

        await call.message.answer("✈️ Введи свой возраст\n\n<i>Пример ответа: 18</i>")


def setup_start(dp: Dispatcher):
    dp.register_message_handler(get_start_command, commands="start", state='*')

    dp.register_message_handler(get_subscription_msg, is_not_member=True, state=Val.SEND)
    dp.register_callback_query_handler(subscription_fail, text="check_sub", is_not_member=False, state=Val.SEND)
    dp.register_callback_query_handler(subscription_success, text="check_sub", state=Val.SEND)
    dp.register_message_handler(state_send_message, state=Val.SEND)

    dp.register_callback_query_handler(set_start_gender, SetGenderKb.gender_data.filter(), is_not_gender=True)
    dp.register_callback_query_handler(get_start_command_cb, AnswerKb.callback_data.filter())
    dp.register_message_handler(get_start_command, is_not_gender=True)
    dp.register_message_handler(set_start_age, is_not_age=True)
