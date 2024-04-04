# -*- coding: utf-8 -*-
"""
Created on Thu Sep 22 13:56:11 2022

@author: pengyifeng
"""
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.chrome.options import Options
import json


def Page_data_from_Stock(stock, x, y):
    PageData_Dict = {'view_num': [], 'comment_num': [], 'title': [],
                     'poster': [], 'latest_time': [], 'sub_url': []}
    href_list = []
    print("爬虫启动，爬取范围从第{}页到第{}页".format(x, y - 1))
    for i in range(x, y):
        print('正在第{}页'.format(i))
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        browser = webdriver.Chrome(options=chrome_options)

        url = 'http://guba.eastmoney.com/list,{}_{}.html'.format(stock, i)
        url2 = 'http://guba.eastmoney.com'
        browser.get(url)

        html_source = browser.page_source
        soup = BeautifulSoup(html_source, "html.parser")
        view_num = soup.find_all('span', class_='l1 a1')
        comment_num = soup.find_all('span', class_='l2 a2')
        title = soup.find_all('span', class_='l3 a3')
        poster = soup.find_all('span', class_='l4 a4')
        time = soup.find_all('span', class_='l5 a5')
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
        for element in time[1:]:
            PageData_Dict['latest_time'].append(element.text)
        for i in range(len(time[1:])):
            if (href_list[i][:5] == '/news') and href_list[i][7].isdigit():
                sub_url = url2 + href_list[i]
            else:
                sub_url = ''
            PageData_Dict['sub_url'].append(sub_url)
        browser.close()
    print('结束爬虫')
    total_list = [PageData_Dict['view_num'], PageData_Dict['comment_num'], PageData_Dict['title'],
                  PageData_Dict['poster'],
                  PageData_Dict['latest_time'], PageData_Dict['sub_url']]
    df = pd.DataFrame(total_list)
    df = df.T
    df.columns = ['view_num', 'comment_num', 'title', 'poster', 'latest_time', 'sub_url']
    return df, PageData_Dict


def get_comment(sub_url):
    comment_list = []
    comment_time_list = []
    sub_comment_list = []
    sub_comment_time_list = []
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    browser = webdriver.Chrome(options=chrome_options)

    browser.get(sub_url)
    html_source = browser.page_source
    soup = BeautifulSoup(html_source, "html.parser")

    post_time = soup.find('div', class_="zwfbtime")
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
    browser.close()

    if page_num > 1:
        for i in range(2, page_num + 1):

            print('爬取第{}页'.format(i))
            new_url = sub_url[:-5] + '_{}'.format(i) + sub_url[-5:]
            browser = webdriver.Chrome(options=chrome_options)
            browser.get(new_url)
            html_source = browser.page_source
            soup = BeautifulSoup(html_source, "html.parser")

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

            browser.close()
    return article, article_like, comment_list, comment_time_list, sub_comment_list, sub_comment_time_list


if __name__ == '__main__':

    df, PageData_Dict = Page_data_from_Stock(600000, 2, 3)
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
    Commend_DF.to_csv("./All_Commend.csv")

    All_Commend_JSON = json.dumps(All_Commend_Dict, sort_keys=False, indent=4, separators=(',', ': '))
    print(type(All_Commend_JSON))
    f = open('All_Commend.json', 'w')
    f.write(All_Commend_JSON)
