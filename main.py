from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import pandas as pd


class WebCrawler:
    def __init__(self, show_browser=True):
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
        data = []
        rows = table.find_all('tr')
        for row in rows:
            data.append([date_str])
            cells = row.find_all('td')
            for cell in cells:
                data[-1].append(cell.text)
        print(f'Finished day {date_str}!')
        return pd.DataFrame(data[1:49], columns=self.labels)

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


if __name__ == "__main__":
    crawler = WebCrawler(show_browser=False)
    # crawler.write_daily_data_to_csv(year=2020, month=1, day=1)
    crawler.write_month_data_to_csv(year=2020, month=12)
    # crawler.write_year_data_to_csv(2020)
    crawler.stop()
