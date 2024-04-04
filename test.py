from bs4 import BeautifulSoup
import pandas as pd
import requests
from lxml import etree
import json
import time
import random
import math
import datetime


def get_proxy():
    return requests.get("http://127.0.0.1:5010/get/").json()


def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))


def getHtml(URL, headers):
    retry_count = 3
    proxy = get_proxy().get("proxy")
    while retry_count > 0:
        try:
            # 使用代理访问
            print("使用{}尝试第{}次get".format(proxy, 4-retry_count))
            html = requests.get(url=URL, headers=headers, proxies={"http": "http://{}".format(proxy)}, timeout=2)
            return html
        except Exception:
            print("get {}出现异常，重试{}次".format(URL, 4-retry_count))
            retry_count -= 1
            # time.sleep(0.4)
            # 删除代理池中代理
            # delete_proxy(proxy)
    return None


def IDtoName(stock):
    Raw_Table = pd.read_csv("科创板列表-重新采集-ID&Name_Doing.csv")
    index = Raw_Table[Raw_Table['code'] == stock].index.tolist()[0]
    return Raw_Table['name'][index]


def getTotalPage(stock):
    URL = 'http://guba.eastmoney.com/list,{}_1.html'.format(stock)
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.42"
    }
    Stock_Name = IDtoName(stock) + '吧'

    Response = requests.get(url=URL, headers=headers,
                            timeout=3)  # 或许有疑问为什么不用我写的getHtml方法，因为本机ip用的很不频繁，得到TotalPage要避免代理失效返回None
    if Response is None:
        while (Response is None) or Response.status_code !=200:
            Response = getHtml(URL, headers)
            time.sleep(0.5)
    else:
        HTML_OBJ = etree.HTML(Response.content.decode("utf-8"))
        Current_Name = HTML_OBJ.xpath("//span[@id='stockname']/a/text()")  # 这个是提取页面当前吧的名字然后和股票对应真正的贴吧进行对比
        if not Current_Name:
            print("当前页面获取的贴吧名字为空，重新获取")
        else:
            Current_Name = str(Current_Name[0])

        retry = 1
        while Current_Name != Stock_Name:
            print("在获取当前股吧{}({})的全部页数时遭遇反爬虫，获取到({})的信息，未获取有效页面，重试第{}次".format(Stock_Name, stock, Current_Name, retry))
            retry += 1
            Response = getHtml(URL, headers)
            if Response is not None:
                HTML_OBJ = etree.HTML(Response.content.decode("utf-8"))
                Current_Name = HTML_OBJ.xpath("//span[@id='stockname']/a/text()")
                if not Current_Name:
                    print("当前页面获取的贴吧名字为空，重新获取")
                    continue
                else:
                    Current_Name = str(Current_Name[0])
            else:
                continue

    HTML_OBJ = etree.HTML(Response.content.decode("utf-8"))

    Page_Data = HTML_OBJ.xpath("//span[@class='pagernums']")
    Page_Data = Page_Data[0].__getattribute__('attrib')
    Page_Data = Page_Data['data-pager']

    if Page_Data:
        Page_Num = Page_Data.split("|")
        Total_Page = math.ceil(int(Page_Num[1]) / int(Page_Num[2]))
    else:
        Total_Page = 1

    return Total_Page


# 用来得到当前吧的名字（把名字取出来作为Meta Data，之后每一个页面取数据的时候都要去对比Meta Data，看看是不是请求到反扒页面了）
def getMeta(stock):
    Meta_URL = 'http://guba.eastmoney.com/list,{}_1.html'.format(stock)
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.42"
    }
    Meta_Response = requests.get(url=Meta_URL, headers=headers, timeout=2)
    HTML_OBJ = etree.HTML(Meta_Response.content.decode("utf-8"))
    Meta_Name = HTML_OBJ.xpath("//span[@id='stockname']/a/text()")  # 这个是提取当前吧的名字，比如：贵州茅台吧

    if len(Meta_Name) == 0:  # 说明当前ip很可能被封了，requests.get返回的数据是空的
        print("未获取当前股吧{}的元数据信息，尝试使用其他代理IP访问".format(stock))
        while len(Meta_Name) == 0:
            try:
                proxy = get_proxy().get("proxy")
                print(proxy)
                Meta_Response = requests.get(url=Meta_URL, headers=headers, proxies={"http": "http://{}".format(proxy)},
                                             timeout=2)
                HTML_OBJ = etree.HTML(Meta_Response.content.decode("utf-8"))
                Meta_Name = HTML_OBJ.xpath("//span[@id='stockname']/a/text()")

            except Exception:  # 如果代理IP行不通就用本机IP试试，一般来说本机ip的调用很不频繁，大概率不会被封
                Meta_Response = requests.get(url=Meta_URL, headers=headers)
                HTML_OBJ = etree.HTML(Meta_Response.content.decode("utf-8"))
                Meta_Name = HTML_OBJ.xpath("//span[@id='stockname']/a/text()")

    return Meta_Name


