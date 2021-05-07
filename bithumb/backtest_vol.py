import pybithumb
import pandas as pd
import numpy as np

def calTarget(df):
    #  df['noise'] = 1 - abs(df['open'] - df['close']) / (df['high'] - df['low'])
    df['range'] = (df['high'] - df['low']) * (1 - abs(df['open'] - df['close']) / (df['high'] - df['low']))
    df['t_bull'] = df['open'] + df['range'].shift(1)
    df['t_bear'] = df['open'] - df['range'].shift(1)

def calMA(df, fast=7):
    df['ma'] = df['close'].ewm( span = fast, min_periods = fast - 1 ).mean().shift(1)

def calStochastic(df, n=9, m=3, t=3):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    #  df = df.assign(fast_k=fast_k, fast_d=slow_k, slow_k=slow_k, slow_d=slow_d, slow_osc=slow_osc)
    #  df = df.assign(slow_k=slow_k, slow_osc=slow_osc)
    df['Slow_K'] = slow_k
    df['Slow_OSC'] = slow_osc

def calMACD(df, m_NumFast=12, m_NumSlow=26, m_NumSignal=9):
    df['EMAFast'] = df['close'].ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
    df['EMASlow'] = df['close'].ewm( span = m_NumSlow, min_periods = m_NumSlow - 1 ).mean()
    df['MACD'] = df['EMAFast'] - df['EMASlow']
    df['MACD_Signal'] = df['MACD'].ewm( span = m_NumSignal, min_periods = m_NumSignal - 1 ).mean()
    df['MACD_OSC'] = df['MACD'] - df['MACD_Signal']


tickers = ['BTC', 'ETH', 'XRP', 'ETC', 'QTUM','LTC']
for ticker in tickers:
    df = pybithumb.get_ohlcv(ticker)
    calTarget(df)
    calMA(df)
    calStochastic(df)
    calMACD(df)
# 기간 제한
    df=df.loc['2017-11-1':'2020-01-01']
    #  Just Hold
    #  print(ticker, df['close'][-1] / df['open'][0])

    fee = 0.01 / 100
# Calculate Profit 
    #  df['ror_bull'] = np.where((df['high'] > df['t_bull']) & (df['open'] > df['ma']), df['close'] / df['t_bull'] - fee, 1)
    #  df['ror_bear'] = np.where((df['low'] < df['t_bear']) & (df['open'] < df['ma']), df['t_bear'] / df['close'] - fee, 1)

    #  df['ror_bull'] = np.where((df['Slow_OSC'] > 0), df['close'] / df['open'] - fee, 1)
    #  df['ror_bear'] = np.where((df['Slow_OSC'] < 0) & (df['MACD_OSC'] < 0), df['open'] / df['close'] - fee, 1)
    #
    #  df['ror_bull'] = np.where((df['Slow_OSC'] > 0) & (df['MACD_OSC'] > 0), df['close'] / df['open'] - fee, 1)
    #  df['ror_bear'] = np.where((df['Slow_OSC'] < 0) & (df['MACD_OSC'] < 0), df['open'] / df['close'] - fee, 1)

    #  df['ror_bull'] = np.where((df['Slow_OSC'] > 0), df['close'] / df['open'] - fee, 1)
    #  df['ror_bear'] = np.where((df['Slow_OSC'] < 0), df['open'] / df['close'] - fee, 1)
    #
    #  df['hpr'] = df['ror_bull'].cumprod() * df['ror_bear'].cumprod()
    #  df['hpr'] = df['ror_bull'].cumprod()
    df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
    print(ticker, "HPR: ", df['hpr'][-2])
    print(ticker, "MDD: ", df['dd'].max())
    print("-----------------------------------------------")
