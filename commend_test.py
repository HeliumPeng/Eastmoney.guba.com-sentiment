# -*- coding: utf-8 -*-
"""
Created on Thu Sep 23 13:56:11 2022

@author: pengyifeng

2022年9月26日22:56:38 目前存在的问题，只能爬取个股的页面，热门主题吧的暂时不行，无法获取到sub_url
"""
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.chrome.options import Options
import json
import requests
import time
from lxml import etree
import random


def Page_data_from_Stock(stock, x, y):  # 此函数是爬取指定的股票页面，stock为股票前缀，爬取x~y-1页的内容
    PageData_Dict = {'view_num': [], 'comment_num': [], 'title': [],
                     'poster': [], 'latest_time': [], 'sub_url': []}
    href_list = []
    print("爬虫启动，爬取范围从第{}页到第{}页".format(x, y - 1))

    for i in range(x, y):   # 爬取股票页面不需要使用selenium模拟浏览器，直接requests.get就可以返回真实的数据，这样可以更快
        prepare_time = time.perf_counter()

        print("正在第{}页".format(2))
        url = 'http://guba.eastmoney.com/list,{}_{}.html'.format(stock, 2)
        url2 = 'http://guba.eastmoney.com'
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.42"
        }
        time.sleep(random.random() * 2)
        response = requests.get(url=url, headers=headers)
        html_source = etree.HTML(response.content.decode("utf-8"))
        html_source = etree.tostring(html_source)
        print(f"爬虫准备花了：{time.perf_counter() - prepare_time:0.4f} seconds/n")
        '''
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        browser = webdriver.Chrome(options=chrome_options)
        browser.get(url)
        html_source = browser.page_source
        soup = BeautifulSoup(html_source1, "html.parser")                
        '''
        print("正在爬取网址{}".format(url))
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
        for i in range(len(latest_post_time[1:])):
            if (href_list[i][:5] == '/news') and href_list[i][7].isdigit():
                sub_url = url2 + href_list[i]
            else:
                sub_url = ''
            PageData_Dict['sub_url'].append(sub_url)
        # browser.close()
        print(f"此页面爬取时间为：{time.perf_counter() - soup_start_time:0.4f} seconds/n")
    print("结束爬虫")
    ''' 如果需要的话，可以将数据保存为df然后返回，注释代码的内容也是保存为df
    total_list = [PageData_Dict['view_num'], PageData_Dict['comment_num'], PageData_Dict['title'],
                  PageData_Dict['poster'],
                  PageData_Dict['latest_time'], PageData_Dict['sub_url']]
    df = pd.DataFrame(total_list)
    df = df.T
    df.columns = ['view_num', 'comment_num', 'title', 'poster', 'latest_time', 'sub_url']
    return df, PageData_Dict    
    '''
    return PageData_Dict