def Spider(stock):
    start_time = time.perf_counter()
    PageData_Dict = {'view_num': [], 'comment_num': [], 'sub_url': [],
                     'poster': [], 'latest_time': [], 'title': []}
    href_list = []

    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.42"
    }

    Total_page = getTotalPage(stock)
    # Stock_Name = getMeta(stock)
    Stock_Name = IDtoName(stock) + '吧'

    Page_Count = 0
    print("爬虫启动，爬取范围从第1页到第{}页".format(Total_page - 1))

    for i in range(1, Total_page - 1):
        prepare_time = time.perf_counter()

        print("正在第{}页，还有{}页".format(i, Total_page - i))
        url = 'http://guba.eastmoney.com/list,{}_{}.html'.format(stock, i)
        base_url = 'http://guba.eastmoney.com'

        response = getHtml(url, headers)

        if response is None:
            print("初次获取该页面信息失败，开始重试")
            Current_Name = ""
            retry = 10
            while (response is None) and (Current_Name != Stock_Name):
                if retry <= 0:
                    break

                print("Use another Proxy to Retry")
                response = getHtml(url, headers)
                if response is not None:
                    if response.status_code != 200:
                        print("response statue code:", response.status_code, " retry")
                        continue
                    HTML_OBJ = etree.HTML(response.content.decode("utf-8", "ignore"))
                    Current_Name = HTML_OBJ.xpath("//span[@id='stockname']/a/text()")
                    if not Current_Name:
                        print("当前页面获取的贴吧名字为空，重新获取")
                        retry -= 1
                        continue
                    else:
                        Current_Name = str(Current_Name[0])

                    if Current_Name == Stock_Name:
                        break
                retry -= 1
            if response is None:
                print("All Proxy fail, try local IP to get the response")
                response = requests.get(url=url, headers=headers)

        elif response is not None:
            retry = 10
            if response.status_code != 200:
                print("response statue code:", response.status_code, " retry")
                while (response is None) or response.status_code != 200:
                    response = getHtml(url, headers)
                    print("response非空但返回404，重新获取")

            HTML_OBJ = etree.HTML(response.content.decode("utf-8", "ignore"))
            # print("1HTML_OBJ type:", type(HTML_OBJ), "response statue code:", response.status_code)
            Current_Name = HTML_OBJ.xpath("//span[@id='stockname']/a/text()")
            if not Current_Name:
                print("当前页面获取的贴吧名字为空，重新获取")
            else:
                Current_Name = str(Current_Name[0])

            while (Current_Name != Stock_Name) and (retry > 0):
                print("可能遭遇反爬虫机制，当前页面{}信息错误，要获取的是{}，目前获取的是{}，重试第{}次".format(url, Stock_Name, Current_Name, 11 - retry))
                response = getHtml(url, headers)

                if response is not None:
                    HTML_OBJ = etree.HTML(response.content.decode("utf-8", "ignore"))
                    if response.status_code != 200:
                        print("response statue code:", response.status_code, " retry")
                        continue
                    Current_Name = HTML_OBJ.xpath("//span[@id='stockname']/a/text()")
                    if not Current_Name:
                        print("当前页面获取的贴吧名字为空，重新获取")
                        retry -= 1
                        time.sleep(0.5)
                        continue
                    else:
                        Current_Name = str(Current_Name[0])

                    if Current_Name == Stock_Name:
                        break
                retry -= 1

            if Current_Name != Stock_Name:
                print("所有IP失效，获取的名字是{}，而真实的名字应该是{}, try local IP to get the response".format(Current_Name, Stock_Name))
                response = requests.get(url=url, headers=headers)

        if response is None:  # 最坏的结果是代理全部失效，然后本地采集也失效，或者代理把数据爬下来但是实际上response是none，直接跳过这页就是了
            print("All Proxy fail and local IP banned, skip this page: {}".format(url))
            continue

        HTML_OBJ = etree.HTML(response.content.decode("utf-8", "ignore"))  # 这段代码看着其实没什么必要，但是确实报过错明明有response但是HTML_OBJ是空的
        if response.status_code != 200:
            print("response statue code:", response.status_code, " retry run out and skip this page")
            continue

        Current_Name = HTML_OBJ.xpath("//span[@id='stockname']/a/text()")
        if not Current_Name:
            print("当前页面获取的贴吧名字为空，所有的IP都试过了失败了，跳过这页吧")
            continue
        else:
            Current_Name = str(Current_Name[0])
            print("当前获取的股吧名字为{}，对应的真实名字为{}".format(Current_Name, Stock_Name))

        if Current_Name != Stock_Name:
            print("All Proxy fail and local IP didn't get right name, skip this page: {}".format(url))
            continue

        print(f"爬虫准备花了：{time.perf_counter() - prepare_time:0.4f} seconds/n")
        print("爬取网址{}完毕，开始解析数据".format(url))
        # 下面是xpath解析网址模块，要换bs4的把这么一直到下一次注释的地方全部注释了然后把bs4的取消注释就可以
        Xpath_start_time = time.perf_counter()

        Article_List = HTML_OBJ.xpath("//div[@id='articlelistnew']/div[contains(@class,'articleh')]")

        for article in Article_List:
            if article.xpath("./span[@class='l1 a1']/text()"):
                PageData_Dict['view_num'].append(article.xpath("./span[@class='l1 a1']/text()")[0])
            else:
                PageData_Dict['view_num'].append("")

            if article.xpath("./span[@class='l2 a2']/text()"):
                PageData_Dict['comment_num'].append(article.xpath("./span[@class='l2 a2']/text()")[0])
            else:
                PageData_Dict['comment_num'].append("")

            if article.xpath("./span[@class='l3 a3']/a/@title"):
                PageData_Dict['title'].append(article.xpath("./span[@class='l3 a3']/a/@title")[0])
            else:
                PageData_Dict['title'].append("")

            if article.xpath("./span[@class='l3 a3']/a/@href"):
                if article.xpath("./span[@class='l3 a3']/a/@href")[0][2] == 'c':
                    PageData_Dict['sub_url'].append(article.xpath("./span[@class='l3 a3']/a/@href")[0])
                else:
                    PageData_Dict['sub_url'].append(base_url + article.xpath("./span[@class='l3 a3']/a/@href")[0])
            else:
                PageData_Dict['sub_url'].append("")

            if article.xpath("./span[@class='l4 a4']//text()"):
                PageData_Dict['poster'].append(article.xpath("./span[@class='l4 a4']//text()")[0])
            else:
                PageData_Dict['poster'].append("")

            if article.xpath("./span[@class='l5 a5']/text()"):
                PageData_Dict['latest_time'].append(article.xpath("./span[@class='l5 a5']/text()")[0])
            else:
                PageData_Dict['latest_time'].append("")

        print(f"此页面解析时间为：{time.perf_counter() - Xpath_start_time:0.4f} seconds/n")
        Page_Count += 1

        # 下面的是BeautifulSoup的方法，这个方法没有问题，逻辑上还更方便理解一些，只是不够快，然后提取url的过程多少有些繁琐
        # soup_start_time = time.perf_counter()
        # HTML_OBJ = etree.tostring(HTML_OBJ)  # 如果用bs4的方法，就需要这一步
        # soup = BeautifulSoup(HTML_OBJ, "html.parser")
        # view_num = soup.find_all('span', class_='l1 a1')
        # comment_num = soup.find_all('span', class_='l2 a2')
        # title = soup.find_all('span', class_='l3 a3')
        # poster = soup.find_all('span', class_='l4 a4')
        # latest_post_time = soup.find_all('span', class_='l5 a5')
        # for element in view_num[1:]:
        #     PageData_Dict['view_num'].append(element.string)
        # for element in comment_num[1:]:
        #     PageData_Dict['comment_num'].append(element.text)
        # for element in title[1:]:
        #     a = element.find('a')
        #     href = a.get('href')
        #     title = a.get('title')
        #     href_list.append(href)
        #     PageData_Dict['title'].append(title)
        # for element in poster[1:]:
        #     PageData_Dict['poster'].append(element.text)
        # for element in latest_post_time[1:]:
        #     PageData_Dict['latest_time'].append(element.text)
        # for j in range(len(latest_post_time[1:])):
        #     if (href_list[j][:5] == '/news') and href_list[j][7].isdigit():
        #         sub_url = base_url + href_list[j]
        #     else:
        #         sub_url = ''
        #     PageData_Dict['sub_url'].append(sub_url)
        #
        # print(f"此页面爬取时间为：{time.perf_counter() - soup_start_time:0.4f} seconds/n")

    print('结束爬虫')
    Time_Cost = time.perf_counter() - start_time
    print(f"整个网页爬取时间为：{Time_Cost:0.4f} seconds/n")

    Commend_List = [PageData_Dict['view_num'], PageData_Dict['comment_num'], PageData_Dict['sub_url'],
                    PageData_Dict['title'], PageData_Dict['poster'], PageData_Dict['latest_time']]
    Commend_DF = pd.DataFrame(Commend_List)
    Commend_DF = Commend_DF.T
    Commend_DF.columns = ['view_num', 'comment_num', 'sub_url', 'title', 'poster', 'latest_time']

    return Commend_DF, Time_Cost, Total_page, Page_Count


