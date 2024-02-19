from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from sqlalchemy import select, delete
from sqlalchemy.orm import sessionmaker

from app.keyboards.inline import ShowsManageKb, ShowManageKb, CancelKb
from app.keyboards.reply import AdminMarkup
from app.models.shows import Shows
from app.models.shows_use import ShowsUse
from app.states.admin_states import AddShow


async def manage_shows(message: types.Message, db: sessionmaker):
    async with db() as session:
        result = await session.execute(select(Shows))
        result = result.all()
    await message.answer("Используйте кнопки для управления уникальными показами",
                         reply_markup=ShowsManageKb().get(result))


async def manage_show(callback: types.CallbackQuery, callback_data: dict, db: sessionmaker):
    await callback.answer()
    show_id = int(callback_data.get("show_id"))
    async with db() as session:
        show = await session.execute(select(Shows).where(Shows.Id == show_id))
        show = show.first()
    await callback.message.answer(
        f"Показы ID: {show_id}\nНужное количество: {show[0].Count}\nУникальных показов: {show[0].Total}\n\nСообщение:",
        reply_markup=ShowManageKb().get(show_id, 0))
    await callback.message.answer(show[0].Message)


async def delete_show(call: types.CallbackQuery, callback_data: dict, db: sessionmaker):
    await call.answer()
    show_id = int(callback_data.get("show_id"))
    if str(callback_data.get("agreed")) == "1":
        await call.message.delete()
        await call.message.answer("Показы успешно удалены.")
        async with db() as session:
            await session.execute(delete(ShowsUse).where(ShowsUse.ShowId == show_id))
            await session.execute(
                delete(Shows).where(Shows.Id == show_id)
            )
            await session.commit()
    else:
        await call.message.answer("Вы действительно хотите удалить показ?",
                                  reply_markup=ShowManageKb().get(show_id, 1))


async def add_show(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AddShow.Text)
    await callback.message.answer("Введите текст в следующем сообщении:", reply_markup=CancelKb().get())


async def add_show_text(message: types.Message, state: FSMContext):
    btns_txt = ''
    if message.reply_markup:
        btns = message.reply_markup.inline_keyboard
        for line in btns:
            for i in line:
                btns_txt += f'{i.text}\|/{i.url},.,'
            else:
                btns_txt = btns_txt[:-3]
                btns_txt += f'\n'
        btns_txt = btns_txt[:-1]
    await state.update_data(text=message.html_text, btns_txt=btns_txt)
    await state.set_state(AddShow.Count)
    await message.answer("Введите количество показов в следующем сообщении:", reply_markup=CancelKb().get())


async def add_show_count(message: types.Message, state: FSMContext, db: sessionmaker):
    error = False
    count = 0
    try:
        count = int(message.text)
        if count <= 0:
            error = True
    except ValueError:
        error = True

    if not error:
        async with db() as session:
            ad = Shows(
                Message=(await state.get_data()).get("text"),
                Buttons=(await state.get_data()).get("btns_txt"),
                Count=count
            )
            session.add(ad)
            await session.commit()
        await state.finish()
        await message.answer("Показы успешно добавлены")
    else:
        await message.answer("Введите количество показов больше нуля:", reply_markup=CancelKb().get())


def setup_shows(dp: Dispatcher):
    dp.register_message_handler(manage_shows, text=AdminMarkup.shows_button, is_admin=True)
    dp.register_callback_query_handler(manage_show, ShowsManageKb.callback_data_stats.filter(), is_admin=True)
    dp.register_callback_query_handler(add_show, ShowsManageKb.callback_data_add.filter(), is_admin=True)
    dp.register_callback_query_handler(delete_show, ShowManageKb.callback_data_delete.filter(), is_admin=True)
    dp.register_message_handler(add_show_text, state=AddShow.Text, is_admin=True)
    dp.register_message_handler(add_show_count, state=AddShow.Count, is_admin=True)
