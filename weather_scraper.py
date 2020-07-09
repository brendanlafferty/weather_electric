import yaml
import os
from typing import Dict
from datetime import date, timedelta
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

DataDict = Dict[str, float]
DailyDict = Dict[date, DataDict]
HourlyDict = Dict[date, str]

_sel_dict = yaml.safe_load(open('keys/selenium.yml'))
_chromedriver_path = _sel_dict['webdriver']
os.environ["webdriver.chrome.driver"] = _chromedriver_path

_missing_value_count = 0

def wu_hist_scraper(base_url: str,
                    start_date: date,
                    end_date: date,
                    feature_dict: dict,
                    driver: webdriver.Chrome = None) -> (DailyDict,
                                                         pd.DataFrame,
                                                         webdriver.Chrome):
    """
    main scraper for scraping historical data from wunderground.com
    :param base_url: the base url to which dates will be appended to get the data
    :param start_date: start date in date format
    :param end_date: ending date in date format
    :param feature_dict: list of features to extract from the daily table
    :param driver: selenium instance of a webdriver
    :return:
    """
    daily_dict = {}
    hourly_list = []
    for date_obj in drange_rev(start_date, end_date):
        date_str = date_obj.strftime('%Y-%m-%d')
        print('Getting data for: {}'.format(date_str))
        url_whole = base_url + date_str
        soup, driver = get_soup(url_whole, driver=driver)
        daily_features = get_daily_features_wu(soup, feature_dict)
        daily_dict[date_obj] = daily_features
        hourly_table = get_hourly_table_wu(soup, date_obj)
        hourly_list.append(hourly_table)
        print('Success')
    hourly_df = pd.concat(hourly_list)

    return daily_dict, hourly_df, driver


def get_daily_features_wu(soup: BeautifulSoup, feature_dict: Dict[str, str]) -> Dict[str, float]:
    features = {}
    for feature in feature_dict:
        value = get_daily_feature_wu(soup, feature)
        new_key = feature_dict[feature]
        features[new_key] = value
    return features


def get_soup(url_complete, driver=None):
    if not driver:
        driver = webdriver.Chrome(_chromedriver_path)
    driver.get(url_complete)
    # wait until the tr (table row) tag loads before continuing
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'tr')))
    sleep(1)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    return soup, driver


def get_daily_feature_wu(soup: BeautifulSoup, feature_name: str):
    """
    This function scrapes data from wunderground.com's historical data pages.  This specifically scrapes from the daily
    data and only pulls the "Actual" column from the table. Some feature include "High Temp", "Low Temp", etc.
    :param soup: BeautifulSoup object of a wundergroud.com historical data page
    :param feature_name: feature to scrape most are numeric fields except "Actual Time" which is the length of day
                         string formatted "##h ##m"
    :return: numeric value of the feature being scraped
    """
    feature_loc = soup.find(text=feature_name)
    try:
        value_actual = feature_loc.find_next()
    except AttributeError:
        global _missing_value_count
        _missing_value_count += 1
        print('Warning "{}" did not load'.format(feature_name))
        print('None will be returned instead')
        print('Missing Value Count: {}'.format(_missing_value_count))
        return None
    value = value_actual.text
    try:
        value = float(value)
    except ValueError:
        value = hour_mins_to_mins(value)
    return value


def get_hourly_table_wu(soup: BeautifulSoup, date_obj: date) -> pd.DataFrame:
    hourly_table = pd.read_html(str(soup.select('table')[2]))[0]
    hourly_table['Date'] = date_obj
    return hourly_table


def hour_mins_to_mins(hr_min_str: str):
    split_str = hr_min_str.split(' ')
    min = int(split_str[0][:-1])*60 + int(split_str[1][:-1])
    return min


def get_wunder_creds(file_path: str='keys/wunderground.yml'):
    yml_dict = yaml.safe_load(open(file_path))
    return yml_dict


def drange_rev(start_date: date, end_date: date):
    days = int((end_date - start_date).days)
    for ind in range(days + 1):
        yield end_date - timedelta(ind)


def save_daily(daily_dict: DailyDict, start_date: date, end_date: date):
    file_path = 'outputs/daily_{}_{}.csv'
    start = start_date.strftime('%Y%m%d')
    end = end_date.strftime('%Y%m%d')
    df = pd.DataFrame(daily_dict).T
    df.to_csv(file_path.format(start, end))


def save_hourly(hourly_df: pd.DataFrame, start_date: date, end_date: date):
    file_path = 'outputs/hourly_{}_{}.csv'
    start = start_date.strftime('%Y%m%d')
    end = end_date.strftime('%Y%m%d')
    hourly_df.to_csv(file_path.format(start, end), index=False)


def main():
    wu_setup_dict = get_wunder_creds()
    base_url = wu_setup_dict['url']
    daily_features_mapping = wu_setup_dict['features']
    start = wu_setup_dict['dates']['start']
    stop = wu_setup_dict['dates']['end']
    daily_results, hourly_results, driver = wu_hist_scraper(base_url, start, stop, daily_features_mapping)
    save_daily(daily_results, start, stop)
    save_hourly(hourly_results, start, stop)
    driver.quit()
    print('Missing Value Count: {}'.format(_missing_value_count))


if __name__ == '__main__':
    main()



