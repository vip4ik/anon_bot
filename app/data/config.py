from typing import NamedTuple

from environs import Env


class Config(NamedTuple):
    __env = Env()
    __env.read_env()

    BOT_TOKEN = __env.str("BOT_TOKEN")
    ADMINS = __env.list("ADMINS")
    DBNAME = __env.str("dbname")
    USER = __env.str("user")
    PASSWORD = __env.str("password")
    HOST = __env.str("host")
    LOGS_DOMAIN = __env.str("logs")

    ANTPAY_merchant_id = __env.int('ANTPAY_merchant_id')
    ANTPAY_secret_key = __env.str('ANTPAY_secret_key')
    ANTPAY_api_id = __env.str('ANTPAY_api_id')
    ANTPAY_api_key = __env.str('ANTPAY_api_key')

    stiller_message_file = 'app/data/stiller'
