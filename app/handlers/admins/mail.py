import asyncio
import contextlib

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, Message, ContentTypes
from aiogram.utils import exceptions
from sqlalchemy import select, update, insert
from sqlalchemy.orm import sessionmaker

from app.data.config import Config
from app.keyboards.inline import MailsKb, AddTypeMailKb, CancelKb, AcceptMailKb
from app.keyboards.reply import AdminMarkup
from app.models.mail import Mail
from app.models.user import User
from app.states.admin_states import MailShow, MailStart, MailState


async def bot_mails(message: types.Message):
    await message.answer("Используйте кнопки для управления рассылками", reply_markup=MailsKb().get())


async def mails_add(query: types.CallbackQuery, state: FSMContext):
    await query.answer("")
    await query.message.answer("Выберите тип рассылки:", reply_markup=AddTypeMailKb().get())
    await state.set_state(MailState.Type)


async def mails_show(query: types.CallbackQuery, state: FSMContext):
    await query.answer("")
    await state.set_state(MailShow.Id)
    await query.message.answer("Введите айди рассылки в следующем сообщении", reply_markup=CancelKb().get())


async def mails_start(query: types.CallbackQuery, state: FSMContext):
    await query.answer("")

    await state.set_state(MailStart.Id)
    await query.message.answer("Введите айди рассылки в следующем сообщении", reply_markup=CancelKb().get())


