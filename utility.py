from xgboost import XGBClassifier, XGBRegressor
import pandas as pd


def check_classification_model():
    df = pd.read_csv('processed_weather_data_2017-2023.csv')
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
    df = pd.read_csv('processed_weather_data_2017-2023.csv')
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['month'] = df['datetime'].dt.month
    df['day'] = df['datetime'].dt.day
    df['hour'] = df['datetime'].dt.hour
    X = df.drop(columns=['datetime', 'condition'])
    data = X.iloc[0].values.reshape(1, -1)

    model = XGBRegressor()
    model.load_model("model\\24h_regression\\24h_temp_xgboost_regression.json")
    print(model.predict(data))


test_regression_model()
