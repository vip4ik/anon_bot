import asyncio
import contextlib
import time

from aiogram import types, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils import exceptions
from sqlalchemy import update
from sqlalchemy.orm import sessionmaker

from app.keyboards.inline import SearchGenderKb, VipSearchKb, SearchAgeKb, AnswerVal
from app.keyboards.reply import CancelMarkup, CancelDialogMarkup, MainMenuMarkup
from app.models.queue_search import QueueSearch
from app.models.user import User
from app.states.user_states import UserStates, Val


async def cancel_search(m: types.Message, state: FSMContext, db: sessionmaker, user: User):
    await state.finish()
    async with db() as session:
        await session.execute(
            update(QueueSearch).where(QueueSearch.UserId == user.UserId, QueueSearch.Status == 0).values(Status=1)
        )
        await session.commit()

    await m.answer("Поиск успешно отменён", reply_markup=MainMenuMarkup().get())


async def search_peoples_g(m: types.Message):
    await m.answer("Выберите тип поиска", reply_markup=VipSearchKb().get())


async def vip_search(call: types.CallbackQuery, callback_data: dict):
    type_search = int(callback_data.get("type"))
    await call.answer()
    if type_search == 1:
        await call.message.answer("Кого будем искать?", reply_markup=SearchAgeKb().get())
    else:
        await call.message.answer("Кого будем искать?", reply_markup=SearchGenderKb().get())


async def search_peoples(message: types.Message, state: FSMContext, user: User, db: sessionmaker,
                         storage: RedisStorage2):
    await state.update_data(in_search=True)
    await state.set_state(UserStates.CHAT)
    user_id = message.from_user.id
    search_type = 'default'
    message_search = False

    for i in range(10):

        if not (await state.get_data()).get("in_search"):
            return

        async with db() as session:
            result = await session.execute('with next_task as '
                                           '(select user_id, username from queue_search '
                                           f"where status = 0 AND (gender_search = {user.Gender} or gender_search = 0) and (search_type = '{search_type}') AND user_id != {user_id} "
                                           'limit 1 '
                                           'for update skip locked) '
                                           'update queue_search '
                                           'set status = 1 '
                                           'from next_task '
                                           'where queue_search.user_id = next_task.user_id '
                                           'and queue_search.status = 0 '
                                           'returning (queue_search.user_id, queue_search.username); ')
            parse_result = result.scalars().all()

            if len(parse_result):
                await session.execute(update(QueueSearch).where(QueueSearch.UserId == user.UserId,
                                                                QueueSearch.Status == 0).values(Status=1))
                await session.commit()

                created_at = int(time.time())
                await state.update_data({"in_search": False, "companion": parse_result[0][0],
                                         "created_at": created_at, "send_messages": 0, "username": parse_result[0][1]})
                await FSMContext(storage, parse_result[0][0], parse_result[0][0]) \
                    .update_data({"in_search": False, "companion": user_id, "created_at": created_at,
                                  "send_messages": 0, "username": message.from_user.get_mention()})

                await FSMContext(storage, parse_result[0][0], parse_result[0][0]).set_state(UserStates.CHAT)

                find_txt = "Нашли для тебя кого-то! Начинай общение...\n/stop - остановить диалог"
                print(parse_result)
                with contextlib.suppress(exceptions.TelegramAPIError):
                    await message.answer(find_txt, reply_markup=CancelDialogMarkup().get(parse_result[0][1]))
                    await message.bot.send_message(parse_result[0][0], find_txt,
                                                   reply_markup=CancelDialogMarkup().get(
                                                       message.from_user.get_mention()))

                return

        if not message_search:
            await message.answer("💬 Ищем собеседника", reply_markup=ReplyKeyboardRemove())
            message_search = True
            async with db() as session:
                session.add(QueueSearch(UserId=user_id, Gender=user.Gender, SearchType=search_type))
                await session.commit()

        await asyncio.sleep(5)

    if not (await state.get_data()).get("in_search"):
        return

    async with db() as session:
        await session.execute(update(QueueSearch).where(QueueSearch.UserId == user.UserId, QueueSearch.Status == 0).
                              values(Status=1))
        await session.commit()

    await message.answer("Похоже, никого нет! Заходи позже.", reply_markup=MainMenuMarkup().get())
    await state.finish()


