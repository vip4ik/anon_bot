from typing import List

from aiogram.utils.callback_data import CallbackData

from app.models.channel import Channel
from app.utils.markup_constructor import InlineMarkupConstructor


class CancelKb(InlineMarkupConstructor):

    def get(self):
        schema = [1]
        actions = [
            {'text': "Отмена", 'callback_data': "cancel"},
        ]
        return self.markup(actions, schema)


class MailsKb(InlineMarkupConstructor):
    callback_data_create = CallbackData("mail_create")
    callback_data_start = CallbackData("mail_start")
    callback_data_show = CallbackData("mail_show")

    def get(self):
        schema = [1, 1, 1]
        actions = [
            {'text': "Создать рассылку", 'callback_data': self.callback_data_create.new()},
            {'text': "Запустить рассылку", 'callback_data': self.callback_data_start.new()},
            {'text': "Увидеть рассылку", 'callback_data': self.callback_data_show.new()},
        ]
        return self.markup(actions, schema)


class AddTypeMailKb(InlineMarkupConstructor):
    callback_data_type = CallbackData("add_type", "type")

    def get(self):
        schema = [1, 1]
        actions = [
            # {'text': "Текст", 'callback_data': self.callback_data_type.new(0)},
            # {'text': "С вложением", 'callback_data': self.callback_data_type.new(1)},
            {'text': "copy message", 'callback_data': self.callback_data_type.new(3)},
            {'text': "Отмена", 'callback_data': "cancel"},
        ]
        return self.markup(actions, schema)


class AcceptMailKb(InlineMarkupConstructor):
    callback_data = CallbackData("accept")

    def get(self):
        schema = [1, 1]
        actions = [
            {'text': "✅ Подтвердить", 'callback_data': self.callback_data.new()},
            {'text': "Отмена", 'callback_data': "cancel"},
        ]
        return self.markup(actions, schema)


class AdminChannelsListKb(InlineMarkupConstructor):
    callback_data = CallbackData("channel", "channel_id")
    callback_data_add = CallbackData("add_channel")
    callback_data_add_group = CallbackData("add_group")

    def get(self, channel_list: List[Channel]):
        actions = []
        for channel in channel_list:
            mark = "[BOT]" if channel[0].IsBot else ""
            actions.append(
                {'text': f"{channel[0].ChannelTitle} {mark}", 'cb': self.callback_data.new(channel[0].ChannelId)})
        schema = [1] * len(channel_list)
        actions.append({'text': "Добавить канал/бота", 'cb': self.callback_data_add.new()})
        actions.append({'text': "Добавить группу", 'cb': self.callback_data_add_group.new()})
        schema += [1, 1]
        return self.markup(actions, schema)


class AdminPanelKb(InlineMarkupConstructor):
    callback_data_admins = CallbackData('admins')
    callback_data_stats = CallbackData('stats')
    callback_data_channels = CallbackData('channels')
    callback_data_mails = CallbackData('mails')
    callback_data_links = CallbackData('links')
    callback_data_shows = CallbackData('shows')
    callback_data_hide = CallbackData('cancel')
    callback_data_file = CallbackData('users_file')

    def get(self):
        schema = [1, 1, 1, 1, 1, 1, 1, 1]
        actions = [
            {'text': "Админы", 'callback_data': self.callback_data_admins.new()},
            {'text': "Статистика", 'callback_data': self.callback_data_stats.new()},
            {'text': "Каналы", 'callback_data': self.callback_data_channels.new()},
            {'text': "Рассылка", 'callback_data': self.callback_data_mails.new()},
            {'text': "Реф. ссылки", 'callback_data': self.callback_data_links.new()},
            {'text': "Показы", 'callback_data': self.callback_data_shows.new()},
            {'text': "Скачать базу", 'callback_data': self.callback_data_file.new()},
            {'text': "⏏️ Скрыть панель", 'callback_data': self.callback_data_hide.new()},
        ]
        return self.markup(actions, schema)


class SubscriptionKb(InlineMarkupConstructor):
    def get(self, channels_list: List[Channel]):
        actions = []
        i = 0
        for channel in channels_list:
            i += 1
            title = "Бот" if channel[0].IsBot else "Канал"
            actions.append({'text': f"{title} #{i}", 'url': channel[0].ChannelLink})
        schema = int(len(channels_list) / 2) * [2]
        if len(channels_list) % 2 != 0:
            schema += [1]
        actions.append({'text': "✅ Проверить подписку", 'cb': "check_sub"})
        schema += [1]
        return self.markup(actions, schema)


class SubscriptionForVal(InlineMarkupConstructor):
    def get(self, channels_list: List[Channel]):
        actions = []
        i = 0
        for channel in channels_list:
            i += 1
            title = "Бот" if channel[0].IsBot else "Канал"
            actions.append({'text': f"{title} #{i}", 'url': channel[0].ChannelLink})
        schema = int(len(channels_list) / 2) * [2]
        if len(channels_list) % 2 != 0:
            schema += [1]
        actions.append({'text': "✅ Я подписался", 'cb': "check_sub"})
        schema += [1]
        return self.markup(actions, schema)