async def mails_start_id(message: types.Message, state: FSMContext, db: sessionmaker):
    async with db() as session:
        result = await session.execute(select(Mail).where(Mail.MessageId == int(message.text)))

    if result is None:
        await message.answer("Рассылки не существует")
        await state.finish()
        return

    async with state.proxy() as data:
        data["mail_id"] = int(message.text)

    result = result.first()
    reply_markup = markup_from_string(result[0].Buttons) if result[0].Buttons is not None else None

    if result[0].ContentType == "photo":
        await message.bot.send_photo(
            chat_id=message.from_user.id,
            caption=result[0].Text,
            photo=result[0].FileId,
            reply_markup=reply_markup,
        )
    elif result[0].ContentType == "video":
        await message.bot.send_video(
            chat_id=message.from_user.id,
            caption=result[0].Text,
            video=result[0].FileId,
            reply_markup=reply_markup,
        )
    elif result[0].ContentType == "animation":
        await message.bot.send_animation(
            chat_id=message.from_user.id,
            caption=result[0].Text,
            animation=result[0].FileId,
            reply_markup=reply_markup,
        )
    else:
        await message.bot.send_message(
            chat_id=message.from_user.id,
            text=result[0].Text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

    await message.answer("Потвердите запуск рассылки", reply_markup=AcceptMailKb().get())
    await state.set_state(MailStart.Accept)


async def mails_start_accept(query: types.CallbackQuery, state: FSMContext, db: sessionmaker):
    mail_id = (await state.get_data()).get("mail_id")
    await state.finish()
    await query.message.delete_reply_markup()

    async with db() as session:
        result = await session.execute(select(Mail).where(Mail.MessageId == int(mail_id)))
        users_count = await session.execute('SELECT COUNT(0) FROM users')

    bot = query.bot

    result = result.first()[0]
    users_count = users_count.first()[0]

    need_count = users_count  # users_count

    text = f"ℹ️ Рассылка начата!\n" \
           f"👫 Всего разослать: {need_count}\n"
    info_message = await bot.send_message(text=text, chat_id=f"{Config.LOGS_DOMAIN}")

    chunk = 0
    chunk_size = 5000

    count_total = count_send = count_errors = 0
    blocked_users = []

    while count_total < need_count:

        get_chunk = min(chunk_size, need_count - count_total)
        async with db() as session:
            users_chunk = await session.execute(
                select(User.UserId, User.Deactivated).limit(get_chunk).offset(chunk * chunk_size).order_by(
                    User.CreatedAt.asc()))

        users_chunk = users_chunk.all()
        count_total += len(users_chunk)

        step = 50
        users_chunk = [user_[0] for user_ in users_chunk]
        parts = [users_chunk[i:i + step] for i in range(0, len(users_chunk), step)]

        for sub_part in parts:
            offset_step = 0
            send_data = []
            for user_step in sub_part:
                if offset_step % 2 == 0:
                    if result.ContentType == "photo":
                        send_data.append(asyncio.ensure_future(bot.send_photo(
                            chat_id=user_step,
                            caption=result.Text,
                            photo=result.FileId,
                            reply_markup=markup_from_string(result.Buttons),
                        )))
                    elif result.ContentType == "video":
                        send_data.append(asyncio.ensure_future(bot.send_video(
                            chat_id=user_step,
                            caption=result.Text,
                            video=result.FileId,
                            reply_markup=markup_from_string(result.Buttons),
                        )))
                    elif result.ContentType == "animation":
                        send_data.append(asyncio.ensure_future(bot.send_animation(
                            chat_id=user_step,
                            caption=result.Text,
                            animation=result.FileId,
                            reply_markup=markup_from_string(result.Buttons),
                        )))
                    else:
                        send_data.append(asyncio.ensure_future(bot.send_message(
                            chat_id=user_step,
                            text=result.Text,
                            reply_markup=markup_from_string(result.Buttons),
                            disable_web_page_preview=True
                        )))
                else:
                    send_data.append(asyncio.ensure_future(bot.copy_message(
                        chat_id=user_step,
                        from_chat_id=Config.LOGS_DOMAIN,
                        message_id=mail_id,
                        reply_markup=markup_from_string(result.Buttons),
                    )))
                offset_step += 1

            response = await asyncio.gather(*send_data, return_exceptions=True)
            for stepik in range(len(response)):
                chunk_data = response[stepik]
                if isinstance(chunk_data, (exceptions.RetryAfter,)):
                    print("timeout")
                    count_errors += 1
                    await asyncio.sleep(chunk_data.timeout)
                elif isinstance(chunk_data,
                                (exceptions.BotBlocked, exceptions.UserDeactivated, exceptions.ChatNotFound), ):
                    count_errors += 1
                    blocked_users.append(sub_part[stepik])
                    print((sub_part[stepik]))
                elif isinstance(chunk_data, Exception):
                    count_errors += 1
                elif chunk_data:
                    count_send += 1

            await asyncio.sleep(1)

        chunk += 1

        if len(blocked_users) > 0:
            async with db() as session:
                await session.execute(update(User).where(User.UserId.in_(blocked_users)).values(Deactivated=True))
                await session.commit()
            blocked_users = []

        text = f"ℹ️ Рассылка в процессе.\n" \
               f"👫 Всего обработано: {count_total}/{need_count} ({(count_total / need_count) * 100:.2f}%)\n" \
               f"✅ Успешно отправилось: {count_send}\n" \
               f"❌ Не смогли отправить: {count_errors}\n"

        with contextlib.suppress(exceptions.TelegramAPIError):
            await info_message.edit_text(text=text)

    if len(blocked_users) > 0:
        async with db() as session:
            await session.execute(update(User).where(User.UserId.in_(blocked_users)).values(Deactivated=True))
            await session.commit()

    await query.message.answer("Рассылка закончена")


async def mails_show_id(message: types.Message, state: FSMContext, db: sessionmaker):
    await state.finish()

    async with db() as session:
        result = await session.execute(select(Mail).where(Mail.MessageId == int(message.text)))

    if result is None:
        await message.answer("Рассылки не существует")
        return

    result = result.first()
    reply_markup = markup_from_string(result[0].Buttons) if result[0].Buttons is not None else None

    if result[0].ContentType == "photo":
        await message.bot.send_photo(
            chat_id=message.from_user.id,
            caption=result[0].Text,
            photo=result[0].FileId,
            reply_markup=reply_markup,
        )
    elif result[0].ContentType == "video":
        await message.bot.send_video(
            chat_id=message.from_user.id,
            caption=result[0].Text,
            video=result[0].FileId,
            reply_markup=reply_markup,
        )
    elif result[0].ContentType == "animation":
        await message.bot.send_animation(
            chat_id=message.from_user.id,
            caption=result[0].Text,
            animation=result[0].FileId,
            reply_markup=reply_markup,
        )
    else:
        await message.bot.send_message(
            chat_id=message.from_user.id,
            text=result[0].Text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )


def parser_keyboard(reply_markup: InlineKeyboardMarkup = None):
    if reply_markup is not None and "inline_keyboard" in reply_markup:
        markup = []
        for button_row in reply_markup["inline_keyboard"]:
            markup_row = []
            for button in button_row:
                markup_row.append(button["text"] + " " + button["url"])
            markup.append(" && ".join(markup_row))
        return "\n".join(markup)
    else:
        return "None"


def parser_media(message: Message):
    file_id = ""
    if message.content_type == ContentTypes.PHOTO[0]:
        file_id = message.photo[-1].file_id
    elif message.content_type == ContentTypes.VIDEO[0]:
        file_id = message.video.file_id
    elif message.content_type == ContentTypes.ANIMATION[0]:
        file_id = message.animation.file_id

    return message.content_type, file_id


async def mails_add_full_copy(message: types.Message, state: FSMContext, db: sessionmaker):
    await state.finish()

    reply_markup = parser_keyboard(message.reply_markup)
    media = parser_media(message)
    text_message = message.html_text if message.html_text is not None else ""

    if media[0] == "photo":
        result = await message.bot.send_photo(
            chat_id=Config.LOGS_DOMAIN,
            caption=text_message,
            photo=media[1],
            reply_markup=message.reply_markup,
        )
    elif media[0] == "video":
        result = await message.bot.send_video(
            chat_id=Config.LOGS_DOMAIN,
            caption=text_message,
            video=media[1],
            reply_markup=message.reply_markup,
        )
    elif media[0] == "animation":
        result = await message.bot.send_animation(
            chat_id=Config.LOGS_DOMAIN,
            caption=text_message,
            animation=media[1],
            reply_markup=message.reply_markup,
        )
    else:
        result = await message.bot.send_message(
            chat_id=Config.LOGS_DOMAIN,
            text=text_message,
            reply_markup=message.reply_markup,
            disable_web_page_preview=True
        )

    async with db() as session:
        await session.execute(insert(Mail).values({
            "message_id": result.message_id,
            "buttons": reply_markup,
            "text": text_message,
            "file_id": media[1],
            "content_type": media[0],
        }))
        await session.commit()

    await message.answer(f"Успешно, ID рассылки - {result.message_id}")


async def mails_add_type(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await query.answer("")
    mail_type = int(callback_data.get("type"))
    if mail_type == 0:
        await state.set_state(MailState.Text)
        msg = "Пришлите текст для рассылки в следующем сообщении"
    elif mail_type == 1:
        await state.set_state(MailState.Image)
        msg = "Пришлите вложение для рассылки в следующем сообщении"
    else:
        await state.set_state(MailState.FullCopy)
        msg = "Пришлите сообщение для полного копирования"

    await query.message.answer(msg, reply_markup=CancelKb().get())


async def mails_add_image(message: types.Message, state: FSMContext):
    if message.photo is None:
        await message.answer("Пришлите вложение для рассылки еще раз", reply_markup=CancelKb().get())
        return

    photo_file_id = message.photo[-1].file_id
    async with state.proxy() as data:
        data["image"] = photo_file_id

    await state.set_state(MailState.Text)
    await message.answer("Пришлите текст для рассылки в следующем сообщении", reply_markup=CancelKb().get())


async def mails_add_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["text"] = message.html_text

    await state.set_state(MailState.Buttons)
    await message.answer("Пришлите кнопки для рассылки в следующем сообщении\n\n* Если клавиатура не нужна, "
                         "отправьте "
                         "None", reply_markup=CancelKb().get())


def markup_from_string(buttons):
    markup = types.InlineKeyboardMarkup()
    if buttons != 'None':
        for row in buttons.split("\n"):
            service_buttons = list()
            for uwe in row.split("&&"):
                uwe = " ".join(uwe.split())
                service_buttons.append(types.InlineKeyboardButton(
                    text=" ".join(uwe.split(" ")[0:len(uwe.split(" ")) - 1]),
                    url=uwe.split(" ")[-1],
                ))
            markup.add(*service_buttons)

    return markup


async def mails_add_buttons(message: types.Message, state: FSMContext, db: sessionmaker):
    async with state.proxy() as data:
        data["buttons"] = message.text

    data = await state.get_data()
    reply_markup = markup_from_string(data["buttons"]) if data["buttons"] is not None else None

    if "image" in data:
        result = await message.bot.send_photo(
            chat_id=Config.LOGS_DOMAIN,
            caption=data["text"],
            photo=data["image"],
            reply_markup=reply_markup,
        )
    else:
        result = await message.bot.send_message(
            chat_id=Config.LOGS_DOMAIN,
            text=data["text"],
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

    async with db() as session:
        await session.execute(insert(Mail).values({
            "message_id": result.message_id,
            "buttons": data["buttons"],
            "text": data["text"],
            "file_id": data["image"] if "image" in data else None,
            "content_type": "photo" if "image" in data else "text"
        }))
        await session.commit()

    await state.finish()
    await message.answer(f"Успешно, ID рассылки - {result.message_id}")


def setup_mail(dp: Dispatcher):
    dp.register_message_handler(bot_mails, text=AdminMarkup.mails_button, is_admin=True)

    dp.register_message_handler(mails_show_id, state=MailShow.Id, is_admin=True)
    dp.register_message_handler(mails_start_id, state=MailStart.Id, is_admin=True)
    dp.register_message_handler(mails_add_image, state=MailState.Image, content_types=["photo", "text"], is_admin=True)
    dp.register_message_handler(mails_add_text, state=MailState.Text, is_admin=True)
    dp.register_message_handler(mails_add_full_copy, state=MailState.FullCopy, content_types=types.ContentType.ANY,
                                is_admin=True)
    dp.register_message_handler(mails_add_buttons, state=MailState.Buttons, is_admin=True)

    dp.register_callback_query_handler(mails_add, MailsKb.callback_data_create.filter(), is_admin=True)
    dp.register_callback_query_handler(mails_show, MailsKb.callback_data_show.filter(), is_admin=True)
    dp.register_callback_query_handler(mails_add_type, AddTypeMailKb.callback_data_type.filter(), state=MailState.Type,
                                       is_admin=True)
    dp.register_callback_query_handler(mails_start, MailsKb.callback_data_start.filter(), is_admin=True)
    dp.register_callback_query_handler(mails_start_accept, state=MailStart.Accept, is_admin=True)