async def search_peoples_vulgar(message: types.Message, state: FSMContext, user: User, db: sessionmaker,
                                storage: RedisStorage2):
    await state.update_data(in_search=True)
    await state.set_state(UserStates.CHAT)
    user_id = message.from_user.id
    search_type = 'vulgar'
    message_search = False

    for i in range(10):

        if not (await state.get_data()).get("in_search"):
            return

        async with db() as session:
            result = await session.execute('with next_task as '
                                           '(select user_id, username from queue_search '
                                           f"where status = 0 AND search_type = '{search_type}' AND user_id != {user_id} "
                                           'limit 1 '
                                           'for update skip locked) '
                                           'update queue_search '
                                           'set status = 1 '
                                           'from next_task '
                                           'where queue_search.user_id = next_task.user_id '
                                           'and queue_search.status = 0 '
                                           'returning (queue_search.user_id, queue_search.username); ')
            parse_result = result.scalars().all()

            if len(parse_result):
                await session.execute(update(QueueSearch).where(QueueSearch.UserId == user.UserId,
                                                                QueueSearch.Status == 0).values(Status=1))
                await session.commit()

                created_at = int(time.time())
                await state.update_data({"in_search": False, "companion": parse_result[0][0],
                                         "created_at": created_at, "send_messages": 0, "username": parse_result[0][1]})
                await FSMContext(storage, parse_result[0][0], parse_result[0][0]) \
                    .update_data({"in_search": False, "companion": user_id, "created_at": created_at,
                                  "send_messages": 0, "username": message.from_user.get_mention()})

                await FSMContext(storage, parse_result[0][0], parse_result[0][0]).set_state(UserStates.CHAT)

                find_txt = "Нашли для тебя кого-то! Начинай общение...\n/stop - остановить диалог"
                print(parse_result)
                with contextlib.suppress(exceptions.TelegramAPIError):
                    await message.answer(find_txt, reply_markup=CancelDialogMarkup().get(parse_result[0][1]))
                    await message.bot.send_message(parse_result[0][0], find_txt,
                                                   reply_markup=CancelDialogMarkup().get(
                                                       message.from_user.get_mention()))

                return

        if not message_search:
            await message.answer("💬 Ищем собеседника", reply_markup=ReplyKeyboardRemove())
            message_search = True
            async with db() as session:
                session.add(QueueSearch(UserId=user_id, Gender=user.Gender, SearchType=search_type))
                await session.commit()

        await asyncio.sleep(5)

    if not (await state.get_data()).get("in_search"):
        return

    async with db() as session:
        await session.execute(update(QueueSearch).where(QueueSearch.UserId == user.UserId, QueueSearch.Status == 0).
                              values(Status=1))
        await session.commit()

    await message.answer("Похоже, никого нет! Заходи позже.", reply_markup=MainMenuMarkup().get())
    await state.finish()


