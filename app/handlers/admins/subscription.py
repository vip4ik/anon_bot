from contextlib import suppress

from aiogram import Dispatcher, types
from aiogram.bot.api import make_request
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ChatMemberStatus
from aiogram.utils import exceptions
from sqlalchemy import select, delete
from sqlalchemy.orm import sessionmaker

from app.keyboards.inline import AdminChannelsListKb, AdminDeleteChannelKb, AdminPanelKb, CancelKb, \
    AdminSelectGroupToSub, AdminInfoGroup
from app.keyboards.reply import AdminMarkup
from app.models.channel import Channel
from app.models.groups import Group
from app.states.admin_states import AddChannelAdmin


async def add_channel(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(AddChannelAdmin.CHANNEL_FORWARD)
    await call.message.edit_text(f"Перешлите любое сообщение из "
                                 f"канала/бота в этот чат", reply_markup=CancelKb().get())


async def get_channel_message(m: Message, state: FSMContext):
    bot = m.bot
    bot_me = await bot.get_me()
    if m.forward_from_chat and m.forward_from_chat.type == "channel":
        ans = await bot.get_chat_member(m.forward_from_chat.id, bot_me.id)
        if ans.status == ChatMemberStatus.ADMINISTRATOR:
            await state.update_data(channel_id=m.forward_from_chat.id)
            await AddChannelAdmin.CHANNEL_LINK.set()
            await m.answer(f"Пришлите уникальную инвайт-ссылку",
                           reply_markup=CancelKb().get())
    elif m.forward_from and m.forward_from.is_bot:
        await state.update_data(bot_id=m.forward_from.id, is_bot=True, bot_title=m.forward_from.full_name)
        await AddChannelAdmin.BOT_TOKEN.set()
        await m.answer(f"Пришлите токен для этого бота",
                       reply_markup=CancelKb().get())


async def set_channel_link(m: Message, state: FSMContext, db: sessionmaker):
    if "t.me" not in m.text:
        return await m.answer("Неверная ссылка! Ссылка должна начинаться с t.me",
                              reply_markup=CancelKb().get())

    data = await state.get_data()
    chat = await m.bot.get_chat(data["channel_id"])
    async with db() as session:
        channel = Channel(ChannelId=data["channel_id"], ChannelTitle=chat.title, ChannelLink=m.text)
        session.add(channel)
        await session.commit()

    await state.reset_state()
    await m.answer("Канал был успешно добавлен для подписки.")


async def set_bot_token(m: Message, state: FSMContext):
    token = m.text
    bot_id = (await state.get_data()).get("bot_id")
    try:
        result = (await make_request((await m.bot.get_session()), m.bot.server, token, "getMe"))
        if result["id"] == bot_id:
            await state.update_data(bot_token=token)
            await AddChannelAdmin.BOT_LINK.set()
            await m.answer(f"Пришлите уникальную инвайт-ссылку для бота",
                           reply_markup=CancelKb().get())
    except Exception as e:
        print(e)
        return await m.answer("Неверный токен бота! Попробуйте еще раз",
                              reply_markup=CancelKb().get())


async def set_bot_link(m: Message, state: FSMContext, db: sessionmaker):
    data = await state.get_data()
    bot_id = data.get("bot_id")
    bot_title = data.get("bot_title")
    bot_token = data.get("bot_token")
    async with db() as session:
        channel = Channel(ChannelLink=m.text, ChannelId=bot_id, ChannelTitle=bot_title, BotToken=bot_token,
                          IsBot=True)
        session.add(channel)
        await session.commit()

    await state.reset_state(with_data=True)
    await m.answer("Бот был успешно добавлен для подписки.")


async def manage_channels(message: types.Message, db: sessionmaker):
    async with db() as session:
        result = await session.execute(select(Channel))
        links = result.all()

    txt = "Вот список каналов:"
    if not len(links):
        txt = "Список каналов пуст."

    await message.answer(txt, reply_markup=AdminChannelsListKb().get(links))


async def manage_channels_cb(call: types.CallbackQuery, db: sessionmaker):
    await call.answer()

    async with db() as session:
        result = await session.execute(select(Channel))
        links = result.all()

    txt = "Вот список каналов и ботов:"
    if not len(links):
        txt = "Список каналов пуст."

    await call.message.answer(txt, reply_markup=AdminChannelsListKb().get(links))
    await call.message.delete()


async def manage_channel(call: types.CallbackQuery, callback_data: dict, db: sessionmaker):
    await call.answer()
    channel_id = callback_data["channel_id"]
    bot = call.bot

    async with db() as session:
        result = await session.execute(select(Channel).where(Channel.ChannelId == int(channel_id)))
        result = result.all()

        if not result[0][0].IsBot:
            query = "select status, count(0) from " \
                    f"channels_subs where sub_id={result[0][0].Id} group by status order by status"

            res = (await session.execute(query)).all()
    if result[0][0].IsBot:
        title = f"Бот {result[0][0].ChannelTitle}"
    else:
        try:
            chat = await bot.get_chat(channel_id)
            title = f"Канал: {chat.title}\n\n"
        except exceptions.TelegramAPIError:
            title = f"❌Бот не видит этот канал\nВозможно бот удален с канала\n\nКанал: {result[0][0].ChannelTitle}\n\n"

        sub_all = 0
        sub_live = 0
        sub_leave = 0

        for r in res:
            if r[0] == 0:
                sub_all += r[1]
            if r[0] == 1:
                sub_all += r[1]
                sub_live += r[1]
            if r[0] == 2:
                sub_all += r[1]
                sub_leave += r[1]

        title += f"Было выдано: {sub_all}\nПодписалось: {sub_live}\nОтписалось: {sub_leave}"
    await call.message.edit_text(f"{title}\n\nСсылка: {result[0][0].ChannelLink}",
                                 reply_markup=AdminDeleteChannelKb().get(channel_id, result[0][0].IsBot))


async def delete_channel(call: types.CallbackQuery, callback_data: dict, db: sessionmaker):
    await call.answer()
    async with db() as session:
        await session.execute(
            delete(Channel).where(Channel.ChannelId == int(callback_data.get("channel_id")))
        )
        await session.commit()
    await call.message.edit_text("Канал/Бот успешно удалён.")


async def add_group(call: types.CallbackQuery, db: sessionmaker):
    async with db() as s:
        res = await s.scalars(select(Group).where(Group.status == True))
        groups = res.fetchall()

    if not groups:
        return await call.answer(text='Назначьте бота администратором в группе и нажмите снова.\n'
                                      '\nЕсли бот уже админ, но выходит это сообщение, '
                                      'то добавьте бота заново в админы группы',
                                 show_alert=True,
                                 cache_time=5)

    await call.answer()
    text = 'Выберите группу, которую хотите добавить в обязательную подписку'
    keyboard = AdminSelectGroupToSub().get(groups, 1)
    await call.message.edit_text(text=text, reply_markup=keyboard)


async def edit_page_group(call: types.CallbackQuery, db: sessionmaker, callback_data: dict):
    page = int(callback_data['page'])
    if page == 0:
        return await call.answer(text='Страницы кончились')

    async with db() as s:
        groups = await s.scalars(select(Group).where(Group.status is True))

    if (page - 1) * 8 >= len(groups):
        return await call.answer(text='Страницы кончились')

    keyboard = AdminSelectGroupToSub().get(groups, 1)
    await call.message.edit_reply_markup(reply_markup=keyboard)


async def info_group(call: types.CallbackQuery, callback_data: dict):
    chat_id = int(callback_data['chat_id'])

    try:
        chat = await call.bot.get_chat(chat_id)
    except exceptions.TelegramAPIError:
        return await call.answer(text='Группа недоступна')

    await call.answer()
    text = 'Информация о группе:\n\n' \
           f'Название: {chat.title}\n\n'
    text += f'Юзернейм: @{chat.username}\n' if chat.username else ''
    text += f'Ссылка: {chat.invite_link}\n' if chat.invite_link else ''

    keyboard = AdminInfoGroup().get(chat_id)
    await call.message.answer(text=text, reply_markup=keyboard)


async def leave_group_true(call: types.CallbackQuery, callback_data: dict):
    await call.answer('Успешно')
    await call.message.delete_reply_markup()
    chat_id = int(callback_data['chat_id'])

    with suppress(exceptions.TelegramAPIError):
        await call.bot.leave_chat(chat_id)


async def select_group(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    chat_id = int(callback_data['chat_id'])

    await state.update_data(channel_id=chat_id)
    await AddChannelAdmin.CHANNEL_LINK.set()
    await call.message.edit_text(f"Пришлите уникальную инвайт-ссылку",
                                 reply_markup=CancelKb().get())


def setup_subscriptions(dp: Dispatcher):
    dp.register_message_handler(manage_channels, text=AdminMarkup.channels_button, is_admin=True)

    dp.register_message_handler(get_channel_message, state=AddChannelAdmin.CHANNEL_FORWARD, is_admin=True,
                                content_types=types.ContentType.ANY)
    dp.register_message_handler(set_channel_link, is_admin=True, state=AddChannelAdmin.CHANNEL_LINK)
    dp.register_message_handler(set_bot_token, is_admin=True, state=AddChannelAdmin.BOT_TOKEN)
    dp.register_message_handler(set_bot_link, is_admin=True, state=AddChannelAdmin.BOT_LINK)
    dp.register_callback_query_handler(manage_channels_cb, AdminPanelKb.callback_data_channels.filter(), is_admin=True)
    dp.register_callback_query_handler(manage_channel, AdminChannelsListKb.callback_data.filter(), is_admin=True)
    dp.register_callback_query_handler(delete_channel, AdminDeleteChannelKb.callback_data.filter(), is_admin=True)
    dp.register_callback_query_handler(add_channel, AdminChannelsListKb.callback_data_add.filter(), is_admin=True)
    dp.register_callback_query_handler(add_group, AdminChannelsListKb.callback_data_add_group.filter(), is_admin=True)
    dp.register_callback_query_handler(edit_page_group, AdminSelectGroupToSub.page.filter(), is_admin=True)
    dp.register_callback_query_handler(info_group, AdminSelectGroupToSub.info.filter(), is_admin=True)
    dp.register_callback_query_handler(leave_group_true, AdminInfoGroup.leave_group.filter(), is_admin=True)
    dp.register_callback_query_handler(select_group, AdminSelectGroupToSub.callback_data.filter(), is_admin=True)
