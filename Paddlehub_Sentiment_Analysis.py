from typing import Iterable

import numpy as np
import pandas as pd
from glob import iglob
import os
import scipy.stats as stats
import paddlehub as hub


os.environ["CUDA_VISIBLE_DEVICES"] = '0'

# 这个函数是用来把字符拼起来返回一个数字的，比如'0'和'1'拼起来就是1；'1'和'2'就是12
def NumberCombine(char_x, char_y):
    number_str = char_x + char_y
    return int(number_str)

# 中间可能会有一些时间紊乱的数据，默认极少数不影响整体
def GetRightTime(DF):
    DF_temp = DF.copy()
    DF_temp = DF_temp.dropna(subset=['sub_url'])

    Raw_Time = DF_temp['latest_time'].fillna(method='ffill')
    # Raw_Time = Raw_Time.__str__()
    Raw_Time = Raw_Time.tolist()
    year = 2022
    New_Time_List = []
    for i in range(0, len(Raw_Time)):
        temp = year.__str__() + '-' + Raw_Time[i]
        New_Time_List.append(temp)
        if (i != len(Raw_Time) - 1) and  \
                ((NumberCombine(Raw_Time[i+1][0], Raw_Time[i+1][1]) - NumberCombine(Raw_Time[i][0], Raw_Time[i][1])) > 10):
            year -= 1   # 从1月到12月算是跨年了

        if (i != len(Raw_Time) - 1) and \
                ((NumberCombine(Raw_Time[i][0], Raw_Time[i][1]) - NumberCombine(Raw_Time[i+1][0], Raw_Time[i+1][1])) > 10):
            year += 1

    # DF_temp['latest_time'] = pd.to_datetime(New_Time_List)
    DF_temp['latest_time'] = New_Time_List
    return DF_temp
# 判断两个时间戳是否是同一天
def WhetherSameDate(Date1, Date2):  #输入应该是Timestamp类型的数据
    if(Date1.year == Date2.year) & (Date1.month == Date2.month) & (Date1.day == Date2.day):
        return True
    else:
        return False

def HalfSeries(s, n):
    '''
    if length(X) is odd:
        X <- {(X1 + X2) / 2, ..., (Xn-2 + Xn-1) / 2, Xn}
        n <- (n - 1) / 2
    else:
        X <- {(X1 + X2) / 2, ..., (Xn-1 + Xn) / 2}
        n <- n / 2
    return X, n
    '''
    X = []
    for i in range(0, len(s) - 1, 2):
        X.append((s[i] + s[i + 1]) / 2)
    # if length(s) is odd
    if len(s) % 2 != 0:
        X.append(s[-1])
        n = (n - 1) // 2
    else:
        n = n // 2
    return [np.array(X), n]

def Hurst(ts):
    '''
    Parameters
    ----------
    ts : Iterable Object.
        A time series or a list.

    Raises
    ------
    ValueError
        If input ts is not iterable then raise error.

    Returns
    -------
    H : Float
        The Hurst-index of this series.
    '''
    if not isinstance(ts, Iterable):
        raise ValueError("This sequence is not iterable !")
    ts = np.array(ts)
    # N is use for storge the length sequence
    N, RS, n = [], [], len(ts)
    while (True):
        N.append(n)
        # Calculate the average value of the series
        m = np.mean(ts)
        # Construct mean adjustment sequence
        mean_adj = ts - m
        # Construct cumulative deviation sequence
        cumulative_dvi = np.cumsum(mean_adj)
        # Calculate sequence range
        srange = max(cumulative_dvi) - min(cumulative_dvi)
        # Calculate the unbiased standard deviation of this sequence
        unbiased_std_dvi = np.std(ts)
        # Calculate the rescaled range of this sequence under n length
        RS.append(srange / unbiased_std_dvi)
        # While n < 4 then break
        if n < 4:
            break
        # Rebuild this sequence by half length
        ts, n = HalfSeries(ts, n)
    # Get Hurst-index by fit log(RS)~log(n)
    H = np.polyfit(np.log10(N), np.log10(RS), 1)[0]
    return H





path = os.path.join("KeChuang_Market_12.12/*.csv")
Raw_CSV_Files = iglob(path)
senta = hub.Module(name="senta_bilstm")

# 重新将科创板的数据保存一次为utf-8格式
# path = os.path.join("KeChuang_Market/*.csv")
# Raw_CSV_Files = iglob(path)
# count = 1
# for file in Raw_CSV_Files:
#     File_Name = file[16:]
#     Raw_DF = pd.read_csv(file)
#     Raw_DF.to_csv("KeChuang_Market_UTF-8/" + File_Name, index=False, encoding='utf_8_sig')
#     print("{}吧保存完毕，累计保存{}个贴吧".format(File_Name, count))
#     count += 1

