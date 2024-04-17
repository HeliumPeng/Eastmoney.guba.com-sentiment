import pandas as pd
import baostock as bs

# Login to the system
lg = bs.login()

# Check if the login was successful
if lg.error_code == '0':
    print("Baostock login successful")
else:
    print(f"Baostock login failed, error code: {lg.error_code}, error message: {lg.error_msg}")

# Create a list of dates for June and December each year from 2017 to 2022
dates = [f"{year}-{month}-30" for year in range(2017, 2023) for month in ["06", "12"]]

# Initialize an empty DataFrame to store the results
result_df = pd.DataFrame()

# Iterate over the list of dates
for date in dates:
    # Query the HS300 stocks for the given date
    rs = bs.query_hs300_stocks(date=date)
    print('query_hs300 error_code: ' + rs.error_code)
    print('query_hs300 error_msg: ' + rs.error_msg)

    # Initialize an empty list to hold the stock data
    hs300_stocks = []
    # Fetch the data in a loop until there are no more records
    while (rs.error_code == '0') & rs.next():
        # Get a row of data and append it to the list
        hs300_stocks.append(rs.get_row_data())

    # Convert the list of stock data into a DataFrame
    result = pd.DataFrame(hs300_stocks, columns=rs.fields)
    
    # Concatenate the new result with the existing result DataFrame
    result_df = pd.concat([result_df, result], ignore_index=True)

# Ensure the 'updateDate' column is of datetime type
result_df['updateDate'] = pd.to_datetime(result_df['updateDate'])

# Remove the data for June 2017
result_df = result_df[~((result_df['updateDate'].dt.year == 2017) & (result_df['updateDate'].dt.month == 6))]

# Filter out the data for the year 2017
original_shanghai_300 = result_df[result_df['updateDate'].dt.year == 2017]

# Initialize an empty DataFrame to store changes in the index composition
changes_df = pd.DataFrame()

# Create groups of 300 stocks from the result DataFrame
groups = [result_df.iloc[i:i+300] for i in range(0, len(result_df), 300)]

# Compare each pair of adjacent groups to find added and removed stocks
for i in range(len(groups) - 1):
    current_stocks = set(groups[i]['code'])
    next_stocks = set(groups[i+1]['code'])
    
    # Find stocks that were added and removed between the two periods
    added_stocks = next_stocks - current_stocks
    removed_stocks = current_stocks - next_stocks
    
    # Get the dates for the current and next periods
    current_period = groups[i]['updateDate'].min().strftime('%Y-%m-%d')
    next_period = groups[i+1]['updateDate'].min().strftime('%Y-%m-%d')
    
    # Append the changes to the changes DataFrame
    changes_df = changes_df.append({
        'Period': f'{current_period} - {next_period}',
        'Added Stocks': ', '.join(added_stocks),
        'Removed Stocks': ', '.join(removed_stocks)
    }, ignore_index=True)

# Set the column names for the changes DataFrame
changes_df.columns = ['Period', 'Added Stocks', 'Removed Stocks']

# Split the 'Added Stocks' and 'Removed Stocks' columns, stack them, and count occurrences
added_stocks = changes_df['Added Stocks'].str.split(', ', expand=True).stack().reset_index(drop=True)
removed_stocks = changes_df['Removed Stocks'].str.split(', ', expand=True).stack().reset_index(drop=True)

added_counts = added_stocks.value_counts().to_frame().reset_index()
removed_counts = removed_stocks.value_counts().to_frame().reset_index()

# Rename the columns and add an 'Action' column to indicate if the stock was added or removed
added_df = added_counts.rename(columns={added_stocks.name: 'Count'}).reset_index()
removed_df = removed_counts.rename(columns={removed_stocks.name: 'Count'}).reset_index()

added_df['Action'] = 'Added'
removed_df['Action'] = 'Removed'

# Concatenate the two DataFrames to get a comprehensive count of all changes
change_count_df = pd.concat([added_df, removed_df])

# Print the result
print(change_count_df)

# Identify stocks that have been constant throughout the periods
constant_stocks = set(groups[0]['code'])
for group in groups[1:]:
    constant_stocks &= set(group['code'])

# Create a DataFrame for the stocks that have remained constant in the index
constant_stocks_CSI300 = pd.DataFrame()
for stock in constant_stocks:
    stock_name = result_df[result_df['code'] == stock]['code_name'].iloc[0]
    constant_stocks_CSI300 = constant_stocks_CSI300.append({'code': stock, 'code_name': stock_name}, ignore_index=True)

# Print the DataFrame containing the constant stocks
print(constant_stocks_CSI300)

# Logout from the system
bs.logout()

# Print the final DataFrame containing the HS300 stocks data
print(result_df)
