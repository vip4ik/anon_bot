import contextlib
import logging
import time

from aiogram import types, Dispatcher, Bot
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import exceptions
from aiogram.utils.exceptions import TelegramAPIError
from sqlalchemy import update, select
from sqlalchemy.orm import sessionmaker

from anypay import Anypay
from app.data.config import Config
from app.keyboards.inline import BuyFindChat, ComplaintKb
from app.keyboards.reply import MainMenuMarkup, CancelDialogMarkup
from app.models.purchase_chat import PurchaseChat
from app.models.shows import Shows
from app.models.shows_use import ShowsUse
from app.models.user import User
from app.states.user_states import UserStates
from app.utils.throttling_decorator import rate_limit


async def payment_check_chatter(callback: types.CallbackQuery, callback_data: dict, db: sessionmaker,
                                state: FSMContext):
    payment_id = str(callback_data.get("payment_id"))
    anypay = Anypay(
        merchant_id=Config.ANTPAY_merchant_id,
        amount=49,
        secret_key=Config.ANTPAY_secret_key,
        api_id=Config.ANTPAY_api_id,
        api_key=Config.ANTPAY_api_key
    )

    # data = await state.get_data()
    # companion_username = (await callback.bot.get_chat(data.get('companion'))).username
    # await callback.message.answer(f'Ссылка на упыря {companion_username}')
    try:

        transaction_status = await anypay.cheak_payment(int(payment_id))
        logging.info(f'Transaction status: {transaction_status}')

        if transaction_status == False:
            await callback.answer("Похоже, вы не оплатили этот товар.", show_alert=True)
        else:
            await callback.answer()
            async with db() as session:
                purchase = await session.execute(select(PurchaseChat).where(PurchaseChat.Id == payment_id))
                purchase = purchase.first()[0]

            # if 99 != transaction_data.amount_profit:
            #     return

            await callback.message.answer(f"Ссылка на вашего собеседника - {purchase.Answer}")
            await callback.message.delete()

    except Exception as e:
        logging.error(e)
        await callback.answer("Похоже, вы не оплатили этот товар.", show_alert=True)


async def find_chatter(message: types.Message, db: sessionmaker, state: FSMContext):
    anypay = Anypay(
        merchant_id=Config.ANTPAY_merchant_id,
        amount=49,
        secret_key=Config.ANTPAY_secret_key,
        api_id=Config.ANTPAY_api_id,
        api_key=Config.ANTPAY_api_key
    )

    purchase_id = anypay.get_pay_id()

    async with db() as session:
        purchase = PurchaseChat(Id=str(purchase_id), UserId=message.from_user.id,
                                Answer=(await state.get_data()).get("username"))
        session.add(purchase)
        await session.commit()
        await session.refresh(purchase)
        purchase_id = purchase.Id

    url = anypay.create_payment_link()
    await message.answer("После оплаты вы получите @username собеседника⚡️",
                         reply_markup=BuyFindChat().get(url, int(purchase_id)))


async def any_message(message: types.Message):
    await message.answer("Нажмите /next и начинайте общение!", reply_markup=MainMenuMarkup().get())