for file in Raw_CSV_Files:
    File_Name = file[23:]
    Raw_DF = pd.read_csv(file)
    if Raw_DF.empty:
        continue
    Time_Correct_DF = GetRightTime(Raw_DF)  # 使用函数加年份
    text = []
    for title in Time_Correct_DF['title']:
        text.append(str(title))

    results = senta.sentiment_classify(texts=text, use_gpu=True, batch_size=1)
    print("{}处理完毕。".format(File_Name))
    grades = []
    for result in results:
        grades.append(result['positive_probs'])

    Time_Correct_DF['Sentiment_Grade'] = grades
    # Title_Dict = {'text': [], 'sentiment_label': [], 'sentiment_key': [],
    #               'positive_probs': [], 'negative_probs': []}
    # for result in results:
    #     Title_Dict['text'].append(result['text'])
    #     Title_Dict['sentiment_label'].append(result['sentiment_label'])
    #     Title_Dict['sentiment_key'].append(result['sentiment_key'])
    #     Title_Dict['positive_probs'].append(result['positive_probs'])
    #     Title_Dict['negative_probs'].append(result['negative_probs'])
    #
    # Title_List = [Title_Dict['text'], Title_Dict['sentiment_label'], Title_Dict['sentiment_key'],
    #               Title_Dict['positive_probs'], Title_Dict['negative_probs']]
    # Commend_DF = pd.DataFrame(Title_List)
    # Commend_DF = Commend_DF.T
    # Commend_DF.columns = ['text', 'sentiment_label', 'sentiment_key', 'positive_probs', 'negative_probs']
    folder = "Sentiment_KeChuang12.12/"
    Time_Correct_DF.to_csv(folder + File_Name+"分析结果.csv", index=False, encoding='utf_8_sig')
    os.remove(file)

path = os.path.join("Sentiment_KeChuang/*.csv")
Raw_Sentiment_CSV_Files = iglob(path)
for file in Raw_Sentiment_CSV_Files:
    Guba_Name = file[19:-13]    # 提取的是当前吧的名字（只是名字），例如“贵州茅台”，不是“贵州茅台吧”
    Raw_Sentiment_DF = pd.read_csv(file)
    Raw_Sentiment_DF['Date_Time'] = pd.to_datetime(Raw_Sentiment_DF['latest_time'], format="%Y/%m/%d")  # 暂时忽略具体时间，只统计每一天

# 用于判断日期有没有标错（如果出现非闰年的2月29日肯定就出了问题了）
# 代码未完成！
for file in Raw_Sentiment_CSV_Files:
    Raw_Sentiment_DF = pd.read_csv(file)
    Raw_Sentiment_DF[Raw_Sentiment_DF['latest_time'].str.contains('2021/2/29 | 2019/2/29 | 2018/2/29')]

# 如何给标错的年份加一年
# file = 'Sentiment_KeChuang12.12\\卓然股份吧.csv分析结果.csv'
# Raw_Sentiment_DF = pd.read_csv(file)
# start = 1203
# end = Raw_Sentiment_DF.shape[0]
# for i in range(start, end):
#     Current_Year = Raw_Sentiment_DF['latest_time'][i][:4]
#     Correct_Year = int(Current_Year) + 1
#     Raw_Sentiment_DF['latest_time'][i] = str(Correct_Year) + Raw_Sentiment_DF['latest_time'][i][4:]
#
# Raw_Sentiment_DF.to_csv(file, index=False, encoding='utf_8_sig')


# path = os.path.join("Sentiment_KeChuang/*.csv")
# Raw_Sentiment_CSV_Files = iglob(path)
# Whole_DF = pd.DataFrame()
#
# for file in Raw_Sentiment_CSV_Files:
#     Current_CSV_DF = pd.read_csv(file)
#     Temp_DF = pd.concat([Current_CSV_DF, Whole_DF])
#     Whole_DF = Temp_DF.copy()
#
# Whole_DF.to_csv("Whole_Sentiment.csv", index=False, encoding='utf_8_sig')

RAW_Whole_DF = pd.read_csv("Whole_Sentiment.csv")
RAW_Whole_DF.columns
# count = 0
# for file in Raw_Sentiment_CSV_Files:
#     Current_CSV_DF = pd.read_csv(file)
#     count += Current_CSV_DF.shape[0]

# Simplified_DF = Whole_DF.drop(['view_num', 'comment_num', 'sub_url', 'title', 'poster'], axis=1)
# Simplified_DF.to_csv("Grades&Dates.csv", index=False, encoding='utf_8_sig')
Simplified_DF = pd.read_csv("Grades&Dates.csv")
Simplified_DF['latest_time'] = pd.to_datetime(Simplified_DF['latest_time'])
Sorted_Date_DF = Simplified_DF.sort_values(by='latest_time')

