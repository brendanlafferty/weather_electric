"""
This is a web-scraping module for scraping data from wunderground.com specifically historical data
pages. It requires 2 helper yaml files, 1 has the location of the chrome driver application for
selenium, the other has all the info for scraping wunderground.com.
data/selenium.yml:
    webdriver: path/to/chrome-driver


data/wunderground.yml:
    url: https://www.wunderground.com/history/daily/--------/date/
    features:
      High Temp: high
      Low Temp: low
      Day Average Temp: temp_mean
      Precipitation (past 24 hours from 07:53:00): precip
      Dew Point: dew
      High: dew_high
      Low: dew_low
      Average: dew_mean
      Max Wind Speed: wind
      Visibility: vis
      Sea Level Pressure: pres
      Actual Time: day_len
    dates:
      start: 2020-07-01
      end: 2020-07-05


"""
import os
from typing import Dict, Iterator, Union
from time import sleep
from datetime import date, timedelta

import yaml
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DataDict = Dict[str, float]
DailyDict = Dict[date, DataDict]
HourlyDict = Dict[date, str]

with open('keys/selenium.yml') as fs:
    _sel_dict = yaml.safe_load(fs)
_chromedriver_path = _sel_dict['webdriver']
os.environ["webdriver.chrome.driver"] = _chromedriver_path


def wu_hist_scraper(base_url: str,
                    start_date: date,
                    end_date: date,
                    feature_dict: dict,
                    driver: webdriver.Chrome = None) -> (pd.DataFrame,
                                                         pd.DataFrame,
                                                         webdriver.Chrome):
    """
    main scraper for scraping historical data from wunderground.com
    :param base_url: the base url to which dates will be appended to get the data
    :param start_date: start date in date format
    :param end_date: ending date in date format
    :param feature_dict: list of features to extract from the daily table
    :param driver: selenium instance of a webdriver
    :return: daily_df a dataframe of daily data, hourly_df a dataframe of hourly data,
             and driver the webdriver instance
    """
    daily_dict = {}
    hourly_list = []
    missing_value_count = 0
    for date_obj in drange_rev(start_date, end_date):
        date_str = date_obj.strftime('%Y-%m-%d')
        print('Getting data for: {}'.format(date_str))
        url_whole = base_url + date_str
        soup, driver = get_soup_wait_to_load(url_whole, driver=driver)
        daily_features, missing_value_count = get_daily_features_wu(soup, feature_dict,
                                                                    missing_value_count)
        daily_dict[date_obj] = daily_features
        hourly_table = get_hourly_table_wu(soup, date_obj)
        hourly_list.append(hourly_table)
        print('Success')
    hourly_df = pd.concat(hourly_list)
    daily_df = pd.DataFrame(daily_dict).T

    print('Missing Value Count: {}'.format(missing_value_count))
    return daily_df, hourly_df, driver


def get_daily_features_wu(soup: BeautifulSoup, feature_dict: Dict[str, str],
                          missing_count: int) -> (Dict[str, float], int):
    """
    iterates through each feature to be scraped and scrapes that feature
    :param soup: BeautifulSoup of the webpage
    :param feature_dict: a mapping of wunderground.com fields to clean names
    :param missing_count: the running count of missing values
    :return: a dictionary mapping field name to value, and the new missing value count
    """
    features = {}
    for feature in feature_dict:
        value, missing_count = get_daily_feature_wu(soup, feature, missing_count)
        new_key = feature_dict[feature]
        features[new_key] = value
    return features, missing_count


def get_soup_wait_to_load(url_complete, driver=None) -> (BeautifulSoup, webdriver.Chrome):
    """
    uses a selenium webdriver to navigate to the selected webpage and waits for the 'tr' tag to load
    :param url_complete: the complete url with date to load
    :param driver: webdriver, if None one will be instantiated
    :return: BeautifulSoup object of the webpage, the webdriver used
    """
    if not driver:
        driver = webdriver.Chrome(_chromedriver_path)
    driver.get(url_complete)
    # wait until the tr (table row) tag loads before continuing
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'tr')))
    # sometimes that is not enough for Actual Time (bottom of the table) so adding just a bit more
    sleep(.5)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    return soup, driver


