"""
This module has 2 main functions, 1 an auto-saver/webscraper that navigates through the utilites
account pages to download the specified data, and 2 a parsing tool to concatenate the files after
downloading them. This file also accepts (optional) system arguments specifically:

    $ python electric_scraper [mode] [filepath]

where [mode] selects (a)uto-save or (p)arse (just checks for p or parse)
and [filepath] is the filepath to search for files and where to save the result
System arguments are optional

The auto-saver/webscraper uses 2 helper files:

outputs/selenium.yml:
    webdriver: path/to/chrome-driver

outputs/electric.yml:
    login url: --------
    usage url: --------
    dates:
      start: 2020-07-01
      end: 2020-07-05
"""

import os
import sys
from typing import Iterator
from time import sleep
from datetime import date, timedelta, datetime

import yaml
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

with open('keys/selenium.yml') as f_stream:
    _sel_dict = yaml.safe_load(f_stream)

_chromedriver_path = _sel_dict['webdriver']
os.environ["webdriver.chrome.driver"] = _chromedriver_path

_PRE_CLICK_WAIT = 5
_POST_CLICK_WAIT = .1


def electric_usage_auto_saver(login_url, usage_url, start_date, end_date, driver=None) -> webdriver:
    """
    this is the main scraper for saving the usage data files
    :param login_url: url to the login page
    :param usage_url: url to the usage download page
    :param start_date: starting date of data to be gathered
    :param end_date: ending date of data to be gathered
    :param driver: webdriver if None it will be instantiated
    :return: webdriver object
    """
    driver = navigate_to_login(login_url, driver)
    navigate_to_daily_usage(usage_url, driver)
    current_date_showing = datetime.now().date()
    for prev_date in decrement_30_days(start_date, end_date):
        print('Getting data for the 30 day period ending in {}'.format(prev_date))
        months_away = diff_months(prev_date, current_date_showing)
        change_months(months_away, driver)
        select_day(prev_date.day, driver)
        download_excel(driver)
        print('Downloaded Excel')
        current_date_showing = prev_date

    return driver


def get_electric_creds(file_path: str = 'keys/electric.yml') -> dict:
    """
    loads the helper yaml file with the urls and starting dates
    :param file_path: path to helper file
    :return: dictionary of yaml file
    """
    with open(file_path) as f_s:
        yml_dict = yaml.safe_load(f_s)
    return yml_dict


def navigate_to_login(login_url: str, driver: webdriver = None) -> webdriver:
    """
    Navigates to the login page and pauses for the user to login. If a wedriver is not given a new
    one will be instantiated
    :param login_url: url to the login page
    :param driver: webdriver
    :return: the webdriver used
    """
    if not driver:
        driver = webdriver.Chrome(_chromedriver_path)
    driver.get(login_url)
    input('Please log in on the web browser before continuing\n')
    return driver


def navigate_to_daily_usage(usage_url: str, driver: webdriver):
    """
    navigates to the usage page and sets the
    :param usage_url: url to the usage page
    :param driver: webdriver
    """
    driver.get(usage_url)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, 'Daily')))
    sleep(_PRE_CLICK_WAIT)
    driver.find_element(By.LINK_TEXT, "Daily").click()
    sleep(_POST_CLICK_WAIT)


def change_months(num_months: int, driver: webdriver):
    """
    opens select date menu and goes back a set number of months
    :param num_months: integer number of months to go back
    :param driver: webdriver
    """
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@title="Click to select Date"]'))
    )
    sleep(_PRE_CLICK_WAIT)
    driver.find_element(By.XPATH, '//*[@title="Click to select Date"]').click()
    sleep(_POST_CLICK_WAIT)
    for index in range(num_months):
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, 'Prev')))
        sleep(_PRE_CLICK_WAIT)
        driver.find_element(By.LINK_TEXT, 'Prev').click()
        sleep(_POST_CLICK_WAIT)


def select_day(day_num: int, driver: webdriver):
    """
    with an open select dates menu this selects the day number
    :param day_num: int of day to select
    :param driver: webdriver
    """
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, str(day_num))))
    sleep(_PRE_CLICK_WAIT)
    driver.find_element(By.LINK_TEXT, str(day_num)).click()
    sleep(_POST_CLICK_WAIT)


def download_excel(driver: webdriver):
    """
    Initiates the download of the data being displayed
    :param driver: webdriver
    """
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'lnkExporttoExcel')))
    sleep(_PRE_CLICK_WAIT)
    driver.find_element(By.ID, 'lnkExporttoExcel').click()
    sleep(_POST_CLICK_WAIT)


def decrement_30_days(start_date: date, end_date: date) -> Iterator[date]:
    """
    generator that moves 30 days back at a time
    :param start_date: earliest date
    :param end_date: lastest date
    """
    days = (end_date - start_date).days
    iterations = days // 30 + 1
    for ind in range(iterations):
        yield end_date - timedelta(30 * ind)


def diff_months(low: date, high: date) -> int:
    """
    returns the number of months between 2 dates so that the date menu can be changes appropriately
    so 2020/06/30 and 2020/07/01 will return 1 and 2020/07/01 and 2020/07/31 will return 0
    :param low: earliest date
    :param high: lastest date
    :return: number of months
    """
    months = (high.year - low.year) * 12 + high.month - low.month
    return months


def parse(directory: str = 'outputs/') -> pd.DataFrame:
    """"""
    files_gathered = []
    for filename in os.listdir(directory):
        print(f'File to check: {filename}')
        if filename.startswith('Usage'):
            print(f'appending {filename}')
            files_gathered.append(pd.read_excel(directory+filename, skiprows=4))
    usage_df = pd.concat(files_gathered)
    usage_df['Usage Date'] = pd.to_datetime(usage_df['Usage Date']).dt.date
    usage_df.sort_values('Usage Date', inplace=True)
    start = usage_df.iloc[0, 0]
    end = usage_df.iloc[-1, 0]
    usage_df.to_csv(directory+f'usage_df_{start:%Y%m%d}_{end:%Y%m%d}.csv', index=False)
    return usage_df


def main():
    """
    main script that handles the auto-scraper
    """
    electric_setup_dict = get_electric_creds()
    login_url = electric_setup_dict['login url']
    usage_url = electric_setup_dict['usage url']
    start = electric_setup_dict['dates']['start']
    end = electric_setup_dict['dates']['end']
    driver = electric_usage_auto_saver(login_url, usage_url, start, end)
    sleep(_PRE_CLICK_WAIT)
    driver.close()


if __name__ == '__main__':
    try:
        ans = sys.argv[1]
    except IndexError:
        ans = input('(P)arse or (A)utosave:\n')
    if ans.lower() in ['p', 'parse']:
        try:
            parse(sys.argv[2])
        except IndexError:
            parse()
    else:
        main()
