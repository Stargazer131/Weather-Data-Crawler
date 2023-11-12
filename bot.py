import threading
import time as tme
from datetime import datetime, timedelta, time

import numpy as np
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from xgboost import XGBClassifier, XGBRegressor

from utility import get_sensor_data, round_time, get_api_data, inverse_transform_condition, day_or_night

TOKEN = '6710672539:AAH5AVA2q6yRboBpDXn-_4GAHPTEvMb8LJQ'


latest_data = (datetime.now(), 75, 70, 1000, 5)


def fetch_data():
    global latest_data
    tme.sleep(2)
    while True:
        timestamp, temp, humid = get_sensor_data()
        timestamp += timedelta(hours=7)
        timestamp = round_time(timestamp)
        if datetime.now().hour == timestamp.hour:
            press, wind = get_api_data()
        else:
            press, wind = get_api_data(timestamp)
        latest_data = (timestamp, temp, humid, press, wind)
        print('get latest data')
        tme.sleep(30)


# for printing emoji

icon_bank = {
    "weather": {
        "night": "\U0001F311",
        "day": "\U00002600",
        "cloudy": "\U00002601",
        "rain": "\U0001F327",
        "thunderstorm": "\U000026C8",
        "fog": "\U0001F32B",
        "rainbow": "\U0001F308",
        "temperature": "\U0001F321",
        "wind_speed": "\U0001F32C",
        "humidity": "\U0001F4A7",
        "pressure": "\U0001F4A8",
        "rain_prob": "\U00002614"
    },

    "logo": {
        "day": "\U0001F307",
        "night": "\U0001F303",
        "information": "\U00002139",
        "city": "\U0001F3D9",
        "yes": "\U00002705",
        "no": "\U0000274E",
        "warning": "\U000026A0",
        "prohibit": "\U0001F6AB",
        "calendar": "\U0001F4C5",
        "bot": "\U0001F916",
        "question_mark": "\U00002753",
        "clock": "\U0001F552",
        "bell": "\U0001F514",
        "cancel_bell": "\U0001F515"
    }
}


# command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = (
        f"Hello, Thanks for choosing Weather Bot! {icon_bank['logo']['bot']}\n"
        f"Type /help for more information {icon_bank['logo']['question_mark']}"
    )

    await context.bot.send_message(chat_id=update.message.chat_id, text=answer)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = (
        f"The following command are available (in Hanoi):\n"
        f"/current Current weather {icon_bank['weather']['rainbow']}\n"
        f"/hour Weather in next 12 hours {icon_bank['logo']['clock']}\n"
        f"/day Weather in next 7 days {icon_bank['logo']['calendar']}\n"
        f"/daily Receive daily weather at 07:AM {icon_bank['logo']['bell']}\n"        
        f"/alert Receive alert for uncomfortable/hazardous weather {icon_bank['logo']['warning']}\n"
        f"/stop_daily Stop receiving daily update {icon_bank['logo']['cancel_bell']}\n"
        f"/stop_alert Stop receiving alert {icon_bank['logo']['no']}\n"
    )

    await context.bot.send_message(chat_id=update.message.chat_id, text=answer)


async def current_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_current_weather(latest_data)

    answer = (
        f"The weather is: {data['condition']} {icon_bank['weather'][data['icon']]}\n"
        f"Temperature: {data['temperature']:.1f}°C {icon_bank['weather']['temperature']}\n"
        f"Wind speed: {data['wind_speed']:.1f} mps {icon_bank['weather']['wind_speed']}\n"
        f"Humidity: {data['humidity']:.1f}% {icon_bank['weather']['humidity']}\n"
        f"Pressure: {data['pressure']:.1f} hPa {icon_bank['weather']['pressure']}\n"
        f"Rain Probability: {data['rain_prob']:.2f}% {icon_bank['weather']['rain_prob']}\n"
    )

    await context.bot.send_message(chat_id=update.message.chat_id, text=answer)


def get_current_weather(input_data: tuple):
    timestamp, temp, humid, press, wind = input_data
    inputs = [temp, humid, press, wind, timestamp.month, timestamp.day, timestamp.hour]
    inputs = np.array(inputs).reshape(1, -1)
    model = all_models['classification']
    condition = inverse_transform_condition(model.predict(inputs)[0]).lower()
    rain_prob = model.predict_proba(inputs)[0][3] * 100
    time_of_day = day_or_night(timestamp.hour, 0)
    icon = condition
    if condition == 'fair':
        icon = time_of_day

    data = {
        "temperature": (temp-32) * 5/9,
        "humidity": humid,
        "pressure": press,
        "wind_speed": wind * 0.44704,
        "condition": condition,
        "icon": icon,
        "rain_prob": rain_prob
    }

    return data


