import yaml
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


sel_dict = yaml.load(open('keys/selenium.yml'))
_chromedriver = sel_dict['webdriver']
os.environ["webdriver.chrome.driver"] = _chromedriver


def get_feature_wu(soup: BeautifulSoup, feature_name: str):
    feature_loc = soup.find(text=feature_name)

    value_actual = feature_loc.find_next()
    value_ave = value_actual.find_next()
    value_record = value_ave.find_next()
    values = [value_actual.text, value_ave.text, value_record.text]
    return values


def get_url():
    yml_dict = yaml.load(open('keys/wunderground.yml'))
    return yml_dict['url']


if __name__ == '__main__':
    print('getting url')
    url = get_url()
    url += '2020-07-07'
    print('URL: {}'.format(url))
    driver = webdriver.Chrome(_chromedriver)
    print('Opening website')
    driver.get(url)
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'tr')))
    soup = BeautifulSoup(driver.page_source, "lxml")
    high_temp = get_feature_wu(soup, "High Temp")
    print('high temp: \n', high_temp[0])
    print('Historical Average:\n', high_temp[1])
    print('Record:\n', high_temp[2])
    driver.quit()