def get_comment(sub_url):
    comment_list = []
    comment_time_list = []
    sub_comment_list = []
    sub_comment_time_list = []

    print("开始抓取评论页面：{}".format(sub_url))
    prepare_time = time.perf_counter()
    ''' 直接request是不行的，会返回不完全的界面（股吧更新的反扒措施），要使用selenium模拟浏览器去访问页面，这样确实会很慢
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.42"
    }
    time.sleep(random.random() * 2)
    response = requests.get(url=sub_url, headers=headers)
    html_source = etree.HTML(response.content.decode("utf-8"))
    html_source = etree.tostring(html_source)
    soup = BeautifulSoup(html_source, "html.parser")
    '''
    Chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}  # 不加载图片
    Chrome_options.add_experimental_option("prefs", prefs)
    Chrome_options.add_argument('--headless')  # 不打开实体浏览器
    browser = webdriver.Chrome(options=Chrome_options)
    browser.get(sub_url)
    html_source = browser.page_source
    soup = BeautifulSoup(html_source, "html.parser")

    print(f"爬虫准备花了：{time.perf_counter() - prepare_time:0.4f} seconds\n")

    print("正在爬取该帖各页面数据")
    soup_start_time = time.perf_counter()
    # post_time = soup.find('div', class_="zwfbtime")
    article = soup.find('div', class_="stockcodec .xeditor").text
    article_like = soup.find_all('span', id='like_wrap')[0].text
    comment = soup.find_all('div', class_='full_text')
    comment_time = soup.find_all('div', class_='publish_time')
    sub_comment = soup.find_all('span', class_="l2_full_text")
    sub_comment_time = soup.find_all('span', class_='time fl')

    page_num = soup.find_all('span', class_='sumpage')
    if len(page_num) == 0:
        page_num = 1
    else:
        page_num = int(page_num[0].text)

    print('本贴共{}页:'.format(page_num))
    for element in comment:
        comment_list.append(element.text)
    for element in comment_time:
        comment_time_list.append(element.text)
    for element in sub_comment:
        sub_comment_list.append(element.text)
    for element in sub_comment_time:
        sub_comment_time_list.append(element.text)
    print('爬取第1页')
    print(f"第1页爬取花费时间为：{time.perf_counter() - soup_start_time:0.4f} seconds/n")
    browser.close()


    if page_num > 1:
        for i in range(2, page_num + 1):
            print('爬取第{}页'.format(i))
            Page_start_time = time.perf_counter()
            new_url = sub_url[:-5] + '_{}'.format(i) + sub_url[-5:]
            browser = webdriver.Chrome(options=Chrome_options)
            browser.get(new_url)
            html_source = browser.page_source
            soup = BeautifulSoup(html_source, "html.parser")
            ''' 和上面一个道理，直接requests.get会返回不完全的页面
            time.sleep(random.random() * 2)
            response = requests.get(url=new_url, headers=headers)
            html_source = etree.HTML(response.content.decode("utf-8"))
            html_source = etree.tostring(html_source)
            soup = BeautifulSoup(html_source, "html.parser")
            '''
            comment = soup.find_all('div', class_='full_text')
            comment_time = soup.find_all('div', class_='publish_time')[4:]
            sub_comment = soup.find_all('span', class_="l2_full_text")
            sub_comment_time = soup.find_all('span', class_='time fl')[4:]

            for element in comment:
                comment_list.append(element.text)
            for element in comment_time:
                comment_time_list.append(element.text)
            for element in sub_comment:
                sub_comment_list.append(element.text)
            for element in sub_comment_time:
                sub_comment_time_list.append(element.text)

            print(f"第{format(i)}页爬取花费时间为：{time.perf_counter() - Page_start_time:0.4f} seconds/n")
            browser.close()
    return article, article_like, comment_list, comment_time_list, sub_comment_list, sub_comment_time_list


if __name__ == '__main__':

    PageData_Dict = Page_data_from_Stock('600000', 1, 2)  # 600000, 2, 3这里演示的是浦发银行吧的第二页内容
    All_Commend_Dict = {'article': [], 'article_like': [], 'comment': [],
                        'comment_time': [], 'sub_comment': [], 'sub_comment_time': []}

    for url in PageData_Dict['sub_url']:
        if url != '':
            article, article_like, comment_list, comment_time_list, sub_comment_list, sub_comment_time_list = get_comment(url)

            All_Commend_Dict['article'].append(article)
            All_Commend_Dict['article_like'].append(article_like)
            All_Commend_Dict['comment'].append(comment_list)
            All_Commend_Dict['comment_time'].append(comment_time_list)
            All_Commend_Dict['sub_comment'].append(sub_comment_list)
            All_Commend_Dict['sub_comment_time'].append(sub_comment_time_list)

    Commend_List = [All_Commend_Dict['article'], All_Commend_Dict['article_like'],
                    All_Commend_Dict['comment'], All_Commend_Dict['comment_time'],
                    All_Commend_Dict['sub_comment'], All_Commend_Dict['sub_comment_time']]

    Commend_DF = pd.DataFrame(Commend_List)
    Commend_DF = Commend_DF.T
    Commend_DF.columns = ['article', 'article_like', 'comment', 'comment_time', 'sub_comment', 'sub_comment_time']
    Commend_DF.to_csv("./All_Commend.csv", encoding="utf-8")    # 别直接用excel打开啊，会乱码的，注意编码格式

    All_Commend_JSON = json.dumps(All_Commend_Dict, sort_keys=False, indent=4, separators=(',', ': '))
    print(type(All_Commend_JSON))
    f = open('All_Commend.json', 'w')
    f.write(All_Commend_JSON)
# //div[@class="zwlist"]/div[3]/div[1]/div[5]/div[2]/div[3]/a[1]
# 