async def hour_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hours_data = get_hour_prediction(latest_data)
    answers = []
    for data in hours_data:
        answer = (
            f"Weather in next {data['hour']} hour ({data['time'].strftime('%H:%M')})\n"
            f"The weather is: {data['condition']} {icon_bank['weather'][data['icon']]}\n"
            f"Temperature: {data['temperature']:.1f}°C {icon_bank['weather']['temperature']}\n"
            f"Wind speed: {data['wind_speed']:.1f} mps {icon_bank['weather']['wind_speed']}\n"
            f"Humidity: {data['humidity']:.1f}% {icon_bank['weather']['humidity']}\n"
            f"Pressure: {data['pressure']:.1f} hPa {icon_bank['weather']['pressure']}\n"
            f"Rain Probability: {data['rain_prob']:.2f}% {icon_bank['weather']['rain_prob']}\n"
        )
        answers.append(answer)

    for answer in answers:
        await context.bot.send_message(chat_id=update.message.chat_id, text=answer)


def get_hour_prediction(input_data: tuple):
    timestamp, temp, humid, press, wind = input_data
    inputs = [temp, humid, press, wind,
              timestamp.month, timestamp.day, timestamp.hour]
    inputs = np.array(inputs).reshape(1, -1)
    hours = [1, 3, 6, 9, 12]
    hours_data = []

    classifier = all_models['classification']
    for hour in hours:
        data = {"hour": hour, "time": timestamp + timedelta(hours=hour)}

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

        condition = inverse_transform_condition(classifier.predict(temp_inputs)[0]).lower()
        rain_prob = classifier.predict_proba(temp_inputs)[0][3] * 100
        data['rain_prob'] = rain_prob
        time_of_day = day_or_night(timestamp.hour, hour)
        data['condition'] = condition
        if condition == 'fair':
            data['icon'] = time_of_day
        else:
            data['icon'] = condition

        hours_data.append(data)

    return hours_data


async def day_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    days_data = get_day_prediction(latest_data)
    answers = []
    for data in days_data:
        answer = (
            f"Weather in next {data['day']} day ({data['time'].strftime('%d/%m/%Y')})\n"
            f"The weather is: {data['condition']} {icon_bank['weather'][data['icon']]}\n"
            f"Temperature: {data['temperature']:.1f}°C {icon_bank['weather']['temperature']}\n"
            f"Wind speed: {data['wind_speed']:.1f} mps {icon_bank['weather']['wind_speed']}\n"
            f"Humidity: {data['humidity']:.1f}% {icon_bank['weather']['humidity']}\n"
            f"Pressure: {data['pressure']:.1f} hPa {icon_bank['weather']['pressure']}\n"
            f"Rain Probability: {data['rain_prob']:.2f}% {icon_bank['weather']['rain_prob']}\n"
        )
        answers.append(answer)

    for answer in answers:
        await context.bot.send_message(chat_id=update.message.chat_id, text=answer)


def get_day_prediction(input_data: tuple):
    timestamp, temp, humid, press, wind = input_data

    inputs = [temp, humid, press, wind,
              timestamp.month, timestamp.day, timestamp.hour]
    inputs = np.array(inputs).reshape(1, -1)
    days = list(range(1, 8))
    days_data = []
    classifier = all_models['classification']
    for day in days:
        data = {"day": day, "time": timestamp + timedelta(days=day)}

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

        condition = inverse_transform_condition(classifier.predict(temp_inputs)[0]).lower()
        rain_prob = classifier.predict_proba(temp_inputs)[0][3] * 100

        data['condition'] = condition
        data['rain_prob'] = rain_prob
        time_of_day = day_or_night(timestamp.hour, 0)
        if condition == 'fair':
            data['icon'] = time_of_day
        else:
            data['icon'] = condition
        days_data.append(data)

    return days_data


async def daily_handler(context: ContextTypes.DEFAULT_TYPE):
    data = get_current_weather(latest_data)

    answer = (
        f"Today the weather is: {data['condition']} {icon_bank['weather'][data['icon']]}\n"
        f"Temperature: {data['temperature']:.1f}°C {icon_bank['weather']['temperature']}\n"
        f"Wind speed: {data['wind_speed']:.1f} mps {icon_bank['weather']['wind_speed']}\n"
        f"Humidity: {data['humidity']:.1f}% {icon_bank['weather']['humidity']}\n"
        f"Pressure: {data['pressure']:.1f} hPa {icon_bank['weather']['pressure']}\n"
        f"Rain Probability: {data['rain_prob']:.2f}% {icon_bank['weather']['rain_prob']}\n"
        f"Good day to you!"
    )

    await context.bot.send_message(chat_id=context.job.chat_id, text=answer)


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    jobs = context.job_queue.get_jobs_by_name(f'daily_{chat_id}')
    if len(jobs) != 0:
        text = 'You already subscribed to daily update'
    else:
        now = datetime.now()
        target_time = datetime(now.year, now.month, now.day, 7, 0, 0)
        if now > target_time:
            target_time += timedelta(days=1)
        total_second_till_next_7am = (target_time - now).total_seconds()
        context.job_queue.run_repeating(daily_handler, interval=60*60*24, first=2,
                                        chat_id=chat_id, name=f'daily_{chat_id}')
        text = 'You will receive new weather data every 07:00 AM'

    await context.bot.send_message(chat_id=chat_id, text=text)


