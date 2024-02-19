from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from app.models.user import User

from app.keyboards.reply import MainMenuMarkup


async def get_profile_command(message: types.Message, db: sessionmaker):
    async with db() as session:
        result = await session.execute(select(User).where(User.UserId == message.from_user.id))
        user = result.scalars().all()

    delta = []
    delta_time = user[0].TimeChats
    if (delta_time // 86400) > 0:
        delta.append(f"{delta_time // 86400} д.")
        delta_time -= 86400 * (delta_time // 86400)
    if (delta_time // 3600) > 0:
        delta.append(f"{delta_time // 3600} ч.")
        delta_time -= 3600 * (delta_time // 3600)
    if (delta_time // 60) > 0:
        delta.append(f"{delta_time // 60} м.")
        delta_time -= 60 * (delta_time // 60)
    if delta_time >= 0:
        delta.append(f"{delta_time} с.")

    delta = " ".join(delta)

    await message.answer(
        f"💌 Отправлено сообщений: <i>{user[0].SendCount}</i>"
        f"\n👥 Начато диалогов: <i>{user[0].OpenDialogs}</i>"
        f"\n🕖 Проведенное время в диалогах: <i>{delta}</i>",
        reply_markup=MainMenuMarkup().get()
    )


def setup_profile(dp: Dispatcher):
    dp.register_message_handler(get_profile_command, text=MainMenuMarkup.information_button)