class AnswerVal(InlineMarkupConstructor):
    answer_callback_data = CallbackData('answer_callback_data', 'user_id')

    def get(self, user_id: int):
        actions = [{'text': f"🗯 Ответить", 'cb': self.answer_callback_data.new(user_id=user_id)}]
        schema = [1]
        return self.markup(actions, schema)


class AdminDeleteChannelKb(InlineMarkupConstructor):
    callback_data = CallbackData("delete_channel", "channel_id")

    def get(self, channel_id: str, is_bot=False):
        title = "бота" if is_bot else "канал"
        actions = [
            {'text': f"Удалить {title}", 'cb': self.callback_data.new(channel_id)},
            {'text': "Вернуться", 'cb': AdminPanelKb.callback_data_channels.new()},
        ]
        schema = [1, 1]
        return self.markup(actions, schema)


class AdminSelectGroupToSub(InlineMarkupConstructor):
    callback_data = CallbackData("select_add_group", "chat_id")
    info = CallbackData("info_group", "chat_id")
    page = CallbackData("page_group", "page")
    page_not_changed = 'page_not_changed'

    def get(self, groups, page: int):
        schema = []
        actions = []
        for group in groups[(page - 1) * 8: page * 8]:
            actions.append({'text': group.ChatTitle[:25], 'cb': self.callback_data.new(group.Id)})
            actions.append({'text': 'Инфо', 'cb': self.info.new(group.Id)})
            schema += [2]

        actions.append({'text': '⬅️', 'cb': self.page.new(page - 1)})
        actions.append({'text': f'{page}/{len(groups) // 8 + 1}', 'cb': self.page_not_changed})
        actions.append({'text': '➡️', 'cb': self.page.new(page + 1)})
        actions.append({'text': 'Отмена', 'cb': 'cancel'})
        schema += [3, 1]

        return self.markup(actions, schema)


class AdminInfoGroup(InlineMarkupConstructor):
    leave_group = CallbackData('leave_group', 'chat_id')

    def get(self, chat_id: int):
        schema = [1]
        actions = [{"text": 'Покинуть группу', 'cb': self.leave_group.new(chat_id)}]
        return self.markup(actions, schema)


class ReportUserKb(InlineMarkupConstructor):
    callback_data = CallbackData("report", "report_to_id")

    def get(self, report_to_id: int):
        actions = [
            {'text': "⛔️ Пожаловаться", 'cb': self.callback_data.new(report_to_id)},
        ]
        schema = [1]
        return self.markup(actions, schema)


class AdminLinksKb(InlineMarkupConstructor):
    callback_data = CallbackData("link", "link_id")
    callback_data_add = CallbackData("add_link")

    def get(self, links: List[dict]):
        actions = []
        for link in links:
            actions.append({'text': f"{link[0].LinkTitle}", 'cb': self.callback_data.new(link[0].Id)})
        schema = int(len(links) / 3) * [3]
        if len(links) % 3 != 0:
            schema += [len(links) % 3]
        actions.append({'text': "Добавить ссылку", 'cb': self.callback_data_add.new()})
        schema += [1]
        return self.markup(actions, schema)


class AdminLinkKb(InlineMarkupConstructor):
    callback_data_delete = CallbackData("delete_link", "link_id")
    callback_data_price = CallbackData("set_price", "link_id")

    def get(self, link_id: str):
        actions = [
            {'text': "Удалить ссылку", 'cb': self.callback_data_delete.new(link_id)},
            {'text': "Установить цену", 'cb': self.callback_data_price.new(link_id)},
            {'text': "Вернуться", 'cb': AdminPanelKb.callback_data_links.new()},
        ]
        schema = [1, 1, 1]
        return self.markup(actions, schema)


class AdminDeleteLinkAcceptKb(InlineMarkupConstructor):
    callback_data_delete = CallbackData("delete_link_accept", "link_id", "accept")

    def get(self, link_id: str):
        actions = [
            {'text': "Да, удалить", 'cb': self.callback_data_delete.new(link_id, "1")},
            {'text': "Отмена", 'callback_data': "cancel"},
        ]
        schema = [1, 1]
        return self.markup(actions, schema)


class SetGenderKb(InlineMarkupConstructor):
    gender_data = CallbackData("set_gender", "gender")

    def get(self):
        schema = [1, 1]
        actions = [
            {'text': 'Я парень', 'cd': self.gender_data.new(1)},
            {'text': 'Я девушка‍️', 'cd': self.gender_data.new(2)},
        ]
        return self.markup(actions, schema)


class VipSearchKb(InlineMarkupConstructor):
    callback_data = CallbackData("search_type", "type")

    def get(self):
        schema = [1, 1]
        actions = [
            {'text': '🔍 Поиск по возрасту', 'cd': self.callback_data.new(1)},
            {'text': ' 👫 Поиск по полу', 'cd': self.callback_data.new(2)},
        ]
        return self.markup(actions, schema)


