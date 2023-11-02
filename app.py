from flask import Flask, render_template
import requests
from datetime import datetime
from typing import Optional
from utility import inverse_transform_condition

from xgboost import XGBClassifier, XGBRegressor
import numpy as np

app = Flask(__name__)


@app.route('/', methods=['GET'])
def handle_home_request():
    timestamp, temp, humid = get_sensor_data()
    press, wind = get_api_data()

    inputs = [temp, humid, press, wind, timestamp.month, timestamp.day, timestamp.hour]
    inputs = np.array(inputs).reshape(1, -1)
    model = all_models['classification']
    condition = inverse_transform_condition(model.predict(inputs)[0])

    data = {
        "temperature": (temp-32) * 5/9,
        "humidity": humid,
        "pressure": press,
        "wind_speed": wind * 0.44704,
        "condition": condition
    }

    return render_template('home.html', data=data)


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
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        timestamp = data['feeds'][0]['created_at']
        timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
        temperature = float(data['feeds'][0]['field1']) * 9/5 + 32
        humidity = float(data['feeds'][0]['field2'])
        return timestamp, temperature, humidity
    else:
        print(f'Failed. Status code: {response.status_code}')


def get_api_data(timestamp: Optional[datetime] = None):
    """
    Get pressure and wind from openweather, currently or in a specific timestamp (Ha Noi)
    """
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


# -----------------------------------------------------------------------------------------
def load_all_models():
    start_time = datetime.now()
    models = {
        'classification': None,
        'regression': {
            'hours': {},
            'days': {}
        }
    }

    model = XGBClassifier()
    model.load_model("model\\classification\\xgboost_classification_model.json")
    models['classification'] = model
    print('finish load classification model')

    # hours = [1, 3, 6, 12]
    # features = ['temp', 'humid', 'press', 'wind']
    # names = ['temperature', 'humidity', 'pressure', 'wind_speed']
    # for hour in hours:
    #     for index, feature in enumerate(features):
    #         file_path = f"model\\regression\\hours\\{hour}h_{feature}_xgboost_regression.json"
    #         model = XGBRegressor()
    #         model.load_model(file_path)
    #         models['regression']['hours'][f'{hour}_{names[index]}'] = model
    #         print(f'finish load regression model ({hour}-{feature})')

    end_time = datetime.now()
    print(end_time - start_time)
    return models


all_models = load_all_models()
# -----------------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run()
