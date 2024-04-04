from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.chrome.options import Options
import requests
from lxml import etree
import json
import time
import random


def getHtml(url):  # 下载网页源代码
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.42'
    }
    try:
        r = requests.get(url, headers=header)
        r.encoding = 'utf-8'
        # print(r.status_code)
        r.raise_for_status()
        return r.text
    except:
        getHtml(url)


comment_list = []
comment_time_list = []
sub_comment_list = []
sub_comment_time_list = []

sub_url = "http://guba.eastmoney.com/news,600000,1230202660.html"

Chrome_options = webdriver.ChromeOptions()
prefs = { "profile.managed_default_content_settings.images": 2 }    # 不加载图片
Chrome_options.add_experimental_option("prefs", prefs)
Chrome_options.add_argument('--headless')   # 不打开实体浏览器
browser = webdriver.Chrome(options = Chrome_options)
browser.get(sub_url)
html_source = browser.page_source
soup = BeautifulSoup(html_source, "html.parser")
# 别忘了下面加一句browser.close()
print("开始抓取评论页面：{}".format(sub_url))
prepare_time = time.perf_counter()

html_source = getHtml(sub_url)
soup = BeautifulSoup(html_source, "html.parser")

print(f"爬虫准备花了：{time.perf_counter() - prepare_time:0.4f} seconds/n")

print("正在爬取该帖各页面数据")
# soup_start_time = time.perf_counter()
# post_time = soup.find('div', class_="zwfbtime")
article = soup.find('div', class_="stockcodec .xeditor").text
article_like = soup.find_all('div', id='like_wrap')[0]['data-like_count']
comment = soup.find_all('div', class_='full_text')
comment_time = soup.find_all('div', class_='publish_time')
sub_comment = soup.find_all('span', class_="l2_full_text")
sub_comment_time = soup.find_all('span', class_='time fl')
