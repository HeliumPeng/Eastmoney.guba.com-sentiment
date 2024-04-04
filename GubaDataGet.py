# -*- coding: utf-8 -*-
"""
Created on Wed Sep 21 17:10:53 2022

@author: pengyifeng
"""
import requests
import re
import time
import random
from lxml import etree



class Spider:
    def __init__(self):
        self.base_url = "http://guba.eastmoney.com/"
        # self.start_url = "http://guba.eastmoney.com/default,99_1.html"
        self.start_url = "http://guba.eastmoney.com/list,600000_1.html"
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
        }
        self.items = []
        self.index = 1

    def get_content(self, url):
        """获取url对应的内容"""
        time.sleep(random.random()*3)
        response = requests.get(url=url, headers=self.headers)
        return response.content.decode("utf-8")

    def parse_html(self, html):
        """解析html获取数据"""
        # 解析html
        html_obj = etree.HTML(html)
        # 使用xpath语法提取
        # //div[@id='articlelistnew']/div[@class='articleh normal_post'] | //div[@id='articlelistnew']/div[@class='articleh normal_post odd']
        li_list = html_obj.xpath("//div[@id='articlelistnew']")
        # 循环
        for li in li_list:
            print(self.index)
            item = {}
            item["read"] = li.xpath(".//span[@class='l1 a1']/text()")[0].strip()
            item["comment"] = li.xpath(".//span[@class='l2 a2']/text()")[0].strip()
            # item["name"] = li.xpath(".//span[@class='l4 a4']")[0]
            item["title"] = li.xpath(".//span[@class='l3 a3']/a/@title")[0]
            item["url"] = li.xpath(".//span[@class='l3 a3']/a/@href")[0]
            '''
            if li.xpath("./span/a[2]"):
                item["title"] = li.xpath("./span/a[2]/text()")[0]
            else:
                item["title"] = ""
            if li.xpath("./span/a[2]/@href"):
                item["url"] = self.base_url + li.xpath("./span/a[2]/@href")[0]
            else:
                item["url"] = ""                            
            '''

            # 这个code没有写完，xpath路经还有问题
            item["author"] = li.xpath(".//span[@class='l4 a4']/a")[0]
            item["date"] = li.xpath(".//span[@class='l5 a5']")[0].strip()
            self.items.append(item)
            self.index += 1

        #提取下一页
        next_url = html_obj.xpath('//a[contains(text(),"下一页")]/@href')
        if next_url:
            next_url = self.base_url + next_url[0]
            html = self.get_content(next_url)
            self.parse_html(html)

    def save(self):
        """保存"""
        with open("./浦发.txt", "a", encoding="utf-8") as file:
            for item in self.items:
                file.write(",".join(item.values()))
                file.write("\n")

    def start(self):
        print("爬虫开始...")
        self.parse_html(self.get_content(self.start_url))
        print("爬虫结束...")
        print("保存开始...")
        self.save()
        print("保存结束...")


if __name__ == '__main__':
    Spider().start()




