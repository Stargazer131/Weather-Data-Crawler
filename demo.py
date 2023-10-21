import pandas as pd


# combine all data from 2017-2023 to a single csv
# take out only necessary columns
def combine_data():
    selected = ['date', 'time', 'temperature', 'humidity', 'pressure', 'wind speed', 'condition']
    data = []
    for year in range(2017, 2024):
        folder = f'weather_data_{year}'
        for month in range(1, 13):
            if year == 2023 and month == 10:
                break
            file = f'weather_data_{month:02d}_{year}.csv'
            df = pd.read_csv(f'weather_data/{folder}/{file}')

            df['temperature'] = df['temperature'].str.replace('°F', '').astype(float)
            df['humidity'] = df['humidity'].str.replace('°%', '').astype(float)
            df['pressure'] = df['pressure'].str.replace('°in', '').astype(float)
            df['wind speed'] = df['wind speed'].str.replace('°mph', '').astype(float)
            df['pressure'] = df['pressure'] * 33.86389  # convert to hPa
            df = df[selected]
            data.append(df)

    stacked_df = pd.concat(data, axis=0, ignore_index=True)
    stacked_df.to_csv('raw_weather_data_2017-2023.csv', index=False)


def preprocess_data():
    df = pd.read_csv('raw_weather_data_2017-2023.csv')
    missing_value_columns = ['temperature', 'humidity', 'pressure', 'wind speed']
    zero_value_columns = ['temperature', 'humidity', 'pressure']
    df.at[df['wind speed'].argmax(), 'wind speed'] /= 10

    # fill missing using interpolation
    for column in zero_value_columns:
        df[column] = df[column].replace(0, float('nan'))

    # fill missing using interpolation
    for column in missing_value_columns:
        df[column] = df[column].interpolate(method='linear')

    # fill missing using forward fill
    df['condition'] = df['condition'].ffill()

    # convert less frequent weather condition to more frequent one
    df['condition'] = df['condition'].apply(convert_weather)

    # concert date and time to datetime
    df['date'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    df = df.drop(columns='time')
    df = df.rename(columns={'date': 'datetime'})

    df.to_csv('processed_weather_data_2017-2023.csv', index=False)


def convert_weather(weather_condition: str):
    value = weather_condition.lower()
    if 'thunder' in value or 't-storm' in value:
        return 'Thunderstorm'
    elif 'cloudy' in value:
        return 'Cloudy'
    elif 'rain' in value or 'drizzle' in value:
        return 'Rain'
    elif 'mist' in value or 'haze' in value or 'smoke' in value:
        return 'Fog'
    elif weather_condition == 'Patches of Fog':
        return 'Fog'
    elif weather_condition == 'Showers in the Vicinity':
        return 'Rain'
    elif weather_condition == 'Fair / Windy':
        return 'Fair'
    return weather_condition


def print_weather_condition_count():
    df = pd.read_csv('processed_weather_data_2017-2023.csv')
    # Get unique values and their counts
    unique_values = df['condition'].value_counts()

    # Print unique values and their counts
    for value, count in unique_values.items():
        print(f"Value: {value}, Count: {count}")


if __name__ == "__main__":
    preprocess_data()