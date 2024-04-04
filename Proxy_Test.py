# 2022年10月26日22:36:14

import requests


def get_proxy():
    return requests.get("http://127.0.0.1:5010/get/").json()


def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))

def getHtml():
    retry_count = 5
    proxy = get_proxy().get("proxy")
    print(proxy)
    while retry_count > 0:
        try:
            html = requests.get('http://www.baidu.com', proxies={"http": "http://{}".format(proxy)})
            print(html.text)
            break
        except Exception:
            retry_count -= 1
    # 删除代理池中代理
    delete_proxy(proxy)
    return None

getHtml()

from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.chrome.options import Options
from lxml import etree
import json
import time
import random
stock = 600000
i = 1

PageData_Dict = {'view_num': [], 'comment_num': [], 'title': [],
                 'poster': [], 'latest_time': [], 'sub_url': []}
href_list = []
total_list = []

url = 'http://guba.eastmoney.com/list,{}_{}.html'.format(stock, i)
url2 = 'http://guba.eastmoney.com'
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.42"
}
proxy = get_proxy().get("proxy")
print(proxy)

response = requests.get(url=url, headers=headers, proxies={"http": "http://{}".format(proxy)})

html_source = etree.HTML(response.content.decode("utf-8"))
html_source = etree.tostring(html_source)  # 如果用bs4的方法，就需要这一步

soup_start_time = time.perf_counter()
soup = BeautifulSoup(html_source, "html.parser")
view_num = soup.find_all('span', class_='l1 a1')
comment_num = soup.find_all('span', class_='l2 a2')
title = soup.find_all('span', class_='l3 a3')
poster = soup.find_all('span', class_='l4 a4')
latest_post_time = soup.find_all('span', class_='l5 a5')
for element in view_num[1:]:
    PageData_Dict['view_num'].append(element.string)
for element in comment_num[1:]:
    PageData_Dict['comment_num'].append(element.text)
for element in title[1:]:
    a = element.find('a')
    href = a.get('href')
    title = a.get('title')
    href_list.append(href)
    PageData_Dict['title'].append(title)
for element in poster[1:]:
    PageData_Dict['poster'].append(element.text)
for element in latest_post_time[1:]:
    PageData_Dict['latest_time'].append(element.text)
for j in range(len(latest_post_time[1:])):
    if (href_list[j][:5] == '/news') and href_list[j][7].isdigit():
        sub_url = url2 + href_list[j]
    else:
        sub_url = ''
    PageData_Dict['sub_url'].append(sub_url)

response = requests.get(url=url, headers=headers, proxies={"http": "http://115.236.166.106:9091"})


