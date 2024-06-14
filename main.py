from config import API_TOKEN, WEATHER_API_KEY, DB_NAME
from database_manager import DatabaseManager
from weather_api import WeatherAPI
from weather_bot import WeatherBot

def main():
    db_manager = DatabaseManager(DB_NAME)
    weather_api = WeatherAPI(WEATHER_API_KEY)
    weather_bot = WeatherBot(API_TOKEN, db_manager, weather_api)

    # Инициализация базы данных и запуск ежедневного оповещения
    subscriptions = db_manager.get_all_subscriptions()
    for user_id, location, send_time in subscriptions:
        if send_time:
            weather_bot.add_job_to_scheduler(user_id, location, send_time)

    weather_bot.run()

if __name__ == '__main__':
    main()
