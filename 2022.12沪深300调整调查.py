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
dates = ["2022-01-01", "2022-06-30", "2023-01-31", "2023-06-30"]

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

# 打印changes_df
print(changes_df)

# 登出系统
bs.logout()

# 打印最终结果
print(result_df)