def get_daily_feature_wu(soup: BeautifulSoup, feature_name: str,
                         missing_count: int) -> (Union[float, None], int):
    """
    This function scrapes data from wunderground.com's historical data pages.  This specifically
    scrapes from the daily data and only pulls the "Actual" column from the table. Some feature
    include "High Temp", "Low Temp", etc.
    :param soup: BeautifulSoup object of a wundergroud.com historical data page
    :param feature_name: feature to scrape most are numeric fields except "Actual Time" which is the
                         length of day string formatted "##h ##m"
    :param missing_count: running count of missing values
    :return: numeric value of the feature being scraped, returns the new missing count
    """
    # adding logic for precipitation field because the actual tag varies a bit
    # only need to match the start of the string
    if len(feature_name) > 20:
        feature_abr = feature_name[0:20]
        feature_loc = soup.find(text=lambda string: string and string.startswith(feature_abr))
    else:
        feature_loc = soup.find(text=feature_name)
    try:
        value_actual = feature_loc.find_next()
    except AttributeError:
        missing_count += 1
        print('Warning "{}" did not load'.format(feature_name))
        print('None will be returned instead')
        print('Missing Value Count: {}'.format(missing_count))
        return None
    value = value_actual.text
    try:
        value = float(value)
    except ValueError:
        value = hour_mins_to_mins(value)
    return value, missing_count


def get_hourly_table_wu(soup: BeautifulSoup, date_obj: date) -> pd.DataFrame:
    """
    uses pandas to read the html table (this is surprisingly effective) but returns only
    strings with units to be parsed later
    :param soup: BeatifulSoup object of the webpage
    :param date_obj: date being queried
    :return: dataframe of the hourly table data
    """
    hourly_table = pd.read_html(str(soup.select('table')[2]))[0]
    hourly_table['Date'] = date_obj
    return hourly_table


def hour_mins_to_mins(hr_min_str: str) -> int:
    """
    converts strings of the form "XXh XXm" to an integer representing minutes
    :param hr_min_str: string with hours and mins in the format "XXh XXm"
    :return: minutes
    """
    split_str = hr_min_str.split(' ')
    mins = int(split_str[0][:-1]) * 60 + int(split_str[1][:-1])
    return mins


def get_wunder_creds(file_path: str = 'keys/wunderground.yml') -> dict:
    """
    reads the helper yaml file to get the base url, the features to query and the start and end
    dates. Should read something like this:
    {
    url: "", features: {"WU_feature": "new feature name"},
    dates: {start: "YYYY-MM-DD", end: "YYYY-MM-DD}
    }
    :param file_path: path to helper file
    :return: dictionary contents of the file
    """
    with open(file_path) as f_stream:
        yml_dict = yaml.safe_load(f_stream)
    return yml_dict


def drange_rev(start_date: date, end_date: date) -> Iterator[date]:
    """
    this generator yields dates that it decrements from end_date to start_date inclusive
    :param start_date: earliest date
    :param end_date: latest date
    """
    days = (end_date - start_date).days
    for ind in range(days + 1):
        yield end_date - timedelta(ind)


def save_daily(daily_df: pd.DataFrame, start_date: date, end_date: date):
    """
    takes the dataframe of daily data and saves it to a csv in /data/ with dates in the filename
    :param daily_df: dataframe to save
    :param start_date: starting date of the data frame (this could be looked up but its faster this
                       way)
    :param end_date: ending date of the data frame (this could be looked up but its faster this way)
    """
    file_path = 'data/daily_{}_{}.csv'
    start = start_date.strftime('%Y%m%d')
    end = end_date.strftime('%Y%m%d')
    daily_df.to_csv(file_path.format(start, end))


def save_hourly(hourly_df: pd.DataFrame, start_date: date, end_date: date):
    """
    takes the dataframe of hourly data and saves it to a csv in /data/ with dates in the filename
    :param hourly_df: dataframe to save
    :param start_date: starting date of the data frame (this could be looked up but its faster this
                       way)
    :param end_date: ending date of the data frame (this could be looked up but its faster this way)
    """
    file_path = 'data/hourly_{}_{}.csv'
    start = start_date.strftime('%Y%m%d')
    end = end_date.strftime('%Y%m%d')
    hourly_df.to_csv(file_path.format(start, end), index=False)


def main():
    """
    main script saves results to 2 csvs in /data/
    """
    wu_setup_dict = get_wunder_creds()
    base_url = wu_setup_dict['url']
    daily_features_mapping = wu_setup_dict['features']
    start = wu_setup_dict['dates']['start']
    stop = wu_setup_dict['dates']['end']
    daily_results, hourly_results, driver = wu_hist_scraper(base_url,
                                                            start,
                                                            stop,
                                                            daily_features_mapping)
    save_daily(daily_results, start, stop)
    save_hourly(hourly_results, start, stop)
    driver.quit()


if __name__ == '__main__':
    main()
