import contextlib
import time

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import ChatMemberStatus, Message
from aiogram.utils import exceptions
from sqlalchemy import select, delete
from sqlalchemy.orm import sessionmaker

from app.data.config import Config
from app.keyboards.inline import RequestsManageKb, CancelKb, RequestManageKb
from app.keyboards.reply import AdminMarkup
from app.models.channel_request import ChannelRequest
from app.states.admin_states import AddChannelRequest


async def admin_stealer(message: types.Message, db: sessionmaker):
    async with db() as session:
        data = await session.execute(select(ChannelRequest))
        data = data.all()

    await message.answer("Используйте кнопки для управления заявками", reply_markup=RequestsManageKb().get(data))


async def admin_stealer_add_rc(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Чтобы добавить канал для заявок перешлите любое сообщение из канала:",
                                  reply_markup=CancelKb().get())
    await callback.answer()
    await state.set_state(AddChannelRequest.CHANNEL_FORWARD)


async def admin_stealer_add_forward(message: types.Message, db: sessionmaker, state: FSMContext):
    if not message.forward_from_chat:
        return await message.answer("Вы отправили не пересланное сообщение! Перешлите сообщение из канала:",
                                    reply_markup=CancelKb().get())
    bot = message.bot
    bot_me = await bot.get_me()
    if message.forward_from_chat.type == "channel":
        with contextlib.suppress(exceptions.TelegramAPIError):
            ans = await bot.get_chat_member(message.forward_from_chat.id, bot_me.id)
        if ans is not None and ans.status == ChatMemberStatus.ADMINISTRATOR:
            await state.finish()
            await message.answer("Канал для заявок успешно добавлен")
            async with db() as session:
                session.add(ChannelRequest(
                    ChannelId=message.forward_from_chat.id,
                    ChannelTitle=message.forward_from_chat.title
                ))
                await session.commit()
        else:
            await message.answer("У бота нет статуса администратора в канале. Перешлите сообщение из канала:",
                                 reply_markup=CancelKb().get())
    else:
        return await message.answer("Вы отправили сообщение не из канала! Перешлите сообщение из канала:",
                                    reply_markup=CancelKb().get())


async def admin_stealer_stats_rc(callback: types.CallbackQuery, callback_data: dict, db: sessionmaker):
    await callback.answer()
    channel_request_id = int(callback_data.get("id"))
    channel_id = int(callback_data.get("channel_id"))
    ref_link = f'{channel_request_id}:{channel_id}'

    async with db() as session:
        result_age_t = (await session.execute(
            f"SELECT AVG(age) FROM users WHERE (age>0 and ref_link='{ref_link}'"
            f" and created_at >= {int(time.time()) - 86400})")).first()
        result_m_t = (await session.execute(
            f"SELECT count(0) FROM users WHERE (gender=1 and ref_link='{ref_link}'"
            f" and created_at >= {int(time.time()) - 86400})")).first()
        result_d_t = (await session.execute(
            f"SELECT count(0) FROM users WHERE (gender=2 and ref_link='{ref_link}'"
            f" and created_at >= {int(time.time()) - 86400})")).first()
        result_a_t = (await session.execute(
            f"SELECT count(0) FROM users WHERE ref_link='{ref_link}'"
            f" and created_at >= {int(time.time()) - 86400}")).first()
        result_r_t = (await session.execute(
            f"SELECT count(0) FROM users WHERE ref_link='{ref_link}'"
            f" and created_at >= {int(time.time()) - 86400} and age > 0 and gender > 0")).first()
        result_age_w = (await session.execute(
            f"SELECT AVG(age) FROM users WHERE (age>0 and ref_link='{ref_link}'"
            f" and created_at >= {int(time.time()) - 604800})")).first()
        result_m_w = (await session.execute(
            f"SELECT count(0) FROM users WHERE (gender=1 and ref_link='{ref_link}'"
            f" and created_at >= {int(time.time()) - 604800})")).first()
        result_d_w = (await session.execute(
            f"SELECT count(0) FROM users WHERE (gender=2 and ref_link='{ref_link}'"
            f" and created_at >= {int(time.time()) - 604800})")).first()
        result_a_w = (await session.execute(
            f"SELECT count(0) FROM users WHERE ref_link='{ref_link}'"
            f" and created_at >= {int(time.time()) - 604800}")).first()
        result_r_w = (await session.execute(
            f"SELECT count(0) FROM users WHERE ref_link='{ref_link}'"
            f" and created_at >= {int(time.time()) - 604800} and age > 0 and gender > 0")).first()

        result_all = (await session.execute(
            f"SELECT count(0) FROM users WHERE ref_link='{ref_link}'")).first()

        res = await session.execute(select(ChannelRequest).where(ChannelRequest.ChannelId == channel_id))
        res = res.scalars().all()

    stat = f"\n📊 Статистика канала: \n    {res[0].ChannelTitle} " \
           f"\n🔗 Общее кол-во: {result_all[0]}" \
           f"\n\nЗа сегодня: {result_a_t[0]}" \
           f"\nЗарегистрированных: {result_r_t[0]}" \
           f"\nСредний возраст: {round((result_age_t[0] if result_age_t[0] is not None else 0), 2)}" \
           f"\n{result_m_t[0]} 👨 / {result_d_t[0]} 👩" \
           f"\n\nЗа неделю:  {result_a_w[0]}" \
           f"\nЗарегистрированных: {result_r_w[0]}" \
           f"\nСредний возраст: {round((result_age_w[0] if result_age_w[0] is not None else 0), 2)}" \
           f"\n{result_m_w[0]} 👨 / {result_d_w[0]} 👩\n\n" \
           f"\nВсего заявок было получено: {res[0].CountJoin}" \
           f"\nСтарых юзеров: {res[0].CountOldUser}" \
           f"\nОшибок: {res[0].CountError}" \
           f"\nНовых юзеров: {res[0].CountNewUser}" \
           f"\nЧерный список: {res[0].CountBlackList}"

    await callback.message.answer(stat,
                                  reply_markup=RequestManageKb().get(channel_request_id, 0))


