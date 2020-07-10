import os
# from typing import Dict, Iterator, Union
# from time import sleep
from datetime import date, timedelta

import yaml
# import pandas as pd
# from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

_sel_dict = yaml.safe_load(open('keys/selenium.yml'))
_chromedriver_path = _sel_dict['webdriver']
os.environ["webdriver.chrome.driver"] = _chromedriver_path

_elect_dict = yaml.safe_load(open('keys/electric.yml'))

driver = webdriver.Chrome(_chromedriver_path)
driver.get(_elect_dict['login url'])

x = input('Please Log in on the web browser before continuing')

driver.get(_elect_dict['scraping url'])
driver.find_element(By.LINK_TEXT, "Daily").click()
driver.find_element(By.XPATH, '//*[@title="Click to select Date"]').click()
driver.find_element(By.LINK_TEXT, '1').click()
driver.find_element(By.ID, 'lnkExporttoExcel').click()
driver.find_element(By.XPATH, '//*[@title="Click to select Date"]').click()
driver.find_element(By.LINK_TEXT, 'Prev').click()


def decrement_30_days(start_date, end_date):
    days = int((end_date - start_date).days)
    iterations = days // 30 + 1
    for ind in range(iterations+1):
        yield end_date - timedelta(30 * ind)