# 这个函数是用来把字符拼起来返回一个数字的，比如'0'和'1'拼起来就是1；'1'和'2'就是12
# def NumberCombine(char_x, char_y):
#     number_str = char_x + char_y
#     return int(number_str)


# 这个个函数的运行有个前提，前后两篇帖子的发帖时间不能相差半年以上（一般来说再冷门的贴吧也不至于半年没一篇吧）
# def GetRightTime(DF):
#     DF_temp = DF.copy()
#     DF_temp = DF_temp.dropna(subset=['sub_url'])
#     Raw_Time = DF_temp['latest_time']
#     Raw_Time = Raw_Time.tolist()
#     year = 2022
#     New_Time_List = []
#     for i in range(0, len(Raw_Time)):
#         temp = year.__str__() + '-' + Raw_Time[i]
#         New_Time_List.append(temp)
#         if (i != len(Raw_Time) - 1) and  \
#                 ((NumberCombine(Raw_Time[i+1][0], Raw_Time[i+1][1]) - NumberCombine(Raw_Time[i][0], Raw_Time[i][1])) > 6):
#             year -= 1
#
#         if (i != len(Raw_Time) - 1) and \
#                 ((NumberCombine(Raw_Time[i][0], Raw_Time[i][1]) - NumberCombine(Raw_Time[i+1][0], Raw_Time[i+1][1])) > 6):
#             year += 1
#
#     DF_temp['latest_time'] = pd.to_datetime(New_Time_List)
#     return DF_temp