async def search_peoples_gender(call: types.CallbackQuery, state: FSMContext, user: User, db: sessionmaker,
                                storage: RedisStorage2, callback_data: dict):
    await call.answer()
    await state.update_data(in_search=True)
    await state.set_state(UserStates.CHAT)
    search_type = 'gender'
    gender = int(callback_data.get("gender"))

    user_id = call.from_user.id
    message_search = False
    print(f"{user.Gender}  Ищет {gender}")
    for i in range(10):

        if not (await state.get_data()).get("in_search"):
            return

        async with db() as session:
            result = await session.execute('with next_task as '
                                           '(select user_id, username from queue_search '
                                           f"where status = 0 AND (search_type = '{search_type}' or search_type = 'default') AND gender = {gender} and (gender_search = {user.Gender} or gender_search = 0) and user_id != {user_id} "
                                           'limit 1 '
                                           'for update skip locked) '
                                           'update queue_search '
                                           'set status = 1 '
                                           'from next_task '
                                           'where queue_search.user_id = next_task.user_id '
                                           'and queue_search.status = 0 '
                                           'returning (queue_search.user_id, queue_search.username); ')
            parse_result = result.scalars().all()

            if len(parse_result):
                await session.execute(
                    update(QueueSearch).where(QueueSearch.UserId == user.UserId, QueueSearch.Status == 0).values(
                        Status=1))
                await session.commit()

                created_at = int(time.time())
                await state.update_data({"in_search": False, "companion": parse_result[0][0],
                                         "created_at": created_at, "send_messages": 0, "username": parse_result[0][1]})
                await FSMContext(storage, parse_result[0][0], parse_result[0][0]) \
                    .update_data({"in_search": False, "companion": user_id, "created_at": created_at,
                                  "send_messages": 0, "username": call.from_user.get_mention()})

                await FSMContext(storage, parse_result[0][0], parse_result[0][0]).set_state(UserStates.CHAT)

                find_txt = "Нашли для тебя кого-то! Начинай общение...\n/stop - остановить диалог"

                with contextlib.suppress(exceptions.TelegramAPIError):
                    with contextlib.suppress(exceptions.TelegramAPIError):
                        await call.message.answer(find_txt, reply_markup=CancelDialogMarkup().get(parse_result[0][1]))
                        await call.bot.send_message(parse_result[0][0], find_txt,
                                                    reply_markup=CancelDialogMarkup().get(
                                                        call.from_user.get_mention()))

                return

        if not message_search:
            pol = "Парня" if gender == 1 else "Девушку"
            await call.message.answer(f"💬 Ищем <b>{pol}</b>", reply_markup=ReplyKeyboardRemove())
            message_search = True
            async with db() as session:
                session.add(
                    QueueSearch(UserId=user_id, Gender=user.Gender, SearchGender=gender, SearchType=search_type))
                await session.commit()

        await asyncio.sleep(5)

    if not (await state.get_data()).get("in_search"):
        return

    async with db() as session:
        await session.execute(update(QueueSearch).where(QueueSearch.UserId == user.UserId, QueueSearch.Status == 0).
                              values(Status=1))
        await session.commit()

    await call.message.answer("Похоже, никого нет! Заходи позже.", reply_markup=MainMenuMarkup().get())
    await state.finish()


