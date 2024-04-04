import pandas as pd
import requests

raw = pd.read_csv("Code_List/深市列表Code&Name.csv")
code = []
for i in raw['code']:
    str_code = str(i)
    code.append(str_code.zfill(6))

raw['code'] = code

record_data = pd.read_csv("深市列表_doing.csv")
code = []
for i in record_data['code']:
    str_code = str(i)
    code.append(str_code.zfill(6))
record_data['code'] = code

name = []
for i in record_data['code']:
    temp = raw[raw['code'] == i].index.tolist()[0]
    name.append(raw['name'][temp])

record_data['name'] = name
record_data.to_csv("test.csv", index=False, header=["code", "name"], encoding='utf-8-sig')
test_data = pd.read_csv("test.csv", converters={'code': lambda x: x.zfill(6)})  # 注意


def IDtoName(stock):
    Raw_Table = pd.read_csv("深市列表Code&Name_Doing.csv")
    index = Raw_Table[Raw_Table['code'] == int(stock)].index.tolist()[0]
    return Raw_Table['name'][index]



# 测试巨量代理有效性
# JuLiang_URL = "http://v2.api.juliangip.com/unlimited/getips?num=10&pt=1&result_type=json&trade_no=5500550513136284&sign=a5a164e16bc0a923a47c6c42d191eec5"
# proxies = requests.get(JuLiang_URL).json()['data']['proxy_list']



from cnsenti import Emotion

emotion = Emotion()
# 对于这个cnsenti库我的建议是别用，预训练模型泛化能力差得很，几乎全是中立词

data = pd.read_csv("ShangHai_Market/ST康美吧.csv")
