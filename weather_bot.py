import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

class WeatherBot:
    def __init__(self, api_token, db_manager, weather_api):
        self.bot = telebot.TeleBot(api_token)
        self.db_manager = db_manager
        self.weather_api = weather_api
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.user_states = {}
        self.user_times = {}

        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.bot.message_handler(commands=['start'])(self.send_welcome)
        self.bot.message_handler(func=lambda message: message.text == 'Меню')(self.show_menu)
        self.bot.message_handler(content_types=['location'])(self.handle_location)
        self.bot.message_handler(func=lambda message: message.text == 'Ввести населенный пункт')(self.ask_for_location)
        self.bot.message_handler(func=lambda message: message.chat.id in self.user_states and self.user_states[message.chat.id] == 'awaiting_location')(self.handle_text_location)
        self.bot.message_handler(func=lambda message: message.text == 'Текущая погода')(self.current_weather)
        self.bot.message_handler(func=lambda message: message.text == 'Прогноз на три дня')(self.weather_forecast)
        self.bot.message_handler(func=lambda message: message.text == 'Подписаться на ежедневный прогноз')(self.subscribe)
        self.bot.message_handler(func=lambda message: message.chat.id in self.user_states and self.user_states[message.chat.id] == 'awaiting_time')(self.handle_time)

    def run(self):
        self.bot.polling(none_stop=True)

    def send_welcome(self, message):
        markup = self.create_main_menu()
        self.bot.send_message(message.chat.id, "Добро пожаловать! Используйте 'Меню' для выбора опций.", reply_markup=markup)

    def create_main_menu(self):
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        markup.add(KeyboardButton('Меню'))
        return markup

    def show_menu(self, message):
        markup = self.create_detailed_menu()
        self.bot.send_message(message.chat.id, "Выберите опцию из меню:", reply_markup=markup)

    def create_detailed_menu(self):
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        #markup.add(KeyboardButton('Отправить локацию', request_location=True))
        markup.add(KeyboardButton('Ввести населенный пункт'))
        markup.add(KeyboardButton('Текущая погода'))
        markup.add(KeyboardButton('Прогноз на три дня'))
        markup.add(KeyboardButton('Подписаться на ежедневный прогноз'))

        return markup

    def handle_location(self, message):
        if message.location is not None:
            user_id = message.chat.id
            latitude = message.location.latitude
            longitude = message.location.longitude
            location = f"{latitude},{longitude}"
            self.db_manager.save_location(user_id, location)
            self.bot.send_message(user_id, "Локация сохранена. Теперь вы можете получать прогноз погоды.")
            self.logger.info(f"User {user_id} location saved: {location}")

    def ask_for_location(self, message):
        user_id = message.chat.id
        self.user_states[user_id] = 'awaiting_location'
        self.bot.send_message(message.chat.id, "Введите название вашего населенного пункта:")

    def handle_text_location(self, message):
        user_id = message.chat.id
        location = message.text.strip()
        if location == 'Текущая погода' or location == 'Прогноз на три дня' or location == 'Подписаться на ежедневный прогноз'  :
            self.bot.send_message(user_id, "Ошибка! Вы не ввели населенный пункт, а выбрали пункт меню.\n")
            return
        self.db_manager.save_location(user_id, location)
        self.user_states.pop(user_id, None)
        self.bot.send_message(user_id, "Населенный пункт сохранен. Теперь вы можете получать прогноз погоды.")
        self.logger.info(f"User {user_id} location saved: {location}")

    def current_weather(self, message):
        user_id = message.chat.id
        subscription = self.db_manager.get_subscription(user_id)
        if subscription:
            location = subscription[0]
            weather = self.weather_api.get_weather(location)
            self.bot.send_photo(message.chat.id, weather['icon'], caption=f"Текущая погода в {weather['location']}: {weather['condition']}, температура {weather['temperature']}°C")
            self.logger.info(f"Sent current weather to user {user_id} for location {location}")
        else:
            self.bot.send_message(message.chat.id, "Пожалуйста, отправьте свою локацию или введите название населенного пункта для получения прогноза погоды.")

    def weather_forecast(self, message):
        user_id = message.chat.id
        subscription = self.db_manager.get_subscription(user_id)
        if subscription:
            location = subscription[0]
            forecast = self.weather_api.get_forecast(location)
            forecast_message = "Прогноз погоды на три дня:\n"
            for day in forecast:
                forecast_message += f"{day['date']}: {day['condition']}, температура {day['temperature']}°C\n"
                self.bot.send_photo(message.chat.id, photo=day['icon'], caption=forecast_message)
                forecast_message = ""  # Сбрасываем сообщение для следующего дня
                self.logger.info(f"Sent weather forecast to user {user_id} for location {location}")
        else:
            self.bot.send_message(message.chat.id, "Пожалуйста, отправьте свою локацию или введите название населенного пункта для получения прогноза погоды.")

    def subscribe(self, message):
        user_id = message.chat.id
        subscription = self.db_manager.get_subscription(user_id)
        if subscription and subscription[0]:
            self.user_states[user_id] = 'awaiting_time'
            self.bot.send_message(message.chat.id, "Введите время для получения ежедневного прогноза (например, 07:00):")
        else:
            self.bot.send_message(message.chat.id, "Сначала отправьте свою локацию или введите название населенного пункта.")

    def handle_time(self, message):
        user_id = message.chat.id
        send_time = message.text.strip()
        try:
            hour, minute = map(int, send_time.split(':'))
            if not (0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError
            self.db_manager.update_send_time(user_id, send_time)
            self.user_states.pop(user_id, None)
            self.bot.send_message(user_id, f"Вы подписались на ежедневный прогноз погоды в {send_time}.")
            self.logger.info(f"User {user_id} subscribed to daily forecast at {send_time}")

            # Добавить задание в планировщик немедленно
            location = self.db_manager.get_subscription(user_id)[0]
            self.add_job_to_scheduler(user_id, location, send_time)
        except ValueError:
            self.bot.send_message(user_id, "Некорректный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ.")

    def add_job_to_scheduler(self, user_id, location, send_time):
        try:
            hour, minute = map(int, send_time.split(':'))
            self.scheduler.add_job(self.send_weather_message, CronTrigger(hour=hour, minute=minute), args=[user_id, location])
            self.logger.info(f"Added job to scheduler for user {user_id} at {send_time}")
        except Exception as e:
            self.logger.error(f"Failed to add job to scheduler for user {user_id} at {send_time}: {e}")

    def send_weather_message(self, user_id, location):
        weather = self.weather_api.get_weather(location)
        self.bot.send_photo(user_id, weather['icon'], caption=f"Текущая погода в {location}: {weather['condition']}, температура {weather['temperature']}°C")
        self.logger.info(f"Sent daily weather to user {user_id} for location {location}")
