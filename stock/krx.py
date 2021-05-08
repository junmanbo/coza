from pykrx import stock
import pandas as pd
import numpy as np
import datetime
import time


#      name = stock.get_market_ticker_name(ticker)
#      print(ticker, name)


#  tickers = stock.get_market_ticker_list("20210504", market="KOSPI")
#  for ticker in tickers:
#      #  df = stock.get_market_ohlcv_by_date("20201104", "20210404", ticker)
#      name = stock.get_market_ticker_name(ticker)
#      print(f"종목 이름: {name}\n종목 코드: {ticker}")
#      print("-----------------------------------------\n")
#      #  profit = (df['종가'][-1] - df['종가'][0]) / df['종가'][0] * 100
#      #  print(f"종목: {name}\n6개월간 수익률: {profit}\n")
#      with 시가("StockCode.txt", 'a') as f:
#          f.write(f"종목 이름: {name}\n종목 코드: {ticker}\n-----------------------------------------\n")
#      time.sleep(0.5)

def calTarget(df):
    #  df['noise'] = 1 - abs(df['시가'] - df['종가']) / (df['고가'] - df['저가'])
    df['range'] = (df['고가'] - df['저가']) * (1 - abs(df['시가'] - df['종가']) / (df['고가'] - df['저가']))
    df['t_bull'] = df['시가'] + df['range'].shift(1)
    df['t_bear'] = df['시가'] - df['range'].shift(1)

def calMA(df, fast=5):
    df['ma'] = df['종가'].ewm( span = fast, min_periods = fast - 1 ).mean().shift(1)

def calStochastic(df, n=10, m=5, t=5):
    ndays_고가 = df.고가.rolling(window=n, min_periods=1).max()
    ndays_저가 = df.저가.rolling(window=n, min_periods=1).min()
    fast_k = ((df.종가 - ndays_저가) / (ndays_고가 - ndays_저가)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k.shift(1) - slow_d.shift(1)
    #  df = df.assign(fast_k=fast_k, fast_d=slow_k, slow_k=slow_k, slow_d=slow_d, slow_osc=slow_osc)
    #  df = df.assign(slow_k=slow_k, slow_osc=slow_osc)
    df['Slow_K'] = slow_k
    df['Slow_OSC'] = slow_osc

def calMACD(df, m_NumFast=5, m_NumSlow=20, m_NumSignal=5):
    df['EMAFast'] = df['종가'].ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
    df['EMASlow'] = df['종가'].ewm( span = m_NumSlow, min_periods = m_NumSlow - 1 ).mean()
    df['MACD'] = df['EMAFast'] - df['EMASlow']
    df['MACD_Signal'] = df['MACD'].ewm( span = m_NumSignal, min_periods = m_NumSignal - 1 ).mean()
    df['MACD_OSC'] = df['MACD'].shift(1) - df['MACD_Signal'].shift(1)

def PrintMDD(pd_chart):
    pd_chart['max_close'] = 0
    pd_chart['min_close'] = 999999999

    for i in range(len(pd_chart)):
        fw_date = pd_chart.index[i]
        bw_date = pd_chart.index[len(pd_chart)-1-i]

        if int(pd_chart.loc[fw_date, '종가']) >= int(pd_chart.loc[fw_date, 'max_close']):
            pd_chart.loc[fw_date:, 'max_close'] = pd_chart.loc[fw_date, '종가']

        if int(pd_chart.loc[bw_date, '종가']) <= int(pd_chart.loc[bw_date, 'min_close']):
            pd_chart.loc[:bw_date, 'min_close'] = pd_chart.loc[bw_date, '종가']

    pd_chart['mdd'] = pd_chart['max_close'] - pd_chart['min_close']

    max_mdd = pd_chart['mdd'].max()
    mask = pd_chart['mdd'] == max_mdd
    mdd_chart = pd_chart.loc[mask,:]

    start_date = str(mdd_chart.index[0])[:10]
    end_date = str(mdd_chart.index[len(mdd_chart)-1])[:10]
    max_close = mdd_chart.loc[mdd_chart.index[0], 'max_close']
    min_close = mdd_chart.loc[mdd_chart.index[0], 'min_close']
    mdd = str(round((1 - min_close / max_close) * 100, 2)) + "%"

    print("현재 차트의 MDD는 {}이고, {}일({}원)부터 {}일({}원)동안 지속되었습니다.".format(mdd, start_date, max_close, end_date, min_close))

start_date = '20140503' # 시작 날짜
end_date = '20210503' # 마지막 날짜
ticker = '005490' # 종목 코드

df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
print(df)
calTarget(df)
calMA(df)
calStochastic(df)
calMACD(df)

#  Just Hold
name = stock.get_market_ticker_name(ticker)
print(f"분석 기간: {start_date} ~ {end_date}\n종목: {name} >>>\n")
print("단순히 보유하는 전략")
#  df['ror'] = df['종가'] / df['시가']
#  df['hpr'] = df['ror'].cumprod()
#  df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
#  print(ticker, "HPR: ", df['hpr'][-2])
#  print(ticker, "MDD: ", df['dd'].max())
hpr = df['종가'][-1] / df['시가'][0]
print(f"HPR: {hpr}")
PrintMDD(df)
print("-----------------------------------------------")

fee = 0.02 / 100
# Calculate Profit
print("변동성 돌파 전략")
df['ror_bull'] = np.where((df['고가'] > df['t_bull']) & (df['ma'] > 0), df['종가'] / df['t_bull'] - fee, 1)
df['hpr'] = df['ror_bull'].cumprod()
df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
print(ticker, "HPR: ", df['hpr'][-2])
print(ticker, "MDD: ", df['dd'].max())
print("-----------------------------------------------")

print("Stochastic + MACD + 변동성 돌파 전략")
df['ror_bull'] = np.where((df['고가'] > df['t_bull']) & (df['Slow_OSC'] > 0) & (df['MACD_OSC'] > 0), df['종가'] / df['t_bull'] - fee, 1)
df['hpr'] = df['ror_bull'].cumprod()
df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
print(ticker, "HPR: ", df['hpr'][-2])
print(ticker, "MDD: ", df['dd'].max())
print("-----------------------------------------------")

print("Stochastic 전략")
df['ror_bull'] = np.where((df['Slow_OSC'] > 0), df['종가'] / df['시가'] - fee, 1)
df['hpr'] = df['ror_bull'].cumprod()
df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
print(ticker, "HPR: ", df['hpr'][-2])
print(ticker, "MDD: ", df['dd'].max())
print("-----------------------------------------------")

print("MACD 전략")
df['ror_bull'] = np.where((df['MACD_OSC'] > 0), df['종가'] / df['시가'] - fee, 1)
df['hpr'] = df['ror_bull'].cumprod()
df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
print(ticker, "HPR: ", df['hpr'][-2])
print(ticker, "MDD: ", df['dd'].max())
print("-----------------------------------------------")

print("Stochastic + MACD 전략")
df['ror_bull'] = np.where((df['Slow_OSC'] > 0) & (df['MACD_OSC'] > 0), df['종가'] / df['시가'] - fee, 1)
df['hpr'] = df['ror_bull'].cumprod()
df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
print(ticker, "HPR: ", df['hpr'][-2])
print(ticker, "MDD: ", df['dd'].max())
print("-----------------------------------------------\n")
