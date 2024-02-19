from app.utils.markup_constructor import ReplyMarkupConstructor


class AdminMarkup(ReplyMarkupConstructor):
    stats_button = "Статистика"
    channels_button = "Каналы"
    mails_button = "Рассылка"
    links_buttons = "Ссылки"
    shows_button = "Показы"
    requests_button = "Заявки"
    users_button = "Скачать пользователей"
    reports_button = "Жалобы"
    edit_message_stealer = 'Изменить сообщение заявок'
    del_message_stealer = 'Убрать приветствие в заявках'
    give_vip = 'Подарить вип'

    def get(self):
        schema = [2, 2, 2, 1, 1, 1, 1, 1]
        actions = [
            {'text': self.stats_button},
            {'text': self.channels_button},
            {'text': self.mails_button},
            {'text': self.links_buttons},
            {'text': self.shows_button},
            {'text': self.requests_button},
            {'text': self.reports_button},
            {'text': self.users_button},
            {'text': self.edit_message_stealer},
            {'text': self.del_message_stealer},
            {'text': self.give_vip}

        ]
        return self.markup(actions, schema, True)


class MainMenuMarkup(ReplyMarkupConstructor):
    val_key = "💗 Валентинка"
    search_companion_button = "✈️ Начать диалог"
    search_companion_gender_button = "🏆 VIP поиск"
    vulgar_chat_button = "Пошлый чат 🔞"
    information_button = "🗃  Информация"

    def get(self):
        schema = [1, 1, 1, 1]
        actions = [
            {'text': self.val_key},
            {'text': self.search_companion_button},
            {'text': self.search_companion_gender_button},
            {'text': self.vulgar_chat_button},
            # {'text': self.information_button},
        ]
        return self.markup(actions, schema, True)


class CancelDialogMarkup(ReplyMarkupConstructor):
    button_text = '⛔️ Закончить диалог'
    button_find = '🔍 "Спалить" собеседника'

    def get(self, username=None):
        schema = [1,1]
        actions = [
            {'text': self.button_text},
            {'text': self.button_find},
        ]
        if username is not None:
            #schema += [1]
            #.append({'text': self.button_find})
            pass

        return self.markup(actions, schema, True)


class CancelMarkup(ReplyMarkupConstructor):
    button_text = '❌ Остановить поиск'

    def get(self):
        schema = [1]
        actions = [
            {'text': self.button_text},
        ]
        return self.markup(actions, schema, True)


class AdminReportsMarkup(ReplyMarkupConstructor):
    ban_report_button = "❌Забанить"
    skip_report_button = "✅Пропустить"
    cancel_report_button = "Пропустить"

    def get(self):
        schema = [2, 1]
        actions = [
            {'text': self.ban_report_button},
            {'text': self.skip_report_button},
            {'text': self.cancel_report_button},
        ]
        return self.markup(actions, schema, True)