class SearchGenderKb(InlineMarkupConstructor):
    gender_data = CallbackData("search_gender", "gender")

    def get(self):
        schema = [1, 1]
        actions = [
            {'text': '💁‍♂️ Парня', 'cd': self.gender_data.new(1)},
            {'text': '💁‍♀️ Девушку', 'cd': self.gender_data.new(2)},
        ]
        return self.markup(actions, schema)


class SearchAgeKb(InlineMarkupConstructor):
    age_data = CallbackData("search_age", "age")

    def get(self):
        schema = [1, 1]
        actions = [
            {'text': 'Меньше 18', 'cd': self.age_data.new(1)},
            {'text': '18 и больше', 'cd': self.age_data.new(2)},
        ]
        return self.markup(actions, schema)


class AnswerKb(InlineMarkupConstructor):
    callback_data = CallbackData("start")

    def get(self, text="Ответить"):
        schema = [1]
        actions = [
            {'text': text, 'cd': self.callback_data.new()},
        ]
        return self.markup(actions, schema)


class PricesVip(InlineMarkupConstructor):
    callback_data = CallbackData("buy_vip", "type")

    def get(self):
        schema = [1, 1, 1, 1]
        actions = [
            {'text': '1 день - 69 рублей', 'cd': self.callback_data.new(1)},
            {'text': '3 дня - 99 рублей', 'cd': self.callback_data.new(2)},
            {'text': 'неделя - 149 рублей', 'cd': self.callback_data.new(3)},
            {'text': 'навсегда - 499 рублей', 'cd': self.callback_data.new(4)},
        ]
        return self.markup(actions, schema)


class BuyFindChat(InlineMarkupConstructor):
    callback_data = CallbackData("ff_check", "payment_id")

    def get(self, pay_url, pay_id):
        schema = [1, 1]
        actions = [
            {'text': '💵 Перейти к оплате', 'url': pay_url},
            {'text': '✅ Я оплатил', 'cd': self.callback_data.new(pay_id)},
        ]
        return self.markup(actions, schema)


class BuyVip(InlineMarkupConstructor):
    callback_data = CallbackData("payment_check", "payment_id")

    def get(self, pay_url, pay_id):
        schema = [1, 1]
        actions = [
            {'text': '💵 Перейти к оплате', 'url': pay_url},
            {'text': '✅ Я оплатил', 'cd': self.callback_data.new(pay_id)},
        ]
        return self.markup(actions, schema)


class RequestsManageKb(InlineMarkupConstructor):
    callback_data_add = CallbackData("add_rc")
    callback_data_stats = CallbackData("stats_rc", "channel_id", 'id')

    def get(self, data: List[dict]):
        actions = []
        for channel in data:
            actions.append({'text': f"{channel[0].ChannelTitle}",
                            'cb': self.callback_data_stats.new(channel[0].ChannelId, channel[0].Id)})
        schema = int(len(data) / 3) * [3]
        if len(data) % 3 != 0:
            schema += [len(data) % 3]
        actions.append({'text': "Добавить канал", 'cb': self.callback_data_add.new()})
        schema += [1]
        return self.markup(actions, schema)


class RequestManageKb(InlineMarkupConstructor):
    callback_data_delete = CallbackData("delete_rc", "channel_id", "agreed")

    def get(self, channel_id: int, agreed: int):
        actions = [
            {'text': "Удалить канал", 'cb': self.callback_data_delete.new(channel_id, agreed)}
        ]

        schema = [1]
        if agreed:
            schema += [1]
            actions.append({'text': "Отмена", 'cb': 'cancel'})

        return self.markup(actions, schema)


class ShowsManageKb(InlineMarkupConstructor):
    callback_data_add = CallbackData("add_show")
    callback_data_stats = CallbackData("stats_show", "show_id")

    def get(self, data: List[dict]):
        actions = []
        for show in data:
            actions.append({'text': f"ID: {show[0].Id}", 'cb': self.callback_data_stats.new(show[0].Id)})
        schema = int(len(data) / 3) * [3]
        if len(data) % 3 != 0:
            schema += [len(data) % 3]
        actions.append({'text': "Добавить показ", 'cb': self.callback_data_add.new()})
        schema += [1]
        return self.markup(actions, schema)


class ShowManageKb(InlineMarkupConstructor):
    callback_data_delete = CallbackData("delete_show", "show_id", "agreed")

    def get(self, show_id: int, agreed: int):
        actions = [
            {'text': "Удалить показ", 'cb': self.callback_data_delete.new(show_id, agreed)}
        ]

        schema = [1]
        if agreed:
            schema += [1]
            actions.append({'text': "Отмена", 'cb': 'cancel'})

        return self.markup(actions, schema)


class ComplaintKb(InlineMarkupConstructor):

    def get(self, companion_id: int):
        schema = [2]
        actions = [
            {'text': '⚠️Да', 'cd': f'report_yes_{companion_id}'},
            {'text': 'Нет', 'cd': f'report_no_{companion_id}'}
        ]
        return self.markup(actions, schema)
