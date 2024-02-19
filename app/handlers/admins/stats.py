import time

import aiofiles
from aiogram import Dispatcher, types
from aiogram.types import InputFile
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.keyboards.reply import AdminMarkup
from app.models.user import User


async def bot_stats(message: types.Message, db: sessionmaker):
    async with db() as session:
        result_all = (await session.execute("SELECT COUNT(1) FROM users")).all()
        result_active = (await session.execute("SELECT COUNT(1) FROM users WHERE deactivated=false")).all()
        result_gender = (await session.execute(
            "select gender, count(0) from users where deactivated=false group by gender order by gender")).all()
        result_countries = (await session.execute(
            "select language_code, count(0) as c from users where deactivated=false "
            "group by language_code order by c desc limit 10")).all()
        result_age_t = (await session.execute(
            f"SELECT AVG(age) FROM users WHERE (age>0 and created_at >= {int(time.time()) - 86400})")).first()
        result_m_t = (await session.execute(
            f"SELECT count(0) FROM users WHERE (gender=1 and created_at >= {int(time.time()) - 86400})")).first()
        result_d_t = (await session.execute(
            f"SELECT count(0) FROM users WHERE (gender=2 and created_at >= {int(time.time()) - 86400})")).first()
        result_a_t = (await session.execute(
            f"SELECT count(0) FROM users WHERE created_at >= {int(time.time()) - 86400}")).first()
        result_samorost_t = (await session.execute(
            f"SELECT COUNT(1) FROM users WHERE (ref_link = '') IS NOT FALSE and created_at >= {int(time.time()) - 86400}")).first()[
            0]
        result_age_w = (await session.execute(
            f"SELECT AVG(age) FROM users WHERE (age>0 and created_at >= {int(time.time()) - 604800})")).first()
        result_m_w = (await session.execute(
            f"SELECT count(0) FROM users WHERE (gender=1 and created_at >= {int(time.time()) - 604800})")).first()
        result_d_w = (await session.execute(
            f"SELECT count(0) FROM users WHERE (gender=2 and created_at >= {int(time.time()) - 604800})")).first()
        result_a_w = (await session.execute(
            f"SELECT count(0) FROM users WHERE created_at >= {int(time.time()) - 604800}")).first()
        result_samorost_w = (await session.execute(
            f"SELECT COUNT(1) FROM users WHERE (ref_link = '') IS NOT FALSE and created_at >= {int(time.time()) - 604800}")).first()[
            0]

    ans = f"👤 <b>Всего</b> {result_all[0][0]} <i>пользователей</i>\n" \
          f"🗣 <b>Живых:</b> {result_active[0][0]}\n" \
          f"☠️ <b>Мертвых:</b> {result_all[0][0] - result_active[0][0]}\n"

    ans += f"\nЗа сегодня: {result_a_t[0]}" \
           f"\nСредний возраст: {round((result_age_t[0] if result_age_t[0] is not None else 0), 2)}" \
           f"\nСаморост: {result_samorost_t}" \
           f"\n{result_m_t[0]} 👨 / {result_d_t[0]} 👩" \
           f"\n\nЗа неделю:  {result_a_w[0]}" \
           f"\nСредний возраст: {round((result_age_w[0] if result_age_w[0] is not None else 0), 2)}" \
           f"\nСаморост: {result_samorost_w}" \
           f"\n{result_m_w[0]} 👨 / {result_d_w[0]} 👩"

    ans += f"\n\n👀 <b>Без пола:</b> {result_gender[0][1]}\n" \
           f"👨 <b>Мужского пола:</b> {result_gender[1][1]} " \
           f"<i>({((result_gender[1][1] / result_active[0][0]) * 100):.1f}%)</i>\n" \
           f"👩 <b>Женского пола:</b> {result_gender[2][1]} " \
           f"<i>({((result_gender[2][1] / result_active[0][0]) * 100):.1f}%)</i>\n\n"

    ans += "<b>Страны</b>"
    for country in result_countries:
        data_code = emoji_language_code(country[0])
        ans += f"\n{data_code[1]} <b>{data_code[0]}</b> - <i>{country[1]} пользователей</i>"

    await message.answer(ans)


def emoji_language_code(text):
    dict_codes = {
        "ru": ["Россия", "🇷🇺"],
        "uk": ["Украина", "🇺🇦"],
        "uz": ["Узбекистан", "🇺🇿 "],
        "en": ["США", "🇺🇸"],
        "ar": ["Аргентина", "🇦🇷"],
        "fr": ["Франция", "🇫🇷"],
        "ro": ["Романия", "🇷🇴"],
        "tr": ["Турция", "🇹🇷"],
        "id": ["Индонезия", "🇮🇩"],
        "kk": ["Казахстан", "🇰🇿"],
    }
    return dict_codes[text] if text in dict_codes else [text, "🌎"]


async def admin_users_base(message: types.Message, db: sessionmaker):
    async with db() as session:
        result = await session.execute(select(User.UserId).where(User.Deactivated == False))
        users = result.all()

    txt = ""
    for user in users:
        txt += f"{user[0]}\n"

    async with aiofiles.open('users.txt', 'w') as f:
        await f.write(txt)

    await message.answer_document(InputFile('users.txt'))


def setup_stats(dp: Dispatcher):
    dp.register_message_handler(bot_stats, text=AdminMarkup.stats_button, is_admin=True)
    dp.register_message_handler(admin_users_base, text=AdminMarkup.users_button, is_admin=True)
