import pandas as pd
import baostock as bs

# Login to the system
lg = bs.login()

# Check if the login was successful
if lg.error_code == '0':
    print("Baostock login successful")
else:
    print(f"Baostock login failed, error code: {lg.error_code}, error message: {lg.error_msg}")

# Create a list of dates
dates = [f"{year}-{month}-30" for year in range(2017, 2023) for month in ["06", "12"]]

# Create an empty DataFrame to store the results
result_df = pd.DataFrame()

# Iterate through the list of dates
for date in dates:
    # Get the CSI 300 constituent stocks
    rs = bs.query_zz500_stocks(date=date)
    print('query_zz500 error_code:'+rs.error_code)
    print('query_zz500 error_msg:'+rs.error_msg)

    # Print the result set
    zz500_stocks = []
    while (rs.error_code == '0') & rs.next():
        # Get a record and append it to the list
        zz500_stocks.append(rs.get_row_data())
    result = pd.DataFrame(zz500_stocks, columns=rs.fields)
    # Append the result to result_df
    result_df = pd.concat([result_df, result])

# Ensure the date column is of datetime type
result_df['updateDate'] = pd.to_datetime(result_df['updateDate'])

# Remove data from June 2017
result_df = result_df[~((result_df['updateDate'].dt.year == 2017) & (result_df['updateDate'].dt.month == 6))]

# Group the result_df into groups of 300 data points
groups = [result_df[i:i+500] for i in range(0, len(result_df), 500)]

# Initialize a set to store the stock codes in the first group
constant_stocks = set(groups[0]['code'])

# Iterate through the subsequent groups
for group in groups[1:]:
    # Convert the stock codes of the current group to a set and perform an intersection with constant_stocks
    constant_stocks = constant_stocks & set(group['code'])

# Create a new DataFrame to store the codes and names of stocks that are always present
constant_stocks_CSI500 = pd.DataFrame()

# Iterate through the stocks that are always present
for stock in constant_stocks:
    # Find the name of the stock
    stock_name = result_df[result_df['code'] == stock]['code_name'].iloc[0]
    # Append the stock code and name to constant_stocks_CSI500
    constant_stocks_CSI500 = constant_stocks_CSI500.append({
        'code': stock,
        'code_name': stock_name
    }, ignore_index=True)

# Create an empty DataFrame to store the changes in each period
changes_df = pd.DataFrame()

# Compare each pair of adjacent groups
for i in range(len(groups) - 1):
    # Get the stock codes of the current and next groups
    current_stocks = set(groups[i]['code'])
    next_stocks = set(groups[i+1]['code'])

    # Find the added and removed stocks
    added_stocks = next_stocks - current_stocks
    removed_stocks = current_stocks - next_stocks

    # Get the dates of the current and next periods
    current_period = groups[i]['updateDate'].min().strftime('%Y-%m-%d')
    next_period = groups[i+1]['updateDate'].min().strftime('%Y-%m-%d')

    # Append the changes to changes_df
    changes_df = changes_df.append({
        'period': f'{current_period} - {next_period}',
        'added_stocks': ', '.join(added_stocks),
        'removed_stocks': ', '.join(removed_stocks)
    }, ignore_index=True)

# Set the column names for changes_df
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
added_df['Action']
