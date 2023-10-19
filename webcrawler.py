from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import pandas as pd
import utility
from sklearn.preprocessing import StandardScaler


class WebCrawler:
    def __init__(self, show_browser=True):
        self.station_name = 'NOI BAI INTERNATIONAL AIRPORT STATION'
        self.months = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        options = Options()
        self.url = 'https://www.wunderground.com/history/daily/vn/hanoi/VVNB/date/'
        self.labels = ['date', 'time', 'temperature', 'dewpoint', 'humidity', 'wind',
                       'wind speed', 'wind gust', 'pressure', 'precip', 'condition']
        if not show_browser:
            options.add_argument('--headless')
            # headless mode didn't open in full resolution
            options.add_argument('--window-size=1440,900')

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30)

    def get_daily_data(self, year: int, month: int, day: int):
        date = f'{year}-{month}-{day}'
        date_str = f'{day:02d}/{month:02d}/{year}'
        url = self.url + date
        self.driver.get(url)
        self.wait.until(
            ec.presence_of_all_elements_located((By.CSS_SELECTOR, '[aria-labelledby="History observation"]'))
        )

        # Parse the HTML content
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Find the table you want to parse
        table = soup.select_one('table[aria-labelledby="History observation"]')

        # Iterate through the rows and cells to extract data
        data = [[None for x in range(11)] for y in range(48)]
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            try:
                timestamp = cells[0].text
            except:
                continue
            index = self.get_index(timestamp)
            if index == -1:
                continue
            for j in range(2, 11):
                data[index][j] = cells[j-1].text

        for i in range(48):
            data[i][0] = date_str
            data[i][1] = self.get_timestamp(i)

        print(f'Finished day {date_str}!')
        return pd.DataFrame(data, columns=self.labels)

    @staticmethod
    def get_index(timestamp: str):
        try:
            if len(timestamp) < 8:
                timestamp = '0' + timestamp
            hour, minute = int(timestamp[:2]), int(timestamp[3:5])
            hour = hour % 12
            minute = minute // 30
            index = hour * 2 + minute
            if timestamp.endswith('PM'):
                index += 24
            return index
        except:
            return -1

    @staticmethod
    def get_timestamp(index: int):
        hour = index % 24
        minute = 0 if (hour % 2 == 0) else 30
        hour //= 2
        if hour == 0:
            hour += 12
        time = 'AM' if (index <= 23) else 'PM'
        return f'{hour:02d}:{minute:02d} {time}'

    def write_daily_data_to_csv(self, year: int, month: int, day: int):
        data = self.get_daily_data(year, month, day)
        data.to_csv(f'weather_data_{day:02d}_{month:02d}_{year}.csv', index=False)

    def write_month_data_to_csv(self, year: int, month: int):
        days = self.months[month]
        data = []
        for day in range(1, days+1):
            data.append(self.get_daily_data(year, month, day))
        stacked_df = pd.concat(data, axis=0, ignore_index=True)
        stacked_df.to_csv(f'weather_data_{month:02d}_{year}.csv', index=False)

    def write_year_data_to_csv(self, year: int):
        year_data = []
        for month in range(1, 13):
            days = self.months[month]
            month_data = []
            for day in range(1, days + 1):
                month_data.append(self.get_daily_data(year, month, day))
            stacked_month = pd.concat(month_data, axis=0, ignore_index=True)
            year_data.append(stacked_month)
        stacked_df = pd.concat(year_data, axis=0, ignore_index=True)
        stacked_df.to_csv(f'weather_data_{year}.csv', index=False)

    def stop(self):
        self.driver.quit()


# combine all data from 2020-2023 to a single csv
# take out only necessary columns
def combine_data():
    label = ['date', 'time', 'temperature(F)', 'dewpoint(F)', 'humidity(%)', 'wind_direction',
             'wind speed(mps)', 'wind gust(mph)', 'pressure(hPa)', 'precip(in)', 'condition']
    selected = ['date', 'time', 'temperature(F)', 'humidity(%)', 'pressure(hPa)',
                'wind_direction', 'wind speed(mps)', 'condition']
    data = []
    for year in range(2023, 2024):
        for month in range(1, 10):
            file = f'weather_data_{month:02d}_{year}.csv'
            df = pd.read_csv(file)
            df.columns = label

            df['temperature(F)'] = df['temperature(F)'].str.replace('°F', '').astype(float)

            df['humidity(%)'] = df['humidity(%)'].str.replace('°%', '').astype(float)

            df['pressure(hPa)'] = df['pressure(hPa)'].str.replace('°in', '').astype(float)
            df['pressure(hPa)'] = df['pressure(hPa)'] * 33.86389  # convert to hPa

            df['wind_direction'] = df['wind_direction'].apply(utility.wind_direction_to_degree)

            df['wind speed(mps)'] = df['wind speed(mps)'].str.replace('°mph', '').astype(float)
            df['wind speed(mps)'] = df['wind speed(mps)'] * 0.44704  # convert to m/s

            df = df[selected]
            data.append(df)
    stacked_df = pd.concat(data, axis=0, ignore_index=True)
    stacked_df.to_csv('raw_weather_data_2023.csv', index=False)


def preprocess_data():
    df = pd.read_csv('raw_weather_data_2020-2023.csv')
    df.at[df['wind speed(mps)'].argmax(), 'wind speed(mps)'] /= 10
    missing_value_columns = ['temperature(F)', 'humidity(%)', 'pressure(hPa)', 'wind_direction', 'wind speed(mps)']

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

    df.to_csv('processed_weather_data_2020-2023.csv', index=False)


def convert_weather(weather_condition: str):
    value = weather_condition.lower()
    if 'thunder' in value or 't-storm' in value:
        return 'Thunderstorm'
    elif 'rain' in value:
        return 'Rain'
    elif 'drizzle' in value:
        return 'Drizzle'
    elif 'windy' in value:
        return 'Windy'
    elif weather_condition == 'Patches of Fog':
        return 'Fog'
    elif weather_condition == 'Showers in the Vicinity':
        return 'Rain'
    return weather_condition


def print_weather_condition_count():
    df = pd.read_csv('processed_weather_data_2020-2023.csv')
    # Get unique values and their counts
    unique_values = df['condition'].value_counts()

    # Print unique values and their counts
    for value, count in unique_values.items():
        print(f"Value: {value}, Count: {count}")


if __name__ == "__main__":
    df = pd.read_csv('processed_weather_data_2020-2023.csv')

    df['temperature(F)'] /= 122
    df['pressure(hPa)'] /= 1100
    df['humidity(%)'] /= 100
    df['wind_direction'] /= 360

    wind_scaler = StandardScaler()
    wind_scaler.fit(df[['wind speed(mps)']])
    df['wind speed(mps)'] = wind_scaler.transform(df[['wind speed(mps)']])