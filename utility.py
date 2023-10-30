from datetime import datetime

from xgboost import XGBClassifier, XGBRegressor
import pandas as pd


def check_classification_model():
    df = pd.read_csv('weather_data/processed_weather_data_2017-2023.csv')
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['month'] = df['datetime'].dt.month
    df['day'] = df['datetime'].dt.day
    df['hour'] = df['datetime'].dt.hour
    X = df.drop(columns=['datetime', 'condition'])
    data = X.iloc[0].values.reshape(1, -1)

    model = XGBClassifier()
    model.load_model("model\\classification\\xgboost_classification_model.json")
    print(model.predict(data))


def test_regression_model():
    df = pd.read_csv('weather_data/processed_weather_data_2017-2023.csv')
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['month'] = df['datetime'].dt.month
    df['day'] = df['datetime'].dt.day
    df['hour'] = df['datetime'].dt.hour
    X = df.drop(columns=['datetime', 'condition'])
    data = X.iloc[0].values.reshape(1, -1)

    model = XGBRegressor()
    model.load_model("model\\24h_regression\\24h_temp_xgboost_regression.json")
    print(model.predict(data))


def load_all_models():
    start_time = datetime.now()
    classification_model = XGBClassifier()
    classification_model.load_model("model\\classification\\xgboost_classification_model.json")
    print('finish load classification model')

    hours = [1, 3, 6, 12, 24]
    features = ['temp', 'humid', 'press', 'wind']
    regression_models = {}
    for hour in hours:
        for feature in features:
            regression_model = XGBRegressor()
            file_path = f"model\\regression\\{hour}h_{feature}_xgboost_regression.json"
            regression_model.load_model(file_path)
            regression_models[f'{hour}h_{feature}'] = regression_model
            print(f'finish load regression model ({hour}-{feature})')

    end_time = datetime.now()
    print(end_time - start_time)


load_all_models()
