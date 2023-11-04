from datetime import datetime
from typing import Optional
import requests


def inverse_transform_condition(code: int):
    weather_dict = {
        0: "Cloudy",
        1: "Fair",
        2: "Fog",
        3: "Rain",
        4: "Thunderstorm"
    }
    return weather_dict[code]


def day_or_night(time_of_day: int, add: int):
    time_of_day = (time_of_day + add) % 24
    if 5 <= time_of_day <= 18:
        return 'day'
    else:
        return 'night'


def get_sensor_data():
    """
    Get latest timestamp, temperature and humidity from thingspeak (simulated data)
    """
    channel_id = 2323800
    base_url = f'https://api.thingspeak.com/channels/{channel_id}/feeds.json'
    params = {
        'api_key': 'XS2X5BHENB7J2WJD',
        'results': 1,
    }
    try:
        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            data = response.json()
            timestamp = data['feeds'][0]['created_at']
            timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
            temperature = float(data['feeds'][0]['field1']) * 9 / 5 + 32
            humidity = float(data['feeds'][0]['field2'])
            return timestamp, temperature, humidity
        else:
            print(f'Failed. Status code: {response.status_code}')
            return datetime.now(), 75, 70
    except Exception as er:
        print(er)
        return datetime.now(), 75, 70


def get_api_data(timestamp: Optional[datetime] = None):
    """
    Get pressure and wind from openweather, currently or in a specific timestamp (Ha Noi)
    """
    try:
        if timestamp is None:
            base_url = 'https://api.openweathermap.org/data/2.5/weather'
            params = {
                'q': 'hanoi',
                'appid': '922fa7db5e80194935a053d2bbab7354',
                'units': 'imperial'
            }
            response = requests.get(base_url, params=params)

            if response.status_code == 200:
                data = response.json()
                pressure = data['main']['pressure']
                wind_speed = data['wind']['speed']
                return pressure, wind_speed
            else:
                print(f'Failed. Status code: {response.status_code}')
                return 1000, 5
        else:
            base_url = 'https://api.openweathermap.org/data/3.0/onecall/timemachine'
            params = {
                'lat': 21.0245,
                'lon': 105.8412,
                'dt': int(timestamp.timestamp()),
                'appid': '922fa7db5e80194935a053d2bbab7354',
                'units': 'imperial'
            }
            response = requests.get(base_url, params=params)

            if response.status_code == 200:
                data = response.json()
                pressure = data['data'][0]['pressure']
                wind_speed = data['data'][0]['wind_speed']
                return pressure, wind_speed
            else:
                print(f'Failed. Status code: {response.status_code}')
                return 1000, 5
    except Exception as er:
        print(er)
        return 1000, 5
