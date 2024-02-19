import hashlib
import json
import random

import aiohttp


class Anypay():

    def __init__(self, merchant_id: int, amount: int, secret_key: str, api_id: str, api_key: str,
                 currency: str = 'RUB'):
        pay_id = random.randint(1, 99999999999)

        self.url_pay = 'https://anypay.io/merchant'
        self.url_transaction = f'https://anypay.io/api/payments/{api_id}'
        self.amount = amount
        self.pay_id = pay_id
        self.currency = currency
        self.merchant_id = merchant_id
        self.secret_key = secret_key
        self.api_id = api_id
        self.api_key = api_key

    def create_sign(self):
        spliter = f'{self.currency}:{self.amount}:{self.secret_key}:{self.merchant_id}:{self.pay_id}'
        sign = hashlib.md5(spliter.encode()).hexdigest()
        return sign

    def create_payment_sign(self):
        sign = hashlib.sha256(f'payments{self.api_id}{self.merchant_id}{self.api_key}'.encode())
        return sign.hexdigest()

    def create_payment_link(self):
        sign = self.create_sign()
        link = f'{self.url_pay}?merchant_id={self.merchant_id}&pay_id={self.pay_id}&amount={self.amount}&sign={sign}'
        return link

    async def cheak_payment(self, pay_id: int = None):
        sign = self.create_payment_sign()
        params = {'sign': sign, 'project_id': self.merchant_id, 'pay_id': pay_id}
        session = aiohttp.ClientSession()
        async with session.get(self.url_transaction, params=params) as resp:
            print(resp)
            paymend_status = False
            is_paid = 'paid'
            resp = await resp.json()
            print(resp)
            payments = (resp.get('result')).get('payments')
            try:
                for payment_id in payments:
                    transaction = payments.get(payment_id)
                    print(transaction.get('status'))
                    if transaction.get('status') == is_paid:
                        paymend_status = True
            except TypeError:
                pass
            await session.close()
            return paymend_status

    def get_pay_id(self):
        return self.pay_id
