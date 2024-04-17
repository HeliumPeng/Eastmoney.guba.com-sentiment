import pandas as pd
import baostock as bs

# Log in to the system
login_result = bs.login()

# Check if the login was successful
if login_result.error_code == '0':
    print("Baostock login successful")
else:
    print(f"Baostock login failed, error code: {login_result.error_code}, error message: {login_result.error_msg}")

# Create a list of specific dates
dates = ["2022-01-01", "2022-06-30", "2023-01-31", "2023-06-30"]

# Initialize an empty DataFrame to store the results
result_df = pd.DataFrame()

# Iterate over the list of dates
for date in dates:
    # Query the HS300 stocks for the given date
    stock_rs = bs.query_hs300_stocks(date=date)
    
    # Check for errors in the query
    if stock_rs.error_code != '0':
        print(f"Failed to fetch HS300 stocks for date {date}. Error code: {stock_rs.error_code}, Error message: {stock_rs.error_msg}")
        continue
    
    # Fetch data in a loop until there are no more records
    while stock_rs.error_code == '0' and stock_rs.next():
        # Get a row of data and append it to the list
        hs300_stocks = stock_rs.get_row_data()
        result_df = result_df.append(hs300_stocks, ignore_index=True)

# Ensure the 'updateDate' column is of datetime type
result_df['updateDate'] = pd.to_datetime(result_df['updateDate'])

# Initialize an empty DataFrame to store changes in stock composition between evaluations
changes_df = pd.DataFrame()

# Group the result DataFrame by 300 records to simulate the HS300 index composition
groups = [result_df.iloc[i:i+300] for i in range(0, len(result_df), 300)]

# Compare each pair of adjacent groups to identify added and removed stocks
for i in range(len(groups) - 1):
    current_stocks = set(groups[i]['code'])
    next_stocks = set(groups[i+1]['code'])
    
    # Find stocks that were added and removed
    added_stocks = next_stocks - current_stocks
    removed_stocks = current_stocks - next_stocks
    
    # Get the min update date for the period, format as string
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

# Print the DataFrame containing changes in stock composition
print(changes_df)

# Log out from the system
bs.logout()

# Print the final DataFrame containing the HS300 stocks data
print(result_df)
