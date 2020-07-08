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

Data_Dict = Dict[str, float]


_sel_dict = yaml.safe_load(open('keys/selenium.yml'))
_chromedriver = _sel_dict['webdriver']
os.environ["webdriver.chrome.driver"] = _chromedriver


def wu_hist_scraper(base_url, start_date, end_date, feature_dict, driver=None) -> (Dict[str, Dict[str, float]],
                                                                                   webdriver.Chrome):
    date_dict = {}
    for date_obj in drange_rev(start_date, end_date):
        date_str = date_obj.strftime('%Y-%m-%d')
        url_whole = base_url + date_str
        soup, driver = get_soup(url_whole, driver=driver)
        features = get_features_wu(soup, feature_dict)
        date_dict[date_obj] = features
    return date_dict, driver


def get_features_wu(soup: BeautifulSoup, feature_dict: Dict[str, str]) -> Dict[str, float]:
    features = {}
    for feature in feature_dict:
        value = get_feature_wu(soup, feature)
        new_key = feature_dict[feature]
        features[new_key] = value
    return features


def get_soup(url_complete, driver=None):
    if not driver:
        driver = webdriver.Chrome(_chromedriver)
    driver.get(url_complete)
    # wait until the tr (table row) tag loads before continuing
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'tr')))
    sleep(1)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    return soup, driver


def get_feature_wu(soup: BeautifulSoup, feature_name: str):
    """
    This function scrapes data from wunderground.com's historical data pages.  This specifically scrapes from the daily
    data and only pulls the "Actual" column from the table. Some feature include "High Temp", "Low Temp", etc.
    :param soup: BeautifulSoup object of a wundergroud.com historical data page
    :param feature_name: feature to scrape most are numeric fields except "Actual Time" which is the length of day
                         string formatted "##h ##m"
    :return: numeric value of the feature being scraped
    """
    feature_loc = soup.find(text=feature_name)

    value_actual = feature_loc.find_next()
    value = value_actual.text
    try:
        value = float(value)
    except ValueError:
        value = hr_min_str_to_min_int(value)
    return value


def get_hourly_table_wu(soup: BeautifulSoup):
    return soup.select('table')[2]  # for parsing later


def hr_min_str_to_min_int(hr_min_str: str):
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


if __name__ == '__main__':
    print('getting url')
    yml_d = get_wunder_creds()
    url = yml_d['url']
    fields_dict = yml_d['fields']
    start = yml_d['dates']['start']
    stop = yml_d['dates']['end']
    results, driver = wu_hist_scraper(url, start, stop, fields_dict)
    print(pd.DataFrame(results))
    driver.quit()