async def admin_stealer_delete_rc(callback: types.CallbackQuery, callback_data: dict, db: sessionmaker):
    await callback.answer()
    channel_id = int(callback_data.get("channel_id"))
    agreed = int(callback_data.get("agreed"))

    if agreed:
        async with db() as session:
            await session.execute(delete(ChannelRequest).where(ChannelRequest.Id == channel_id))
            await session.commit()
        await callback.message.answer("Канал успешно удален")
    else:
        await callback.message.answer(f"Вы действительно хотите удалить этот канал?",
                                      reply_markup=RequestManageKb().get(channel_id, 1))


async def admin_stealer_message_begin(m: Message):
    await m.answer('Отправьте сообщение, которое будет отсылаться пользователям', reply_markup=CancelKb().get())
    await AddChannelRequest.MESSAGE.set()


async def admin_stealer_edit_message(m: Message, state: FSMContext):
    import json
    with open(Config.stiller_message_file, 'w') as f:
        json.dump(m.to_python(), f)
    await m.answer('Сообщение изменено')
    await state.finish()


async def del_stealer_message(m: Message):
    await m.answer('Сообщение удалено')
    import aiofiles.os
    with contextlib.suppress(Exception):
        await aiofiles.os.remove(Config.stiller_message_file)


def setup_stealer_adm(dp: Dispatcher):
    dp.register_message_handler(admin_stealer, text=AdminMarkup.requests_button, is_admin=True)
    dp.register_callback_query_handler(admin_stealer_add_rc, RequestsManageKb.callback_data_add.filter(), is_admin=True)
    dp.register_message_handler(admin_stealer_add_forward, state=AddChannelRequest.CHANNEL_FORWARD, is_admin=True,
                                content_types=types.ContentType.ANY)
    dp.register_callback_query_handler(admin_stealer_stats_rc, RequestsManageKb.callback_data_stats.filter(),
                                       is_admin=True)
    dp.register_callback_query_handler(admin_stealer_delete_rc, RequestManageKb.callback_data_delete.filter(),
                                       is_admin=True)
    dp.register_message_handler(admin_stealer_message_begin, text=AdminMarkup.edit_message_stealer, is_admin=True)
    dp.register_message_handler(del_stealer_message, text=AdminMarkup.del_message_stealer, is_admin=True)
    dp.register_message_handler(admin_stealer_edit_message, state=AddChannelRequest.MESSAGE, is_admin=True,
                                content_types=types.ContentType.ANY)