async def search_peoples_age(call: types.CallbackQuery, state: FSMContext, user: User, db: sessionmaker,
                             storage: RedisStorage2, callback_data: dict):
    await call.answer()
    await state.update_data(in_search=True)
    await state.set_state(UserStates.CHAT)

    age = int(callback_data.get("age"))
    search_type = 'age'
    user_id = call.from_user.id
    message_search = False

    for i in range(10):

        if not (await state.get_data()).get("in_search"):
            return

        async with db() as session:
            if age == 1:
                result = await session.execute('with next_task as '
                                               '(select user_id, username from queue_search '
                                               f'where age < 18 and user_id != {user_id} and status = 0 '
                                               'limit 1 '
                                               'for update skip locked) '
                                               'update queue_search '
                                               'set status = 1 '
                                               'from next_task '
                                               'where queue_search.user_id = next_task.user_id '
                                               'and queue_search.status = 0 '
                                               'returning (queue_search.user_id, queue_search.username); ')
            else:
                result = await session.execute('with next_task as '
                                               '(select user_id, username from queue_search '
                                               f'where age >= 18 and user_id != {user_id} and status = 0 '
                                               'limit 1 '
                                               'for update skip locked) '
                                               'update queue_search '
                                               'set status = 1 '
                                               'from next_task '
                                               'where queue_search.user_id = next_task.user_id '
                                               'and queue_search.status = 0 '
                                               'returning (queue_search.user_id, queue_search.username); ')
            parse_result = result.scalars().all()

            if len(parse_result):
                await session.execute(
                    update(QueueSearch).where(QueueSearch.UserId == user.UserId, QueueSearch.Status == 0).values(
                        Status=1))
                await session.commit()

                created_at = int(time.time())
                await state.update_data({"in_search": False, "companion": parse_result[0][0],
                                         "created_at": created_at, "send_messages": 0, "username": parse_result[0][1]})
                await FSMContext(storage, parse_result[0][0], parse_result[0][0]) \
                    .update_data({"in_search": False, "companion": user_id, "created_at": created_at,
                                  "send_messages": 0, "username": call.from_user.get_mention()})

                await FSMContext(storage, parse_result[0][0], parse_result[0][0]).set_state(UserStates.CHAT)

                find_txt = "Нашли для тебя кого-то! Начинай общение...\n/stop - остановить диалог"

                with contextlib.suppress(exceptions.TelegramAPIError):
                    await call.message.answer(find_txt, reply_markup=CancelDialogMarkup().get(parse_result[0][1]))
                    await call.bot.send_message(parse_result[0][0], find_txt,
                                                reply_markup=CancelDialogMarkup().get(call.from_user.get_mention()))

                return

        if not message_search:
            pol = "меньше 18 лет" if age == 1 else "18 лет и больше"
            await call.message.answer(f"💬 Ищем <b>{pol}</b>", reply_markup=ReplyKeyboardRemove())
            message_search = True
            async with db() as session:
                session.add(QueueSearch(UserId=user_id, Age=user.Age, SearchGender=age, SearchType=search_type))
                await session.commit()

        await asyncio.sleep(5)

    if not (await state.get_data()).get("in_search"):
        return

    async with db() as session:
        await session.execute(update(QueueSearch).where(QueueSearch.UserId == user.UserId, QueueSearch.Status == 0).
                              values(Status=1))
        await session.commit()

    await call.message.answer("Похоже, никого нет! Заходи позже.", reply_markup=MainMenuMarkup().get())
    await state.finish()


async def about_val(m: types.Message):
    bot = await m.bot.get_me()
    from aiogram.utils.markdown import hide_link

    hide = hide_link('http://telegra.ph//file/1d180d530a18ed5c36b4f.mp4')

    text = f'{hide}<b>😉 Привет!</b> Для того чтобы получать анонимные послания от своих друзей, ' \
           'просто размести свою личную ссылку в Инстаграм сторис' \
           ' или отправь его в чат с друзьями. ' \
           '\n' \
           '\n' \
           f'<b>🔗 Твоя ссылка:</b> https://t.me/{bot.username}?start=val-{m.chat.id}'

    await m.answer(text=text)


async def answer_val(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    await call.message.delete_reply_markup()
    user_id = int(callback_data['user_id'])
    await state.set_state(Val.SEND)
    await state.update_data(user_val=user_id)
    text = '⚡️ Напиши ответ на анонимное послание одним сообщением...'
    await call.message.answer(text=text, reply_markup=ReplyKeyboardRemove())


def setup_next(dp: Dispatcher):
    dp.register_callback_query_handler(answer_val, AnswerVal.answer_callback_data.filter(), )
    dp.register_message_handler(about_val, text=MainMenuMarkup.val_key)
    dp.register_message_handler(about_val, commands='valentinka', state='*')
    dp.register_message_handler(cancel_search, text=CancelMarkup.button_text, state=UserStates.CHAT)
    dp.register_message_handler(search_peoples, text=MainMenuMarkup.search_companion_button)
    dp.register_message_handler(search_peoples_vulgar, text=MainMenuMarkup.vulgar_chat_button)
    dp.register_message_handler(search_peoples_g, is_vip_access=True,
                                text=MainMenuMarkup.search_companion_gender_button)
    dp.register_callback_query_handler(search_peoples_gender, SearchGenderKb.gender_data.filter())
    dp.register_callback_query_handler(search_peoples_age, SearchAgeKb.age_data.filter())
    dp.register_callback_query_handler(vip_search, VipSearchKb.callback_data.filter())
    dp.register_message_handler(search_peoples, commands="next")
