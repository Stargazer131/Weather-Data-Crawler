import threading
import time

from flask import Flask, render_template, redirect, url_for
import requests
from datetime import datetime
from typing import Optional
from utility import inverse_transform_condition

from xgboost import XGBClassifier, XGBRegressor
import numpy as np

app = Flask(__name__)
latest_data = (datetime.now(), 75, 70, 1000, 5)


def fetch_data():
    global latest_data
    while True:
        timestamp, temp, humid = get_sensor_data()
        if datetime.now().hour == timestamp.hour:
            press, wind = get_api_data()
        else:
            press, wind = get_api_data(timestamp)
        latest_data = (timestamp, temp, humid, press, wind)
        print('get latest data')
        time.sleep(30)


@app.route('/')
def root():
    return redirect(url_for('home_page'))


@app.route('/home', methods=['GET'])
def home_page():
    timestamp, temp, humid, press, wind = latest_data

    inputs = [temp, humid, press, wind, timestamp.month, timestamp.day, timestamp.hour]
    inputs = np.array(inputs).reshape(1, -1)
    model = all_models['classification']
    condition = inverse_transform_condition(model.predict(inputs)[0])
    rain_prob = model.predict_proba(inputs)[0][3] * 100
    time = day_or_night(timestamp.hour, 0)

    data = {
        "temperature": (temp-32) * 5/9,
        "humidity": humid,
        "pressure": press,
        "wind_speed": wind * 0.44704,
        "condition": condition,
        "weather_image_url": f"images/{condition.lower()}_{time}.png",
        "rain_prob": rain_prob
    }

    return render_template('home.html', data=data)


@app.route('/hours', methods=['GET'])
def hours_page():
    timestamp, temp, humid, press, wind = latest_data

    inputs = [temp, humid, press, wind,
              timestamp.month, timestamp.day, timestamp.hour]
    inputs = np.array(inputs).reshape(1, -1)
    hours = [1, 3, 6, 9, 12]
    hours_data = []
    classifier = all_models['classification']
    for hour in hours:
        data = {"hour": hour}

        # temperature
        model = all_models['regression']['hours'][f'{hour}_temperature']
        predict_temperature = model.predict(inputs)[0]
        data['temperature'] = (predict_temperature-32) * 5/9

        # humidity
        model = all_models['regression']['hours'][f'{hour}_humidity']
        predict_humidity = model.predict(inputs)[0]
        data['humidity'] = predict_humidity

        # pressure
        model = all_models['regression']['hours'][f'{hour}_pressure']
        predict_pressure = model.predict(inputs)[0]
        data['pressure'] = predict_pressure

        # wind_speed
        model = all_models['regression']['hours'][f'{hour}_wind_speed']
        predict_wind_speed = model.predict(inputs)[0]
        data['wind_speed'] = predict_wind_speed * 0.44704

        # condition and rain probability
        temp_inputs = [predict_temperature, predict_humidity, predict_pressure, predict_wind_speed,
                       timestamp.month, timestamp.day, timestamp.hour+hour]
        temp_inputs = np.array(temp_inputs).reshape(1, -1)

        condition = inverse_transform_condition(classifier.predict(temp_inputs)[0])
        rain_prob = classifier.predict_proba(temp_inputs)[0][3] * 100

        data['condition'] = condition
        data['rain_prob'] = rain_prob
        time = day_or_night(timestamp.hour, hour)
        data["weather_image_url"] = f"images/{condition.lower()}_{time}.png"
        hours_data.append(data)

    return render_template('hours.html', hours_data=hours_data)


@app.route('/days', methods=['GET'])
def days_page():
    timestamp, temp, humid, press, wind = latest_data

    inputs = [temp, humid, press, wind,
              timestamp.month, timestamp.day, timestamp.hour]
    inputs = np.array(inputs).reshape(1, -1)
    days = list(range(1, 8))
    days_data = []
    classifier = all_models['classification']
    for day in days:
        data = {"day": day}

        # temperature
        model = all_models['regression']['days'][f'{day}_temperature']
        predict_temperature = model.predict(inputs)[0]
        data['temperature'] = (predict_temperature-32) * 5/9

        # humidity
        model = all_models['regression']['days'][f'{day}_humidity']
        predict_humidity = model.predict(inputs)[0]
        data['humidity'] = predict_humidity

        # pressure
        model = all_models['regression']['days'][f'{day}_pressure']
        predict_pressure = model.predict(inputs)[0]
        data['pressure'] = predict_pressure

        # wind_speed
        model = all_models['regression']['days'][f'{day}_wind_speed']
        predict_wind_speed = model.predict(inputs)[0]
        data['wind_speed'] = predict_wind_speed * 0.44704

        # condition and rain probability
        temp_inputs = [predict_temperature, predict_humidity, predict_pressure, predict_wind_speed,
                       timestamp.month, timestamp.day+day, timestamp.hour]
        temp_inputs = np.array(temp_inputs).reshape(1, -1)

        condition = inverse_transform_condition(classifier.predict(temp_inputs)[0])
        rain_prob = classifier.predict_proba(temp_inputs)[0][3] * 100

        data['condition'] = condition
        data['rain_prob'] = rain_prob
        time = day_or_night(timestamp.hour, 0)
        data["weather_image_url"] = f"images/{condition.lower()}_{time}.png"
        days_data.append(data)

    return render_template('days.html', days_data=days_data)


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
        return datetime.now(), 75, 70


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


def day_or_night(time: int, add: int):
    time += add
    if 5 <= time <= 18:
        return 'day'
    else:
        return 'night'


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

    # classification
    model = XGBClassifier()
    model.load_model("model\\classification\\xgboost_classification_model.json")
    models['classification'] = model
    print('finish load classification model')

    # hours regression
    hours = [1, 3, 6, 9, 12]
    features = ['temperature', 'humidity', 'pressure', 'wind_speed']
    for hour in hours:
        for feature in features:
            file_path = f"model\\regression\\hours\\{hour}_{feature}_xgboost_regression.json"
            model = XGBRegressor()
            model.load_model(file_path)
            models['regression']['hours'][f'{hour}_{feature}'] = model
            print(f'finish load regression model ({hour}H-{feature})')

    # days regression
    days = list(range(1, 8))
    features = ['temperature', 'humidity', 'pressure', 'wind_speed']
    for day in days:
        for feature in features:
            file_path = f"model\\regression\\days\\{day}_{feature}_xgboost_regression.json"
            model = XGBRegressor()
            model.load_model(file_path)
            models['regression']['days'][f'{day}_{feature}'] = model
            print(f'finish load regression model ({day}D-{feature})')

    end_time = datetime.now()
    print(end_time - start_time)
    return models


all_models = load_all_models()
thread = threading.Thread(target=fetch_data, daemon=True)
thread.start()
# -----------------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run()