async def stop_daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    jobs = context.job_queue.get_jobs_by_name(f'daily_{chat_id}')
    if len(jobs) != 0:
        job = jobs[0]
        job.enabled = False
        job.schedule_removal()
        text = 'Stop receiving daily update!'
    else:
        text = "You haven't subscribed to daily update!"

    await context.bot.send_message(chat_id=chat_id, text=text)


async def alert_handler(context: ContextTypes.DEFAULT_TYPE):
    data = get_current_weather(latest_data)

    answer = (
        f"The weather in next hour will be: {data['condition']} {icon_bank['weather'][data['icon']]}\n"
        f"Temperature: {data['temperature']:.1f}°C {icon_bank['weather']['temperature']}\n"
        f"Wind speed: {data['wind_speed']:.1f} mps {icon_bank['weather']['wind_speed']}\n"
        f"Humidity: {data['humidity']:.1f}% {icon_bank['weather']['humidity']}\n"
        f"Pressure: {data['pressure']:.1f} hPa {icon_bank['weather']['pressure']}\n"
        f"Rain Probability: {data['rain_prob']:.2f}% {icon_bank['weather']['rain_prob']}\n"
        f"Please be careful!"
    )

    await context.bot.send_message(chat_id=context.job.chat_id, text=answer)


async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    jobs = context.job_queue.get_jobs_by_name(f'daily_{chat_id}')
    if len(jobs) != 0:
        text = 'You already subscribed to daily update'
    else:
        now = datetime.now()
        target_time = datetime(now.year, now.month, now.day, 7, 0, 0)
        if now > target_time:
            target_time += timedelta(days=1)
        total_second_till_next_7am = (target_time - now).total_seconds()
        context.job_queue.run_repeating(daily_handler, interval=60*60*24, first=2,
                                        chat_id=chat_id, name=f'daily_{chat_id}')
        text = 'You will receive new weather data every 07:00 AM'

    await context.bot.send_message(chat_id=chat_id, text=text)


async def stop_alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    jobs = context.job_queue.get_jobs_by_name(f'daily_{chat_id}')
    if len(jobs) != 0:
        job = jobs[0]
        job.enabled = False
        job.schedule_removal()
        text = 'Stop receiving daily update!'
    else:
        text = "You haven't subscribed to daily update!"

    await context.bot.send_message(chat_id=chat_id, text=text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_types = update.message.chat.type
    text = update.message.text
    print(f'User {update.message.chat_id} in {message_types}: "{text}"')
    answer = "Sorry, for now I can only take command, type /help for more information"
    print('Bot:', answer)
    await context.bot.send_message(chat_id=update.message.chat_id, text=answer)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


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

    # # hours regression
    # hours = [1, 3, 6, 9, 12]
    # features = ['temperature', 'humidity', 'pressure', 'wind_speed']
    # for hour in hours:
    #     for feature in features:
    #         file_path = f"model\\regression\\hours\\{hour}_{feature}_xgboost_regression.json"
    #         model = XGBRegressor()
    #         model.load_model(file_path)
    #         models['regression']['hours'][f'{hour}_{feature}'] = model
    #         print(f'finish load regression model ({hour}H-{feature})')
    #
    # # days regression
    # days = list(range(1, 8))
    # features = ['temperature', 'humidity', 'pressure', 'wind_speed']
    # for day in days:
    #     for feature in features:
    #         file_path = f"model\\regression\\days\\{day}_{feature}_xgboost_regression.json"
    #         model = XGBRegressor()
    #         model.load_model(file_path)
    #         models['regression']['days'][f'{day}_{feature}'] = model
    #         print(f'finish load regression model ({day}D-{feature})')

    end_time = datetime.now()
    print(end_time - start_time)
    return models


all_models = load_all_models()
data_thread = threading.Thread(target=fetch_data, daemon=True)
data_thread.start()
# -----------------------------------------------------------------------------------------


if __name__ == '__main__':
    print('Starting bot ...')
    app = Application.builder().token(TOKEN).build()

    # command
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("current", current_command))
    app.add_handler(CommandHandler("hour", hour_command))
    app.add_handler(CommandHandler("day", day_command))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("stop_daily", stop_daily_command))

    # message
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # error
    app.add_error_handler(error)

    # poll
    print('Polling ...')
    app.run_polling(poll_interval=2)
