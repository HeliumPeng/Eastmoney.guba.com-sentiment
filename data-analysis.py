import pandas as pd

# Read the Excel file
df = pd.read_excel('QX_TRM.xlsx')

# Now you can perform further processing on the dataframe
# For example, you can print the first few rows
print(df.head())

AGGREGATE = df.loc[df['MarketType'] == '5']
AGGREGATE_YEARS = AGGREGATE.loc[AGGREGATE['Parameter'] == '240']
# Convert the 'TradingDate' column to datetime
AGGREGATE_YEARS['TradingDate'] = pd.to_datetime(AGGREGATE_YEARS['TradingDate'])

# Filter the data between the specified dates
filtered_data = AGGREGATE_YEARS.loc[AGGREGATE_YEARS['TradingDate'].between('2018-01-02', '2022-12-30')]

# Count the number of rows in the filtered data
count = len(filtered_data)

print(count)
AGGREGATE_YEARS_01_04 = AGGREGATE_YEARS[AGGREGATE_YEARS['TradingDate'].str.contains("01-04")]
# YEAR_AVERAGE_TURNOVER_RATE = AGGREGATE_YEARS_01_04['TurnoverRate2'].mean()
YEAR_AVERAGE_TURNOVER_RATE = AGGREGATE_YEARS_01_04['TurnoverRate2'].iloc[-11:-1].mean()
print(YEAR_AVERAGE_TURNOVER_RATE)

