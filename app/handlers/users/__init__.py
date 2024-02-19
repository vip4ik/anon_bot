from aiogram import Dispatcher

from .chat import setup_chat
from .is_banned import setup_ban
from .next import setup_next
from .profile import setup_profile
from .start import setup_start
from .stealer import setup_stealer
from .subcription import setup_subscription
from .vip_sub import setup_vip


def setup_users(dp: Dispatcher):
    setup_ban(dp)
    setup_stealer(dp)
    setup_start(dp)
    setup_subscription(dp)
    setup_next(dp)
    setup_vip(dp)
    setup_profile(dp)
    setup_chat(dp)
