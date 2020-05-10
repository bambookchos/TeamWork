import pickle
from abc import ABC, abstractmethod
from pg_api import PgAPI
from aiogram import types


class BotAPI(ABC):
    """Базовый класс для API разных ботов.
    Дочерние классы обрабатывают особенности оболочек
    и передают базе данных необходимые запросы.
    """

    @abstractmethod
    def set_city(self, data):
        pass

    @abstractmethod
    def set_preferences(self, data):
        pass

    @abstractmethod
    def get_event(self, data):
        pass

class TelegramAPI(BotAPI):
    def __init__(self, config):
        self.db = PgAPI(**config)

    def set_db(self, config):
        """config = {database: str, user: str[, password: str]}"""
        self.db = PgAPI(**config)

    @staticmethod
    def convert_data(data):
        """Метод для преобразования сообщения из Telegram
        в данные, сериализованые для бота.
        """
        return data

    def set_city(self, data):
        converted_data = self.convert_data(data)
        self.db.set_city(converted_data)

    def set_preferences(self, data):
        converted_data = self.convert_data(data)
        self.db.set_preferences(converted_data)

    def get_event(self, data):
        converted_data = self.convert_data(data)
        self.db.get_event(converted_data)

    def start_command(self, message):
        text = f'Привет, {message.from_user.username} я бот, который ' \
               'подскажет, куда тебе сходить ' \
               'в свободное время, для начала расскажи о себе ' \
               '/registration ^^ '
        self.db.add_user(message.from_user.id)
        return text

    @staticmethod
    def registration_command(data):
        text = 'Выбери город'
        keyboard_markup = types.InlineKeyboardMarkup(row_width=2)
        text_and_data = (
            ('Moscow', 'msk'),
            ('Saint Petersburg', 'spb'),
        )
        row_btn = (types.InlineKeyboardButton(text, callback_data=data)
                   for text, data in text_and_data)
        keyboard_markup.row(*row_btn)

        return text, keyboard_markup

    def set_subscriber(self, data):
        # TODO нужна функци добавления инфы о подписке в бд
        return 0

    def process_callback(self, query):
        answer_data = query.data
        bot_callback = {
            'find': 'find_command',
            'clean': 'clean_command'
        }
        func = bot_callback.get(answer_data,
                                lambda: "Я пока не знаю такой команды")
        return func(self, answer_data)

    def process_city(self, query):
        self.db.set_user_city(query.from_user.id, query.data)
        text = "давай посмотрим, что ты любишь /categories"
        return text

    @staticmethod
    def categories_command(self, query):
        # with open('categories', 'rb') as f:
        #    categories_ev = pickle.load(f)
        user_tags = self.db.get_user_categories(query.from_user.id)
        print(user_tags)
        if(user_tags == [[None]]):
            text = 'У тебя пока ничего не выбрано, отметь что-нибудь'
        else:
            cat = ', '.join(self.db.get_category_name(user_tag)
                            for user_tag in user_tags)
            text = f'Сейчас у тебя выбраны:{cat}'
        keyboard_markup = types.InlineKeyboardMarkup(row_width=6)
        # categories = (category["slug"], category["name"] for category
        # in categories_ev if category["name"] not in)
        categories = (('Кино', 'cinema'),
                      ('Стенд-ап', 'stand-up'),
                      ('Концерт', 'concert'),
                      ('Фестиваль', 'festival'),
                      ('Завершить выбор и начать поиск', 'find'),
                      ('Сбросить все выбранные', 'clean'))

        row_btn = (types.InlineKeyboardButton(text, callback_data=data)
                   for text, data in categories)
        keyboard_markup.row(*row_btn)

        return text, keyboard_markup

    def process_categories(self, query):
        self.db.set_user_category(query.from_user.id, query.data)

    @staticmethod
    def help_command():
        text = 'Для начала работы /start\nДля выбора города' \
               ' /registration\nДля настройки категорий ' \
               '/categories\nДля поиска /find\nЧтобы подписаться' \
               ' на рассылку /subscribe'
        return text

    def find_command(self, data):
        text = "Смотри, куда можно сходить\n"
        events = self.get_event(data)
        return text + "\n".join(events)

    def clean_command(self, data):
        # почистить выбранные категории пользователя в бд
        self.categories_command(data)

    def subscribe_command(self, data):
        # изменить полу подписки в базе
        self.db.set_user_subscribed(data.from_user.id)
        text = "Поздравялем, теперь тебе будет приходить подборка " \
               "меропирятий и ты ничего не пропустишь "
        return text

    def unsubscribe_command(self, data):
        # изменить полу подписки в базе
        self.db.clear_user_subscribed(data.from_user.id)
        text = "Ты отписался, но все равно можешь посмотреть, куда " \
               "сходить, просто нажми /find или /help - чтобы " \
               "посмотреть все команды"
        return text
