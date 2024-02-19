from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from app.models.user import User

from app.keyboards.reply import MainMenuMarkup


async def is_banned(message: types.Message, db: sessionmaker):
    await message.answer("Вы заблокированы")


def setup_ban(dp: Dispatcher):
    dp.register_message_handler(is_banned,is_banned=True,state='*')