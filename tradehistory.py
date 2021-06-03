# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import openpyxl
import pandas as pd
import numpy as np
import datetime

# %%
df_new = pd.DataFrame()

# 추출하고 싶은 년, 월 설정
year = '2021'
month = '6'
day = ''

df = pd.read_excel(io='/home/cocojun/Downloads/ExportTradeHistory.xlsx', index_col='Date(UTC)')
df.index =  pd.to_datetime(df.index)
df.drop(['Side', 'Price', 'Fee', 'Fee Coin', 'Quote Asset'], axis=1, inplace=True)

for i in range(1, 31, 1):
    day = str(i)
    a = [year, month, day]
    date = '-'.join(a)

    filtered_df = df.loc[date]

    symbols = np.array(filtered_df['Symbol'].tolist())
    symbols = list(set(symbols))
    date = [datetime.datetime(int(year), int(month), i)]
    columns = ['Symbol', 'Quantity', 'Amount', 'Realized Profit', 'Rate of Profit', 'Rate of Win']
    index = pd.DatetimeIndex(date)
    data = []
    for symbol in symbols:
        mask = (filtered_df['Symbol'] == symbol)
        quantity = filtered_df.loc[mask]['Quantity'].sum()
        amount = filtered_df.loc[mask]['Amount'].sum()
        realized_profit = filtered_df.loc[mask]['Realized Profit'].sum()
        rate_profit = realized_profit / amount
        win = 0
        if rate_profit > 0:
            win = 1
        data = [(symbol, quantity, amount, realized_profit, rate_profit, win)]
        new_data = pd.DataFrame(data=data, columns=columns, index=index)
        df_new = df_new.append(new_data)
        df_new.dropna(inplace=True)

print(df_new)
df_new.to_excel('/home/cocojun/Downloads/TradeHistory_June.xlsx', index_label='Date')


# %%

    #append one dataframe to othher
    #  df.to_excel('/home/cocojun/Downloads/Export Trade History.xlsx', index_label='date')
    #  length = len(df['Realized Profit'])
    #  try:
    #      for i in range(0, length+1, 1):
    #          if df['Realized Profit'][i] == 0.0:
    #              df = df.drop(df.index[i])
    #  except:
    #      pass

    #  mask = (df.index >= fromdate) & (df.index <= todate)
