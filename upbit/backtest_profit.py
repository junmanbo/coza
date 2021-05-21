import pyupbit
import pandas as pd
import numpy as np
import time
import openpyxl

def calTarget(df):
    y_range = (df.high - df.low) * (1 - abs(df.open - df.close) / (df.high - df.low))
    df['t_bull'] = df.open + y_range.shift(1)
    df['t_bear'] = df.open - y_range.shift(1)

def calMA(df, fast=14):
    df['ma'] = df.close.ewm(span=fast).mean().shift(1)

def calStochastic(df, n=9, m=3, t=3):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    df['Slow_K'] = slow_k.shift(1)
    df['Slow_OSC'] = slow_osc.shift(1)
    df['Slow_OSC_Slope'] = slow_osc.shift(1) - slow_osc.shift(2)

def calMACD(df, Fast=5, Slow=20, Signal=5):
    EMAFast = df.close.ewm( span = Fast, min_periods = Fast - 1 ).mean()
    EMASlow = df.close.ewm( span = Slow, min_periods = Slow - 1 ).mean()
    MACD = EMAFast - EMASlow
    MACDSignal = MACD.ewm( span = Signal, min_periods = Signal - 1 ).mean()
    df['MACD_OSC'] = MACD.shift(1) - MACDSignal.shift(1)

def calRSI(df, N=14):

    difference = df.close - df.close.shift(1)
    df['U'] = np.where(difference > 0, difference, 0)
    df['D'] = np.where(difference < 0, difference * (-1), 0)

    df['AU'] = df['U'].rolling( window=N, min_periods=N).mean()
    df['AD'] = df['D'].rolling( window=N, min_periods=N).mean()
    df['RSI'] = df['AU'] / (df['AU']+df['AD']) * 100
    df['RSI_SMA'] = df['RSI'].rolling(N).mean().shift(1)

with open("AnalysisStrategies.txt", 'w') as f:
    tickers = pyupbit.get_tickers("KRW")
    count_win = 0
    count_dd = 0
    for ticker in tickers:
        try:
            print(f"코인: {ticker}")
            df = pyupbit.get_ohlcv(ticker=ticker, interval="day")
            #  calTarget(df)
            calMA(df)
            calStochastic(df)
            calMACD(df)
            calRSI(df)
# 기간 제한
            f.write(f"코인: {ticker} >>>>>\n\n")

            fee = 0.02 / 100

            #  df['bull'] = np.where((df['Slow_OSC_Slope'] > 0) & (df['Slow_OSC'] > 0) & (df['RSI_SMA'] < 30), 1, 0)
            #  df['bear'] = np.where((df['Slow_OSC_Slope'] < 0) & (df['Slow_OSC'] < 0) & (df['RSI_SMA'] > 70), 1, 0)
            #  df['ror_bull'] = np.where((df['bull'] == 1), (df['close'] / df['open']) - fee, 1)
            #  df['ror_bear'] = np.where((df['bear'] == 1), (df['open'] / df['close']) - fee, 1)
            #  df['hpr'] = df['ror_bull'].cumprod() * df['ror_bear'].cumprod()
            #  df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
            #  df['trading'] = np.where((df['ror_bull'] == 1) & (df['ror_bear'] == 1), 0, 1)
            #  df['win'] = np.where((df['ror_bull'] > 1) | (df['ror_bear'] > 1), 1, 0)
            #  df['total_trading'] = df['trading'].cumsum()
            #  df['total_win'] = df['win'].cumsum()
            #  df['승률'] = df['total_win'] / df['total_trading'] * 100
            #  f.write(f"stoch+macd(1.5%)\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n승률: {df['승률'][-2]}\n---------------------------------\n")

            df['bull'] = np.where((df['Slow_OSC_Slope'] > 0) & (df['Slow_OSC'] > 0) & (df['MACD_OSC'] > 0) & (df['ma'] < df['open']), 1, 0)
            df['bear'] = np.where((df['Slow_OSC_Slope'] < 0) & (df['Slow_OSC'] < 0) & (df['MACD_OSC'] < 0) & (df['ma'] > df['open']), 1, 0)
            df['ror_bull'] = np.where((df['bull'] == 1), np.where((df['high'] > (df['open'] * 1.015)), 1.015 - fee, (df['close'] / df['open']) - fee), 1)
            df['ror_bear'] = np.where((df['bear'] == 1), np.where((df['low'] < (df['open'] * 0.985)), 1.015 - fee, (df['open'] / df['close']) - fee), 1)
            df['hpr'] = df['ror_bull'].cumprod() * df['ror_bear'].cumprod()
            df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
            df['trading'] = np.where((df['ror_bull'] == 1) & (df['ror_bear'] == 1), 0, 1)
            df['win'] = np.where((df['ror_bull'] > 1) | (df['ror_bear'] > 1), 1, 0)
            df['total_trading'] = df['trading'].cumsum()
            df['total_win'] = df['win'].cumsum()
            df['승률'] = df['total_win'] / df['total_trading'] * 100
            f.write(f"stoch+macd(1.5%)\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n승률: {df['승률'][-2]}\n---------------------------------\n")

            if df['승률'][-2] > 90:
                count_win += 1

            if df['dd'].max() < 20:
                count_dd += 1

            #  df.to_excel(f"/home/cocojun/Logs/{ticker}-자동엑셀.xlsx")
            print("\n")
            f.write("\n")
        except:
            pass
    f.write(f"전략>>>\n승률 90이상: {count_win} MDD 20 이하: {count_dd}")
