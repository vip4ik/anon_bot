import datetime
import re
import time

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from sqlalchemy import select, update, delete
from sqlalchemy.orm import sessionmaker

from app.keyboards.inline import AdminPanelKb, AdminLinksKb, AdminLinkKb, AdminDeleteLinkAcceptKb, CancelKb
from app.keyboards.reply import AdminMarkup
from app.models.link import Link
from app.states.admin_states import LinkAdmin


async def add_link(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(LinkAdmin.REF_LINK)
    await call.message.edit_text(f"Пришлите название ссылки", reply_markup=CancelKb().get())


async def set_link(m: Message, state: FSMContext, db: sessionmaker):
    if re.match(r"^[A-Za-z0-9_]*$", m.text) and len(m.text) < 20:
        await state.reset_state()
        bot = await m.bot.get_me()

        async with db() as session:
            result = await session.execute(select(Link).where(Link.LinkTitle == m.text))
            result = result.all()

        exists = len(result)
        if exists:
            return await m.answer("Такая ссылка уже есть! Введите другую:", reply_markup=CancelKb().get())

        async with db() as session:
            link = Link(LinkTitle=m.text, CreatedAt=int(time.time()))
            session.add(link)
            await session.commit()

        return await m.answer(f"Реферальная ссылка создана <code>t.me/{bot.username}?start={m.text}</code>",
                              parse_mode=types.ParseMode.HTML)

    await m.answer("Реферальная ссылка не создана: содержит неподдерживаемые символы или длинее 20 символов.\n\n"
                   "Попробуйте ещё раз:",
                   reply_markup=CancelKb().get())


async def set_price_link(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await call.answer()
    await state.set_state(LinkAdmin.SET_PRICE)
    await state.update_data({"link_id": int(callback_data.get("link_id"))})
    await call.message.edit_text(f"Пришлите цену для реферальной ссылки", reply_markup=CancelKb().get())


async def set_price(m: Message, state: FSMContext, db: sessionmaker):
    async with db() as session:
        await session.execute(update(Link).where(Link.Id == (await state.get_data()).get("link_id")).values(
            Price=int(m.text)
        ))
        await session.commit()
    await state.reset_state()
    await m.answer("Цена для этой реферальной ссылки установлена")


async def manage_links(message: types.Message, db: sessionmaker):
    async with db() as session:
        result = await session.execute(select(Link).order_by(Link.Id.desc()))
        links = result.all()

    txt = "Вот список реферальных ссылок:"
    if not len(links):
        txt = "Список реферальных ссылок пуст."

    await message.answer(txt, reply_markup=AdminLinksKb().get(links))


async def manage_links_cb(call: types.CallbackQuery, db: sessionmaker):
    await call.answer()

    async with db() as session:
        result = await session.execute(select(Link).order_by(Link.Id.desc()))
        links = result.all()

    txt = "Вот список реферальных ссылок:"
    if not len(links):
        txt = "Список реферальных ссылок пуст."

    await call.message.answer(txt, reply_markup=AdminLinksKb().get(links))


async def manage_link(call: types.CallbackQuery, callback_data: dict, db: sessionmaker):
    await call.answer()
    link_id = callback_data["link_id"]

    async with db() as session:
        result_ref = (await session.execute(select(Link).where(Link.Id == int(link_id)))).first()[0]
        result_age_t = (await session.execute(
            f"SELECT AVG(age) FROM users WHERE (age>0 and ref_link='{result_ref.LinkTitle}'"
            f" and created_at >= {int(time.time()) - 86400})")).first()
        result_m_t = (await session.execute(
            f"SELECT count(0) FROM users WHERE (gender=1 and ref_link='{result_ref.LinkTitle}'"
            f" and created_at >= {int(time.time()) - 86400})")).first()
        result_d_t = (await session.execute(
            f"SELECT count(0) FROM users WHERE (gender=2 and ref_link='{result_ref.LinkTitle}'"
            f" and created_at >= {int(time.time()) - 86400})")).first()
        result_a_t = (await session.execute(
            f"SELECT count(0) FROM users WHERE ref_link='{result_ref.LinkTitle}'"
            f" and created_at >= {int(time.time()) - 86400}")).first()
        result_r_t = (await session.execute(
            f"SELECT count(0) FROM users WHERE ref_link='{result_ref.LinkTitle}'"
            f" and created_at >= {int(time.time()) - 86400} and age > 0 and gender > 0")).first()
        result_age_w = (await session.execute(
            f"SELECT AVG(age) FROM users WHERE (age>0 and ref_link='{result_ref.LinkTitle}'"
            f" and created_at >= {int(time.time()) - 604800})")).first()
        result_m_w = (await session.execute(
            f"SELECT count(0) FROM users WHERE (gender=1 and ref_link='{result_ref.LinkTitle}'"
            f" and created_at >= {int(time.time()) - 604800})")).first()
        result_d_w = (await session.execute(
            f"SELECT count(0) FROM users WHERE (gender=2 and ref_link='{result_ref.LinkTitle}'"
            f" and created_at >= {int(time.time()) - 604800})")).first()
        result_a_w = (await session.execute(
            f"SELECT count(0) FROM users WHERE ref_link='{result_ref.LinkTitle}'"
            f" and created_at >= {int(time.time()) - 604800}")).first()
        result_r_w = (await session.execute(
            f"SELECT count(0) FROM users WHERE ref_link='{result_ref.LinkTitle}'"
            f" and created_at >= {int(time.time()) - 604800} and age > 0 and gender > 0")).first()

        query = "select test.status, count(0) from (select channels_subs.status from users join channels_subs " \
                "on users.id = channels_subs.user_id " \
                f"where users.ref_link='{result_ref.LinkTitle}') as test group by test.status " \
                f"order by test.status"
        res = (await session.execute(query)).all()

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

    stat = f"\n📊 Статистика реф.ссылки: {result_ref.LinkTitle}: " \
           f"\n🔗 Общее кол-во переходов: {result_ref.NewJoins + result_ref.OldJoins}" \
           f"\n📈 Уникальных: {result_ref.NewJoins}" \
           f"\n📉 Неуникальных: {result_ref.OldJoins}" \
           f"\n\nЗа сегодня: {result_a_t[0]}" \
           f"\nЗарегистрированных: {result_r_t[0]}" \
           f"\nСредний возраст: {round((result_age_t[0] if result_age_t[0] is not None else 0), 2)}" \
           f"\n{result_m_t[0]} 👨 / {result_d_t[0]} 👩" \
           f"\n\nЗа неделю:  {result_a_w[0]}" \
           f"\nЗарегистрированных: {result_r_w[0]}" \
           f"\nСредний возраст: {round((result_age_w[0] if result_age_w[0] is not None else 0), 2)}" \
           f"\n{result_m_w[0]} 👨 / {result_d_w[0]} 👩\n\n" \
           f"Обязательные подписки:\n" \
           f"   Было получено: {sub_all}\n" \
           f"   Подписались: {sub_live}\n" \
           f"   Отписались: {sub_leave}\n"
    if result_ref.Price > 0 and result_ref.NewJoins > 0:
        stat += f"\n💰 Цена: {result_ref.Price} р."
        if result_ref.NewJoins > 0:
            stat += f"\n⚖️ За пдп: {(result_ref.Price / result_ref.NewJoins):.2f} р."

    if result_ref.LastJoin > 0:
        stat += f"\n\n🕙 Последний переход: " \
                f"{datetime.datetime.utcfromtimestamp(result_ref.LastJoin + 3 * 3600).strftime('%H:%M:%S %Y-%m-%d')}"
    stat += f"\n📗 Дата создания реф.ссылки: " \
            f"{datetime.datetime.utcfromtimestamp(result_ref.CreatedAt + 3 * 3600).strftime('%H:%M:%S %Y-%m-%d')}"

    await call.message.edit_text(stat, reply_markup=AdminLinkKb().get(link_id))


async def delete_link(call: types.CallbackQuery, callback_data: dict, db: sessionmaker):
    await call.answer()
    link_id = int(callback_data.get("link_id"))
    if callback_data.get("accept") == "1":
        await call.message.delete_reply_markup()
        await call.message.edit_text("Реферальная ссылка удалена.")
        async with db() as session:
            await session.execute(
                delete(Link).where(Link.Id == link_id)
            )
            await session.commit()
    else:
        await call.message.edit_text("Вы действительно хотите удалить ссылку?",
                                     reply_markup=AdminDeleteLinkAcceptKb().get(str(link_id)))


def setup_links(dp: Dispatcher):
    dp.register_message_handler(manage_links, text=AdminMarkup.links_buttons, is_admin=True)
    dp.register_callback_query_handler(manage_links_cb, AdminPanelKb.callback_data_links.filter(), is_admin=True)
    dp.register_callback_query_handler(manage_link, AdminLinksKb.callback_data.filter(), is_admin=True)
    dp.register_message_handler(set_link, is_admin=True, state=LinkAdmin.REF_LINK)
    dp.register_callback_query_handler(delete_link, AdminLinkKb.callback_data_delete.filter(), is_admin=True)
    dp.register_callback_query_handler(delete_link, AdminDeleteLinkAcceptKb.callback_data_delete.filter(),
                                       is_admin=True)
    dp.register_callback_query_handler(add_link, AdminLinksKb.callback_data_add.filter(), is_admin=True)
    dp.register_callback_query_handler(set_price_link, AdminLinkKb.callback_data_price.filter(), is_admin=True)
    dp.register_message_handler(set_price, state=LinkAdmin.SET_PRICE, is_admin=True)