Sorted_Date_DF = Sorted_Date_DF.reset_index(drop=True)
WhetherSameDate(Sorted_Date_DF['latest_time'][0], Sorted_Date_DF['latest_time'][1])

Current_Date = Sorted_Date_DF['latest_time'][0]
Num = 1     # 统计当前天出现的次数
Sentiment = Sorted_Date_DF['Sentiment_Grade'][0]   # 统计当前天情绪分数的累加

PageData_Dict = {'Date': [], 'Sentiment': []}

for i in range(1, Sorted_Date_DF.shape[0]):
    if WhetherSameDate(Current_Date, Sorted_Date_DF['latest_time'][i]):
        Num += 1
        Sentiment += Sorted_Date_DF['Sentiment_Grade'][i]
    else:
        Average_Senti = Sentiment / Num
        PageData_Dict['Date'].append(Current_Date)
        PageData_Dict['Sentiment'].append(Average_Senti)
        Current_Date = Sorted_Date_DF['latest_time'][i]
        Sentiment = Sorted_Date_DF['Sentiment_Grade'][i]
        Num = 1

Sentiment_List = [PageData_Dict['Date'], PageData_Dict['Sentiment']]
Sentiment_DF = pd.DataFrame(Sentiment_List)
Sentiment_DF = Sentiment_DF.T
Sentiment_DF.columns = ['Date', 'Sentiment']
Sentiment_DF['Date'] = Sentiment_DF['Date'].dt.date
Sentiment_DF.to_csv("日期+情绪分数.csv", index=False, encoding='utf_8_sig')


Sentiment_DF = pd.read_csv("日期+情绪分数.csv")
VIX_DF = pd.read_csv("OtherData/^VIX.csv")
VIX_DF = VIX_DF.drop(["High", "Low", "Adj Close"], axis=1)
VIX_DF['Date'] = pd.to_datetime(VIX_DF['Date'])
Sentiment_DF['Date'] = pd.to_datetime(Sentiment_DF['Date'])

Banzhi = pd.read_csv("OtherData/399006.csv")
Banzhi['Date'] = pd.to_datetime(Banzhi['Date'])


Sentiment_DF.set_index('Date', inplace=True)
VIX_DF.set_index('Date', inplace=True)
Banzhi.set_index('Date', inplace=True)

Sentiment_VIX_DF = pd.concat([Sentiment_DF, VIX_DF], axis=1)
Sentiment_VIX_DF = Sentiment_VIX_DF.dropna()
Sentiment_VIX_DF['VIX_Log_Return'] = np.log(Sentiment_VIX_DF['Close'] / Sentiment_VIX_DF['Close'].shift(1))

Whole_DF = pd.concat([Sentiment_VIX_DF, Banzhi], axis=1)
Whole_DF = Whole_DF.dropna()

Whole_DF.to_csv("OtherData/Banzhi&VIX&Sentiment.csv")
Whole_DF = pd.read_csv("OtherData/Banzhi&VIX&Sentiment.csv")
Whole_DF['BanZhi_Log_Return'] = np.log(Whole_DF['BanZhi_Close'] / Whole_DF['BanZhi_Close'].shift(1))

import statsmodels.api as sm
decomposition = sm.tsa.seasonal_decompose(Whole_DF['Sentiment'], model='addictive', period=65)
decomposition.plot()


from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
plot_acf(Sentiment_VIX_DF['Sentiment'].tolist(), lags=50)
plot_pacf(Sentiment_VIX_DF['Sentiment'].tolist(), lags=50)

H = Hurst(Whole_DF['Sentiment'])

from statsmodels.tsa.stattools import adfuller, kpss
result = adfuller(Whole_DF['Sentiment'], autolag='AIC')
print(f'ADF Statistic: {result[0]}')
print(f'p-value: {result[1]}')
for key, value in result[4].items():
    print('Critial Values:')
    print(f'   {key}, {value}')

result = kpss(Whole_DF['Sentiment'], regression='c')
print('\nKPSS Statistic: %f' % result[0])
print('p-value: %f' % result[1])
for key, value in result[3].items():
    print('Critial Values:')
    print(f'   {key}, {value}')

import seaborn as sns
import matplotlib.pyplot as plt
arr = pd.to_datetime(RAW_Whole_DF['latest_time'])

from pmdarima import auto_arima
stepwise_fit = auto_arima(Whole_DF['Sentiment'], trace=True, suppress_warnings=True)
from statsmodels.tsa.stattools import grangercausalitytests
Whole_DF = Whole_DF.dropna()
grangercausalitytests(Whole_DF[['VIX_Close', 'Sentiment']], maxlag=5)
grangercausalitytests(Whole_DF[['BanZhi_Log_Return', 'Sentiment']], maxlag=5)