if __name__ == '__main__':
    Market_DF = pd.read_csv("科创板列表-重新采集-ID&Name_Doing.csv")
    Market_List = []
    for i in Market_DF['code']:
        Market_List.append(i)

    # count = Market_List.__len__()

    for j in Market_List:
        Commend_DF, Time_Cost, Total_Page, Page_Count = Spider(j)
        Commend_DF_temp = Commend_DF.copy()
        # Commend_DF_temp = GetRightTime(Commend_DF)

        # Meta_Name = getMeta(j)
        # Meta_Name = str(Meta_Name[0])
        Meta_Name = IDtoName(j) + '吧'

        Meta_Name = Meta_Name.replace('*', '+')  # 这一步为了防止一些*开头的股票无法保存为名字的问题，把*换成+，后期再处理
        Commend_DF_temp.to_csv("KeChuang_Market_12.12/{}.csv".format(Meta_Name), index=False, encoding='utf-8-sig')
        Market_List.remove(j)
        # Market_DF = pd.DataFrame(Market_List)

        Market_DF.drop(index=Market_DF.loc[Market_DF['code'] == j].index, inplace=True)
        Market_DF.to_csv("科创板列表-重新采集-ID&Name_Doing.csv", index=False,
                                header=["code", "name"], encoding='utf-8-sig')  # 不保留索引避免多一列索引数据影响运行，然后指定保留列名字为code为了复用代码
        with open("科创板记录.txt", 'a') as f:  # 写个文件记录一下运行的时间数据
            f.write("股吧{}({})数据收集完毕, 共有{}页，爬取了{}页，花费时间{}\n".format(Meta_Name, j, Total_Page, Page_Count, Time_Cost))
            f.close()
