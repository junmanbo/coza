import pyupbit
import pandas as pd
import numpy as np
import time
import openpyxl

def calRSI(df, N=14):

    difference = df.close - df.close.shift(1)
    df['U'] = np.where(difference > 0, difference, 0)
    df['D'] = np.where(difference < 0, difference * (-1), 0)

    df['AU'] = df['U'].rolling( window=N, min_periods=N).mean()
    df['AD'] = df['D'].rolling( window=N, min_periods=N).mean()
    RSI = df['AU'] / (df['AU']+df['AD']) * 100
    df['RSI'] = RSI

ticker = "KRW-BTC"
df = pyupbit.get_ohlcv(ticker=ticker, interval="day")
calRSI(df)
print(df['RSI'][-1])

