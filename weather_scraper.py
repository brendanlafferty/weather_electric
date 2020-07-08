import yaml
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


_sel_dict = yaml.safe_load(open('keys/selenium.yml'))
_chromedriver = _sel_dict['webdriver']
os.environ["webdriver.chrome.driver"] = _chromedriver


def get_html(url, driver=None):
    if not driver:
        driver = webdriver.Chrome(_chromedriver)
    driver.get(url)
    # wait until the tr (table row) tag loads before continuing
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'tr')))
    return driver


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


def get_wunder_creds():
    yml_dict = yaml.safe_load(open('keys/wunderground.yml'))
    return yml_dict


if __name__ == '__main__':
    print('getting url')
    yml_d = get_wunder_creds()
    url = yml_d['url']
    url += '2020-07-07'
    fields_dict = yml_d['fields']
    print('URL: {}'.format(url))
    driver = get_html(url)
    soup = BeautifulSoup(driver.page_source, "lxml")
    features = {}
    print('Scraping Data:')
    for key in fields_dict:
        value = get_feature_wu(soup, key)
        new_key = fields_dict[key]
        features[new_key] = value
        print('{0:10s}: {1}'.format(new_key, value))
    print(get_hourly_table_wu(soup).prettify())
    driver.quit()



