#Relative Strength Index
import numpy as np
import pandas as pd
import pyupbit

def fnRSI(df, N=14):

    U = np.where(df.close.diff(1) > 0, df.close.diff(1), 0)
    D = np.where(df.close.diff(1) < 0, df.close.diff(1) * (-1), 0)

    AU = pd.DataFrame(U).rolling( window=N, min_periods=N).mean()
    AD = pd.DataFrame(D).rolling( window=N, min_periods=N).mean()
    RSI = AU / (AD+AU) * 100
    df['RSI'] = RSI

def calRSI(df, N=14):

    df['U'] = np.where(df.close.diff(1) > 0, df.close.diff(1), 0)
    df['D'] = np.where(df.close.diff(1) < 0, df.close.diff(1) * (-1), 0)

    df['AU'] = df['U'].rolling( window=N, min_periods=N).mean()
    df['AD'] = df['D'].rolling( window=N, min_periods=N).mean()
    df['RSI'] = df['AU'] / (df['AD']+df['AU']) * 100
    return df['RSI'][-1]

ticker = 'KRW-BTC'
df = pyupbit.get_ohlcv(ticker, interval='day')
calRSI(df)
print(calRSI(df))