async def cancel_chat(m: types.Message, state: FSMContext, db: sessionmaker, storage: RedisStorage2):
    user_data = await state.get_data()
    if user_data.get("companion") is None:
        if not user_data.get("in_search"):
            await state.finish()
        await m.answer("❗️ Сейчас ты не находишься в диалоге.", reply_markup=MainMenuMarkup().get())
        return

    companion = await FSMContext(storage, user_data["companion"], user_data["companion"]).get_data()
    if companion.get("companion") is None:
        if not user_data.get("in_search"):
            await state.finish()
        await m.answer("❗️ Сейчас ты не находишься в диалоге.", reply_markup=MainMenuMarkup().get())
        return

    await FSMContext(storage, user_data["companion"], user_data["companion"]).reset_state()
    await state.finish()

    delta_time = int(time.time() - user_data["created_at"])
    delta_t = delta_time

    delta = []

    if (delta_time // 86400) > 0:
        delta.append(f"{delta_time // 86400} д.")
        delta_time -= 86400 * (delta_time // 86400)
    if (delta_time // 3600) > 0:
        delta.append(f"{delta_time // 3600} ч.")
        delta_time -= 3600 * (delta_time // 3600)
    if (delta_time // 60) > 0:
        delta.append(f"{delta_time // 60} м.")
        delta_time -= 60 * (delta_time // 60)
    if delta_time > 0:
        delta.append(f"{delta_time} с.")

    delta = " ".join(delta)

    with contextlib.suppress(exceptions.TelegramAPIError):
        await m.answer(
            f"💬 Вы закончили диалог\nДиалог продлился <i>{delta}</i>\n\n<i>Нажмите</i> /next <i>чтобы найти следующего собеседника</i>",
            reply_markup=MainMenuMarkup().get())
        await m.answer('Хотите пожаловаться на собеседника?', reply_markup=ComplaintKb().get(user_data['companion']))
        await m.bot.send_message(user_data["companion"],
                                 f"💬 Собеседник закончил диалог\nДиалог продлился <i>{delta}</i>\n\n<i>Нажмите</i> /next <i>чтобы найти следующего собеседника</i>",
                                 reply_markup=MainMenuMarkup().get())
        await m.bot.send_message(user_data["companion"], text='Хотите пожаловаться на собеседника?',
                                 reply_markup=ComplaintKb().get(m.chat.id))

    async with db() as session:
        await session.execute(update(User).where(User.UserId == m.from_user.id).values(
            SendCount=User.SendCount + user_data["send_messages"],
            OpenDialogs=User.OpenDialogs + 1,
            TimeChats=User.TimeChats + delta_t
        ))
        await session.execute(update(User).where(User.UserId == user_data["companion"]).values(
            SendCount=User.SendCount + companion["send_messages"],
            OpenDialogs=User.OpenDialogs + 1,
            TimeChats=User.TimeChats + delta_t
        ))
        await session.commit()

    await add_show(m.from_user.id, m.bot, db)
    await add_show(user_data["companion"], m.bot, db)


async def add_show(user_id: int, bot: Bot, db: sessionmaker):
    async with db() as session:
        data = await session.execute(
            f"SELECT * FROM shows WHERE (total < count) AND (shows.id NOT IN "
            f"(SELECT shows_use.show_id FROM shows_use WHERE user_id = {user_id})) LIMIT 1;")
        view_kb = InlineKeyboardMarkup()
        data = data.first()
        if data is not None:
            buttons = data[-1]
            if len(buttons) > 5:
                split_buttons = buttons.split('\n')
                for line in split_buttons:
                    line_split = line.split(',.,')
                    kb_line = []
                    for btn in line_split:
                        text = btn.split('\|/')[0]
                        # print(text)
                        url = btn.split('\|/')[-1]
                        kb = InlineKeyboardButton(text=text, url=url)
                        kb_line.append(kb)
                    else:
                        view_kb.add(*kb_line)
                        kb_line = []
            else:
                view_kb = None
            session.add(ShowsUse(ShowId=data[0], UserId=user_id))
            try:
                await bot.send_message(user_id, data[1], disable_web_page_preview=True, reply_markup=view_kb)
            except TelegramAPIError:
                return
            await session.execute(update(Shows).where(Shows.Id == data[0]).values(Total=Shows.Total + 1))
            await session.commit()


@rate_limit(1)
async def redirect_messages(message: types.Message, state: FSMContext, user: User, db: sessionmaker):
    if user.Subscription <= int(time.time()) and (
            message.photo or message.video or message.animation or message.sticker or message.voice):
        await message.answer("️⛔️ <b>Отправлять медиа файлы запрещено.</b>")
        return
    bot = message.bot

    # Check for forbidden entities
    has_forbidden_entities = False
    if message.entities or message.caption_entities:
        if any(
                entity.type in [
                    types.MessageEntityType.URL,
                    types.MessageEntityType.MENTION,
                    types.MessageEntityType.TEXT_MENTION,
                    types.MessageEntityType.TEXT_LINK,
                ]
                for entity in message.entities + message.caption_entities
        ):
            has_forbidden_entities = True

    if has_forbidden_entities:
        await message.answer("⛔️ <b>Отправлять ссылки запрещено.</b>", parse_mode=types.ParseMode.HTML)
        return

    if message.text is not None and ("bot" in message.text.lower() or "/start" in message.text.lower()):
        return

    if companion := (await state.get_data()).get("companion"):
        try:
            if message.photo:
                await bot.send_photo(companion, photo=message.photo[-1].file_id, caption=message.text)
            elif message.video:
                await bot.send_video(companion, video=message.video.file_id, caption=message.text)
            elif message.voice:
                await bot.send_voice(companion, voice=message.voice.file_id)
            elif message.sticker:
                await bot.send_sticker(companion, sticker=message.sticker.file_id)
            elif message.animation:
                await bot.send_animation(companion, animation=message.animation.file_id)
            elif message.text:
                await bot.send_message(companion, text=message.text)
                async with db() as session:
                    await session.execute(
                        f"INSERT INTO messages (user_id,text,created_at) VALUES ({message.chat.id},'{message.text}',{int(time.time())})")
                    await session.commit()
        except Exception as e:
            logging.error(e)
        with contextlib.suppress(KeyError):
            async with state.proxy() as data:
                data["send_messages"] = int(data["send_messages"]) + 1
            return

    await message.answer("❗️ Сейчас ты находишься в поиске.")


async def report_proccesing(callback: types.CallbackQuery, state: FSMContext, user: User, db: sessionmaker):
    if callback.data.split('_')[1] == 'no':
        await callback.answer('Спасибо!')
        await callback.message.delete()

        return
    else:
        suspect_id = callback.data.split('_')[-1]
        async with db() as session:
            data = await session.execute(
                f"INSERT INTO Reports (suspect_id,reported_by,created_at) VALUES ({suspect_id},{callback.from_user.id},{int(time.time())})"
            )  # sorry for f stirng ,900 rubles come on
            await session.commit()
        await callback.answer("Жалоба отправлена!")
        await callback.message.delete()


from aiogram.dispatcher.filters import Text


def setup_chat(dp: Dispatcher):
    dp.register_callback_query_handler(payment_check_chatter, BuyFindChat.callback_data.filter(), state="*")
    dp.register_callback_query_handler(report_proccesing, Text(contains='report'), state="*")

    dp.register_message_handler(find_chatter, text=CancelDialogMarkup.button_find, state=UserStates.CHAT)
    dp.register_message_handler(cancel_chat, commands="stop", state=UserStates.CHAT)
    dp.register_message_handler(cancel_chat, text=CancelDialogMarkup.button_text, state=UserStates.CHAT)
    dp.register_message_handler(redirect_messages, state=UserStates.CHAT, content_types=types.ContentType.ANY)
    dp.register_message_handler(any_message, content_types=types.ContentType.ANY)
