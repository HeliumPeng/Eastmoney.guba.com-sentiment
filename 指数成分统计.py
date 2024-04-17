import pandas as pd
import baostock as bs

# 登录系统
lg = bs.login()

# 检查登录是否成功
if lg.error_code == '0':
    print("Baostock登录成功")
else:
    print(f"Baostock登录失败，错误代码：{lg.error_code}, 错误信息：{lg.error_msg}")

# 创建日期列表
dates = [f"{year}-{month}-30" for year in range(2017, 2023) for month in ["06", "12"]]

# 创建空的DataFrame用于存储结果
result_df = pd.DataFrame()

# 遍历日期列表
for date in dates:
    # 获取沪深300成分股
    rs = bs.query_hs300_stocks(date=date)
    print('query_hs300 error_code:'+rs.error_code)
    print('query_hs300  error_msg:'+rs.error_msg)

    # 打印结果集
    hs300_stocks = []
    while (rs.error_code == '0') & rs.next():
        # 获取一条记录，将记录合并在一起
        hs300_stocks.append(rs.get_row_data())
    result = pd.DataFrame(hs300_stocks, columns=rs.fields)
    # 将结果添加到result_df中
    result_df = pd.concat([result_df, result])

# 确保日期列是日期类型
result_df['updateDate'] = pd.to_datetime(result_df['updateDate'])

# 去除2017年6月的数据
result_df = result_df[~((result_df['updateDate'].dt.year == 2017) & (result_df['updateDate'].dt.month == 6))]

# 筛选出2017年的数据
original_shanghai_300 = result_df[result_df['updateDate'].dt.year == 2017]

# 创建一个空的DataFrame用于存储每个周期的改变
changes_df = pd.DataFrame()

# 将result_df按照300个数据进行分组
groups = [result_df[i:i+300] for i in range(0, len(result_df), 300)]

# 对每两个相邻的组进行比较
for i in range(len(groups) - 1):
    # 获取当前组和下一组的股票代码
    current_stocks = set(groups[i]['code'])
    next_stocks = set(groups[i+1]['code'])

    # 找出新增和被剔除的股票
    added_stocks = next_stocks - current_stocks
    removed_stocks = current_stocks - next_stocks

    # 获取当前组和下一组的日期
    current_period = groups[i]['updateDate'].min().strftime('%Y-%m-%d')
    next_period = groups[i+1]['updateDate'].min().strftime('%Y-%m-%d')

    # 将改变存入changes_df中
    changes_df = changes_df.append({
        'period': f'{current_period} - {next_period}',
        'added_stocks': ', '.join(added_stocks),
        'removed_stocks': ', '.join(removed_stocks)
    }, ignore_index=True)

# 设置changes_df的列名
changes_df.columns = ['Period', 'Added Stocks', 'Removed Stocks']

# Split the 'Added Stocks' and 'Removed Stocks' columns and stack them into a single column
added_stocks = changes_df['Added Stocks'].str.split(', ', expand=True).stack().reset_index(drop=True)
removed_stocks = changes_df['Removed Stocks'].str.split(', ', expand=True).stack().reset_index(drop=True)

# Count the occurrences of each stock
added_counts = added_stocks.value_counts()
removed_counts = removed_stocks.value_counts()

# Convert the Series to DataFrame and reset the index
added_df = added_counts.to_frame().reset_index()
removed_df = removed_counts.to_frame().reset_index()

# Rename the columns
added_df.columns = ['Stock', 'Count']
removed_df.columns = ['Stock', 'Count']

# Add a new column to indicate whether the stock was added or removed
added_df['Action'] = 'Added'
removed_df['Action'] = 'Removed'

# Concatenate the two dataframes
change_count_df = pd.concat([added_df, removed_df])

# Print the result
print(change_count_df)

# 将result_df按照300个数据进行分组
groups = [result_df[i:i+300] for i in range(0, len(result_df), 300)]

# 初始化一个set用于存储第一个组的股票代码
constant_stocks = set(groups[0]['code'])

# 对后续的每个组进行操作
for group in groups[1:]:
    # 将当前组的股票代码转换为set，然后与constant_stocks进行交集操作
    constant_stocks = constant_stocks & set(group['code'])

# 创建一个新的DataFrame用于存储始终存在的股票的代码和名称
constant_stocks_CSI300 = pd.DataFrame()

# 对每个始终存在的股票进行操作
for stock in constant_stocks:
    # 找出该股票的名称
    stock_name = result_df[result_df['code'] == stock]['code_name'].iloc[0]
    # 将股票的代码和名称添加到constant_stocks_CSI300中
    constant_stocks_CSI300 = constant_stocks_CSI300.append({
        'code': stock,
        'code_name': stock_name
    }, ignore_index=True)

# 打印constant_stocks_CSI300
print(constant_stocks_CSI300)

# 登出系统
bs.logout()

# 打印最终结果
print(result_df)
