import pybithumb
import pandas as pd
import numpy as np

def calMACD(df, m_NumFast=14, m_NumSlow=30, m_NumSignal=10):
    df['EMAFast'] = df['close'].ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
    df['EMASlow'] = df['close'].ewm( span = m_NumSlow, min_periods = m_NumSlow - 1 ).mean()
    df['MACD'] = df['EMAFast'] - df['EMASlow']
    df['MACD_Signal'] = df['MACD'].ewm( span = m_NumSignal, min_periods = m_NumSignal - 1 ).mean()
    df['MACD_OSC'] = df['MACD'] - df['MACD_Signal']
    return df['MACD_OSC']

def calStochastic(df, n=14, m=7, t=7):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    df = df.assign(fast_k=fast_k, fast_d=slow_k, slow_k=slow_k, slow_d=slow_d, slow_osc=slow_osc)
    return df['slow_osc'], df['slow_k']

def cal_target(df):
    df['noise'] = 1 - abs(df['open'] - df['close']) / (df['high'] - df['low'])
    df['range'] = (df['high'] - df['low']) * df['noise']
    df['target_bull'] = df['open'] + df['range'].shift(1)
    df['target_bear'] = df['open'] - df['range'].shift(1)
    return df['target_bull'], df['target_bear']

df = pybithumb.get_ohlcv("BTC")
df['target_bull'] = cal_target(df)[0]
df['target_bear'] = cal_target(df)[1]
df['macd_osc'] = calMACD(df)
df['slow_osc'] = calStochastic(df)[0]
df['slow_k'] = calStochastic(df)[1]
print(df)
df.to_excel("btc.xlsx")
