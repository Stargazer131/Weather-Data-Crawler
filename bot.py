import threading
import time
from datetime import datetime, timedelta

import numpy as np
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from xgboost import XGBClassifier, XGBRegressor

from utility import get_sensor_data, round_time, get_api_data, inverse_transform_condition, day_or_night

TOKEN = '6710672539:AAH5AVA2q6yRboBpDXn-_4GAHPTEvMb8LJQ'


latest_data = (datetime.now(), 75, 70, 1000, 5)


def fetch_data():
    global latest_data
    time.sleep(2)
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
        time.sleep(30)


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

    await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)


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

    await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)


async def current_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    timestamp, temp, humid, press, wind = latest_data

    inputs = [temp, humid, press, wind, timestamp.month, timestamp.day, timestamp.hour]
    inputs = np.array(inputs).reshape(1, -1)
    model = all_models['classification']
    condition = inverse_transform_condition(model.predict(inputs)[0]).lower()
    rain_prob = model.predict_proba(inputs)[0][3] * 100
    time_of_day = day_or_night(timestamp.hour, 0)
    icon = condition
    if condition == 'fair':
        icon = time_of_day

    temp = (temp-32) * 5/9
    wind = wind * 0.44704

    answer = (
        f"The weather is: {condition} {icon_bank['weather'][icon]}\n"
        f"Temperature: {temp:.1f}°C {icon_bank['weather']['temperature']}\n"
        f"Wind speed: {wind:.1f} mps {icon_bank['weather']['wind_speed']}\n"
        f"Humidity: {humid:.1f}% {icon_bank['weather']['humidity']}\n"
        f"Pressure: {press:.1f} hPa {icon_bank['weather']['pressure']}\n"
        f"Rain Probability: {rain_prob:.2f}% {icon_bank['weather']['rain_prob']}\n"
    )

    await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_types = update.message.chat.type
    text = update.message.text
    print(f'User {update.effective_chat.id} in {message_types}: "{text}"')
    answer = "Sorry, for now I can only take command, type /help for more information"
    print('Bot:', answer)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)


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

    # message
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # error
    app.add_error_handler(error)

    # poll
    print('Polling ...')
    app.run_polling(poll_interval=2)
