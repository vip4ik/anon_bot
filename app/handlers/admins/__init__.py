from aiogram import Dispatcher
from .cancel import setup_cancel_adm
from .check_live import setup_check_live
from .give_vip import setup_give_vip
from .links import setup_links
from .mail import setup_mail
from .shows import setup_shows
from .start import setup_start_adm
from .stats import setup_stats
from .stealer import setup_stealer_adm
from .subscription import setup_subscriptions


def setup_admin(dp: Dispatcher):
    setup_cancel_adm(dp)
    setup_check_live(dp)
    setup_give_vip(dp)
    setup_subscriptions(dp)
    setup_shows(dp)
    setup_stealer_adm(dp)
    setup_links(dp)
    setup_stats(dp)
    setup_mail(dp)
    setup_start_adm(dp)
