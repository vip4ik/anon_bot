from functools import partialmethod

from aiogram import Dispatcher
from sqlalchemy.orm import sessionmaker

from .is_admin import AdminFilter
from .is_age import NotAgeFilter
from .is_gender import NotGenderFilter
from .is_group import GroupFilter
from .is_not_member import NotMemberFilter
from .is_vip_access import IsVipFilter
from .is_banned import IsBanFilter


def setup(dp: Dispatcher, session: sessionmaker):
    AdminFilter.check = partialmethod(AdminFilter.check, session)
    dp.filters_factory.bind(AdminFilter)
    dp.filters_factory.bind(GroupFilter)
    dp.filters_factory.bind(IsBanFilter)
    dp.filters_factory.bind(NotGenderFilter)
    dp.filters_factory.bind(NotAgeFilter)
    dp.filters_factory.bind(NotMemberFilter)
    dp.filters_factory.bind(IsVipFilter)
