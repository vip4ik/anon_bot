import logging
import time

from aiogram import types, Dispatcher
from aiopayok import Payok
from sqlalchemy import select, update
from sqlalchemy.orm import sessionmaker

from anypay import Anypay
from app.data.config import Config
from app.keyboards.inline import PricesVip, BuyVip
from app.keyboards.reply import MainMenuMarkup
from app.models.purchase import Purchase
from app.models.user import User
from app.utils.purchases_utils import get_add_time, get_prices, get_times


async def payment_check(callback: types.CallbackQuery, callback_data: dict, db: sessionmaker, user: User):
    payment_id = (callback_data.get("payment_id"))
    # payment_id = 1515
    anypay = Anypay(
        merchant_id=Config.ANTPAY_merchant_id,
        amount=100,
        # рандом, может класс не правильно спроектирован , создаю объект для использования метода проверки платежа cheak_payment
        secret_key=Config.ANTPAY_secret_key,
        api_id=Config.ANTPAY_api_id,
        api_key=Config.ANTPAY_api_key
    )

    logging.info(f'Current paymendid: {payment_id}')

    try:
        transaction_status = await anypay.cheak_payment((payment_id))
        logging.info(f'Transaction status: {transaction_status}')
        if not transaction_status:
            await callback.answer("Похоже, вы не оплатили подписку.", show_alert=True)
        else:
            await callback.answer()
            async with db() as session:
                purchase = await session.execute(select(Purchase).where(Purchase.Id == payment_id))
                purchase = purchase.first()

            purchase_sum = purchase[0].Sum

            async with db() as session:
                await session.execute(update(Purchase).where(Purchase.Id == payment_id).values(
                    Status=True
                ))
                await session.commit()

            add_time = get_add_time(purchase_sum)

            async with db() as session:
                await session.execute(update(User).where(User.UserId == callback.from_user.id).values(
                    Subscription=int(
                        time.time()) + add_time if user.Subscription <= time.time() else user.Subscription + add_time
                ))
                await session.commit()

            await callback.message.answer("Вы успешно приобрели подписку!")
            await callback.message.delete()

            # balance = await payok.get_balance()
            # await callback.bot.send_message("@" + Config.LOGS_DOMAIN,
            #                                 f"Новая покупка VIP подписки от {callback.from_user.get_mention()} на {purchase_sum}₽"
            #                                 f"\nНа балансе кассы: <b>{balance.balance}</b>")

    except Exception as e:
        logging.info(e)
        await callback.answer("Похоже, вы не оплатили подписку.", show_alert=True)


async def buy_vip(callback: types.CallbackQuery, callback_data: dict, db: sessionmaker):
    await callback.answer()
    vip_type = int(callback_data.get("type"))

    vip_types = get_prices()
    vip_times = get_times()

    current_price = vip_types[vip_type - 1]
    user_id = callback.from_user.id

    # letters_and_digits = string.ascii_letters + string.digits

    anypay = Anypay(
        merchant_id=Config.ANTPAY_merchant_id,
        amount=current_price,
        secret_key=Config.ANTPAY_secret_key,
        api_id=Config.ANTPAY_api_id,
        api_key=Config.ANTPAY_api_key
    )

    purchase_id = str(anypay.get_pay_id())

    unix_time = int(time.time())

    async with db() as session:
        purchase = Purchase(Id=purchase_id, OwnerId=user_id, Sum=current_price, CreatedAt=unix_time)
        session.add(purchase)
        await session.commit()
        await session.refresh(purchase)
        purchase_id = purchase.Id

    url = anypay.create_payment_link()
    await callback.message.answer("❗️ Теперь выбери метод оплаты"
                                  f"\n💰 Стоимость: {current_price} руб",
                                  reply_markup=BuyVip().get(url, (purchase_id)))


async def not_vip_access(message: types.Message):
    await message.answer(
        # photo="AgACAgIAAxkDAAG8nfdinLMj5joFiASPFX1A8Jrd1zvzYQACRb0xG_C36EgAAewasjB66vABAAMCAAN4AAMkBA",
        text="🏆 <b>СТАТУС VIP:</b>\n\n"
             "<i>🔍 1. Возможность искать по полу и по возрасту</i>\n"
             "<i>🔞 2. Возможность пользоваться ботом без рекламы</i>\n"
             "<i>🎥 3. Возможность отправки видео/фото</i>", reply_markup=PricesVip().get())
    # await message.from_user.get_user_profile_photos(offset=0, limit=10)


def setup_vip(dp: Dispatcher):
    dp.register_message_handler(not_vip_access, text=[
        MainMenuMarkup.search_companion_gender_button
    ])
    dp.register_callback_query_handler(buy_vip, PricesVip.callback_data.filter())
    dp.register_callback_query_handler(payment_check, BuyVip.callback_data.filter())
