from aiogram import Dispatcher

from .acl import ACLMiddleware
from .database import DatabaseMiddleware
from .sub import SUBMiddleware
from .throttling import ThrottlingMiddleware


def setup(dp: Dispatcher):
    dp.setup_middleware(DatabaseMiddleware())
    dp.setup_middleware(ACLMiddleware())
    dp.setup_middleware(SUBMiddleware())
    dp.setup_middleware(ThrottlingMiddleware())
