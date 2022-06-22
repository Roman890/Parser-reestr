from bs4 import BeautifulSoup
import requests as req
import csv
import pandas as pd
import os as os
import time
from fake_useragent import UserAgent #имитация браузера
import logging


# чтение файла по строке
def reader(file_name):
    with open(file_name, encoding='utf-8', errors="ignore") as f:
        reader_data = csv.reader(f, delimiter=',')
        for row in reader_data:
            yield row

script_path = os.getcwd()
os.chdir(script_path + "\\Results")

result = pd.DataFrame(columns=['FULLNAME', 'INN', 'SNILS', 'DOCUMENT', 'MESSAGE', 'DATE'])
txt_reader = reader("all_buf.csv")
first_line = next(txt_reader)

#для добавления прокси (пока не использую)
proxies = {
    'https': '62.210.147.54:3838',
    'http': '62.210.147.54:3838'
}
#логирования записей в файл если отвалится
logging.basicConfig(filename="sample.log", level=logging.INFO)

# парсинг страницы клиента
def parser_person_page(soup):
    inn = soup.find("span", {"id":'ctl00_cphBody_lblINN'}).text  #инн
    snils = soup.find("span", {"id":'ctl00_cphBody_lblSNILS'}).text #снилс
    snils = snils.replace("-","")
    snils = snils.replace(" ", "")
    find_urls = []  #массив для сообщений реализован только для главной страницы, иначе если будем смотреть все, то будет еще дольше
    table_message = soup.find("table", {"id":'ctl00_cphBody_gvMessages'})
    messages = table_message.find_all("a", {"title": "Просмотр сообщения"})
    for message in messages:
        url = message['href']
        find_urls.append(url)
    return inn, snils, find_urls

i = 0
#читаем адреса страниц клиентов из файла
for line in txt_reader:
    i += 1
    flag = True
    if(line[2] == ""):
        continue
    resp = req.post(line[2], headers={'User-Agent': UserAgent().chrome})#, proxies=proxies)
    soup = BeautifulSoup(resp.text, 'lxml')
    time.sleep(2)
    inn, snils, messages = parser_person_page(soup)
    #print(messages)
    for item in messages: #пороходим по каждому сообщению
        data_item = {}
        time.sleep(2)
        resp = req.post("https://bankrot.fedresurs.ru"+item, headers={'User-Agent': UserAgent().chrome})#, proxies=proxies)
        soup = BeautifulSoup(resp.text, 'lxml')
        try:
            tables = soup.find_all('table', {"class":'headInfo'}) # поиск всех таблиц на странице сообщения
            important_message = tables[0].select_one(".even")
            ff = important_message.select('td')[1]  # необходимое сообщение
            if ('о признании гражданина банкротом и введении реализации имущества гражданина' in ff.text) or ('о завершении реализации имущества гражданина' in ff.text):
                # если в описании сообщения есть шаблон, то находим дату и номер дела
                important_date = tables[0].select('tr')[-1] # необходимая дата
                date = important_date.select('td')[1].text
                date = date.strip()
                important_doc = tables[1].select('tr')[-1] # необходимый номер дела
                doc = important_doc.select('td')[1].text
                # заполняем словарь с данными
                data_item['FULLNAME'] = line[0]
                data_item['INN'] = inn
                data_item['SNILS'] = snils
                data_item['DOCUMENT'] = doc
                data_item['MESSAGE'] = ff.text
                data_item['DATE'] = date
                flag = False
                result = result.append(data_item, ignore_index=True)
                print(f"{data_item['FULLNAME']},{data_item['INN']},{data_item['SNILS']},{data_item['DOCUMENT']},{data_item['MESSAGE']},{data_item['DATE']}")
                logging.info(f"{data_item['FULLNAME']},{data_item['INN']},{data_item['SNILS']},{data_item['DOCUMENT']},{data_item['MESSAGE']},{data_item['DATE']}")
        except:
            continue
    if flag:
        data_item_empty = {}
        data_item_empty['FULLNAME'] = line[0]
        data_item_empty['INN'] = inn
        data_item_empty['SNILS'] = snils
        data_item_empty['DOCUMENT'] = ""
        data_item_empty['MESSAGE'] = ""
        data_item_empty['DATE'] = ""
        result = result.append(data_item_empty, ignore_index=True)
        print(f"{data_item_empty['FULLNAME']},{data_item_empty['INN']},{data_item_empty['SNILS']},{data_item_empty['DOCUMENT']},{data_item_empty['MESSAGE']},{data_item_empty['DATE']}")
        logging.info(f"{data_item_empty['FULLNAME']},{data_item_empty['INN']},{data_item_empty['SNILS']},{data_item_empty['DOCUMENT']},{data_item_empty['MESSAGE']},{data_item_empty['DATE']}")

    if i == 100:
        time.sleep(60)
        i = 0
		
# записываем датафрейм в файл
result.to_csv('result.csv', index=False, encoding='utf-8-sig')
