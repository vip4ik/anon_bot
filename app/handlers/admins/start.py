from aiogram import Dispatcher, types
from aiogram import md
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from sqlalchemy import delete
from sqlalchemy.orm import sessionmaker

from app.keyboards.reply import AdminMarkup, AdminReportsMarkup
from app.models.user import User
from app.states.admin_states import AdminReports


async def check_reports(message: types.Message, state: FSMContext, db: sessionmaker):
    async with db() as session:
        result = await session.execute('''
            SELECT
  Reports.*, counter.count
FROM
  Reports
LEFT JOIN (
  SELECT
    Reports.suspect_id, count(Reports.suspect_id) as count
  FROM
    Reports
  GROUP BY
    Reports.suspect_id
) counter ON counter.suspect_id = Reports.suspect_id
WHERE Reports.suspect_id is not null
ORDER BY
  counter.count DESC LIMIT 1''')
    if result:
        suspect_id = None
        for i in result:
            id = i[0]
            suspect_id = i[1]
            count = i[-1]
        await AdminReports.admin_report.set()
        if suspect_id is None:
            await message.answer("Тут никого")
            await admin_start(message, state)
            return
        async with db() as session:
            messages = await session.execute(
                f'SELECT text FROM messages WHERE user_id = {suspect_id} ORDER BY created_at DESC LIMIT 1')
        text = ''
        for msg in messages:
            text += f'{md.quote_html(msg)}'
        add_info = ''
        try:
            sus_data = await message.bot.get_chat(suspect_id)
            add_info += f'Имя: {sus_data.first_name}\nЮзер: @{sus_data.username}'

        except Exception:
            pass
        add_info = md.quote_html(add_info)
        await message.answer(
            f'Жалоба на \n✉️Сообщение: <b>{text}</b>\n{suspect_id}\n❗️Кол-во: <b>{count}</b>\n\n{add_info}',
            reply_markup=AdminReportsMarkup().get())
        await state.update_data(to_user_id=suspect_id)


async def admin_report_processing(message: types.Message, state: FSMContext, db: sessionmaker):
    report = await state.get_data()
    to_user_id = report.get('to_user_id')
    if message.text == '✅Пропустить':
        async with db() as session:
            data = await session.execute(
                f"DELETE FROM reports WHERE suspect_id = {to_user_id}")
            await session.commit()
    elif message.text == '❌Забанить':
        async with db() as session:
            data = await session.execute(
                f"DELETE FROM reports WHERE suspect_id = {to_user_id}")
            data = await session.execute(
                f"UPDATE users SET is_banned = True WHERE id = {to_user_id}")
            await session.commit()
    else:
        await admin_start(message, state)
        return
    await check_reports(message, state, db)


async def admin_delete(m: Message, db: sessionmaker):
    await m.answer("ok")
    async with db() as session:
        await session.execute(delete(User).where(User.UserId == m.from_user.id))
        await session.commit()


async def admin_start(message: Message, state: FSMContext):
    await state.finish()
    await message.answer("Используйте кнопки", reply_markup=AdminMarkup().get())


def setup_start_adm(dp: Dispatcher):
    dp.register_message_handler(check_reports, text=AdminMarkup.reports_button, is_admin=True)
    dp.register_message_handler(admin_report_processing,
                                text=[AdminReportsMarkup.ban_report_button, AdminReportsMarkup.skip_report_button,
                                      AdminReportsMarkup.cancel_report_button], is_admin=True,
                                state=AdminReports.admin_report)
    dp.register_message_handler(admin_delete, commands="delete", is_admin=True)
    dp.register_message_handler(admin_start, commands="admin", is_admin=True)
