import csv
from selenium import webdriver
import pandas as pd
import os as os
import time
import subprocess
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.support import expected_conditions as ec


def reader(file_name):
    with open(file_name, encoding='utf-8', errors="ignore") as f:
        reader_data = csv.reader(f, delimiter=',')
        for row in reader_data:
            yield row

script_path = os.getcwd()
os.chdir(script_path + "\\Results")

txt_reader = reader("new21.csv")
first_line = next(txt_reader)
col_count = len(first_line)
data = []

"""Парсинг страницы с должниками"""
def parser_main_page(driver, inn):
    person = inn
    try:
        #time.sleep(5)
        INN = driver.find_element_by_id('ctl00_cphBody_PersonCode1_CodeTextBox')
        INN.clear()
        INN.send_keys(person)
        btn_search = driver.find_element_by_id('ctl00_cphBody_btnSearch')
        btn_search.click()
        #time.sleep(5)
        person = driver.find_element_by_xpath("//table[@id='ctl00_cphBody_gvDebtors']/tbody/tr[2]/td[2]/a")
    except NoSuchElementException as e:
        person = None
    return person


chromeOptions = webdriver.ChromeOptions()
chromeOptions.add_experimental_option('excludeSwitches',['enable-logging'])
result = pd.DataFrame(columns=['FULLNAME','INN','HREF'])

driver1 = webdriver.Chrome("C:/Program Files (x86)/Google/Chrome/Application/chromedriver.exe", options=chromeOptions)
#driver1.set_page_load_timeout(5)
driver1.get("https://bankrot.fedresurs.ru/DebtorsSearch.aspx")
fisic = driver1.find_element_by_id('ctl00_cphBody_rblDebtorType_1')
fisic.click()

i = 0
for line in txt_reader:
    #print(line[0])
    time.sleep(2)
    data_item = {}
    person = parser_main_page(driver1, line[0])
    i += 1
    if person is None:
        data_item['FULLNAME'] = ""
        data_item['INN'] = line[0]
        data_item['HREF'] = ""
        result = result.append(data_item, ignore_index=True)
        print(f"{line[0]} не найден")
        continue
    data_item['FULLNAME'] = person.text
    data_item['INN'] = line[0]
    data_item['HREF'] = person.get_attribute('href')
    result = result.append(data_item, ignore_index=True)
    print(f"{i},{data_item['FULLNAME']},{data_item['INN']},{data_item['HREF']}")
    if i == 500:
        driver1.quit()
        time.sleep(180)
        i = 0
        driver1.get("https://bankrot.fedresurs.ru/DebtorsSearch.aspx")
        fisic = driver1.find_element_by_id('ctl00_cphBody_rblDebtorType_1')
        fisic.click()


driver1.quit()
result.to_csv('result.csv', index=False, encoding='utf-8-sig')