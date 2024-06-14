import requests

class WeatherAPI:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_weather(self, location):
        url = f"http://api.weatherapi.com/v1/current.json?key={self.api_key}&q={location}&lang=ru"
        response = requests.get(url).json()
        weather = response['current']
        location = response['location']['name']
        return {
            'condition': weather['condition']['text'],
            'temperature': weather['temp_c'],
            'icon': 'https:' + weather['condition']['icon'],
            'location': location
        }

    def get_forecast(self, location):
        url = f"http://api.weatherapi.com/v1/forecast.json?key={self.api_key}&q={location}&days=3&lang=ru"
        response = requests.get(url).json()
        forecast_days = response['forecast']['forecastday']
        forecast = []
        for day in forecast_days:
            forecast.append({
                'date': day['date'],
                'condition': day['day']['condition']['text'],
                'temperature': day['day']['avgtemp_c'],
                'icon': 'https:' + day['day']['condition']['icon']
            })
        return forecast
