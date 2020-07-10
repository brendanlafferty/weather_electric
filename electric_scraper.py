import os
from typing import Iterator
from time import sleep
from datetime import date, timedelta, datetime

import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

with open('keys/selenium.yml') as fs:
    _sel_dict = yaml.safe_load(fs)

_chromedriver_path = _sel_dict['webdriver']
os.environ["webdriver.chrome.driver"] = _chromedriver_path

_PRE_CLICK_WAIT = 5
_POST_CLICK_WAIT = .1


def electric_usage_auto_saver(login_url, usage_url, start_date, end_date, driver=None):
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

    return driver


def get_electric_creds(file_path: str = 'keys/electric.yml') -> dict:
    with open(file_path) as fs:
        yml_dict = yaml.safe_load(fs)
    return yml_dict


def navigate_to_login(login_url: str, driver: webdriver = None):
    if not driver:
        driver = webdriver.Chrome(_chromedriver_path)
    driver.get(login_url)
    input('Please log in on the web browser before continuing\n')
    return driver


def navigate_to_daily_usage(usage_url: str, driver: webdriver):
    driver.get(usage_url)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, 'Daily')))
    sleep(_PRE_CLICK_WAIT)
    driver.find_element(By.LINK_TEXT, "Daily").click()
    sleep(_POST_CLICK_WAIT)


def change_months(num_months, driver):
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


def select_day(day_num, driver):
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, str(day_num))))
    sleep(_PRE_CLICK_WAIT)
    driver.find_element(By.LINK_TEXT, str(day_num)).click()
    sleep(_POST_CLICK_WAIT)


def download_excel(driver):
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'lnkExporttoExcel')))
    sleep(_PRE_CLICK_WAIT)
    driver.find_element(By.ID, 'lnkExporttoExcel').click()
    sleep(_POST_CLICK_WAIT)


def decrement_30_days(start_date: date, end_date: date) -> Iterator[date]:
    days = (end_date - start_date).days
    iterations = days // 30 + 1
    for ind in range(iterations):
        yield end_date - timedelta(30 * ind)


def diff_months(low: date, high: date):
    if high.year == low.year:
        months = high.month - low.month
    else:
        months = (high.year - low.year) * 12 + high.month - low.month
    return months


def main():
    electric_setup_dict = get_electric_creds()
    login_url = electric_setup_dict['login url']
    usage_url = electric_setup_dict['usage url']
    start = electric_setup_dict['dates']['start']
    end = electric_setup_dict['dates']['end']
    driver = electric_usage_auto_saver(login_url, usage_url, start, end)
    sleep(_PRE_CLICK_WAIT)
    driver.close()


if __name__ == '__main__':
    main()
