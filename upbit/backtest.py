import pyupbit
import pandas as pd
import numpy as np
import time
import openpyxl

np.seterr(divide='ignore', invalid='ignore')

def calTarget(df):
    y_range = (df.high - df.low) * (1 - abs(df.open - df.close) / (df.high - df.low))
    df['t_bull'] = df.open + y_range.shift(1)
    df['t_bear'] = df.open - y_range.shift(1)

def calMA(df, fast=5):
    df['ma'] = df.close.ewm(span=fast).mean().shift(1)

def calStochastic(df, n=9, m=5, t=3):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    df['Slow_OSC'] = slow_osc.shift(1)

def calMACD(df, m_NumFast=14, m_NumSlow=30, m_NumSignal=10):
    EMAFast = df.close.ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
    EMASlow = df.close.ewm( span = m_NumSlow, min_periods = m_NumSlow - 1 ).mean()
    MACD = EMAFast - EMASlow
    MACDSignal = MACD.ewm( span = m_NumSignal, min_periods = m_NumSignal - 1 ).mean()
    df['MACD_OSC'] = MACD.shift(1) - MACDSignal.shift(1)

with open("AnalysisStrategies.txt", 'w') as f:
    tickers = ['KRW-BTC', 'KRW-ETH', 'KRW-NEO', 'KRW-MTL', 'KRW-LTC', 'KRW-XRP', 'KRW-ETC', 'KRW-OMG', 'KRW-QTUM', 'KRW-XLM', 'KRW-ADA', 'KRW-BTG', 'KRW-ICX', 'KRW-TRX']
    count1 = 0
    count2 = 0
    start_date = '2020-04-12'
    end_date = '2021-04-24'
    print(f"분석 날짜 {start_date} ~ {end_date}\n")
    for ticker in tickers:
        print(f"코인: {ticker}")
        df = pyupbit.get_ohlcv(ticker=ticker, interval="day")
        calTarget(df)
        calMA(df)
        calStochastic(df)
        calMACD(df)
# 기간 제한
        #  df=df.loc[start_date:end_date]
        f.write(f"코인: {ticker} >>>>>\n\n")

        ror = np.where((1>0), df['close'] / df['open'], 1)
        df['hpr'] = ror.cumprod()
        df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        f.write(f"Just Holding\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n---------------------------------\n")

        fee = 0.02 / 100

        #  ror_bull = np.where((df.open > df.ma) & (df.high > df.t_bull), df.close / df.t_bull - fee, 1)
        #  ror_bear = np.where((df.open < df.ma) & (df.low < df.t_bear), df.t_bear / df.close - fee, 1)
        #  df['hpr'] = ror_bull.cumprod() * ror_bear.cumprod()
        #  df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        #  trading = np.where((ror_bull == 1) & (ror_bear == 1), 0, 1)
        #  win = np.where((ror_bull > 1) | (ror_bear > 1), 1, 0)
        #  total_trading = trading.cumsum()
        #  total_win = win.cumsum()
        #  df['승률'] = total_win / total_trading * 100
        #  f.write(f"변동성 돌파\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n승률: {df['승률'][-2]}\n---------------------------------\n")

        df['bull'] = np.where((df['Slow_OSC'] > 0), 1, 0)
        df['bear'] = np.where((df['Slow_OSC'] < 0), 1, 0)
        df['ror_bull'] = np.where((df['bull'] == 1), np.where((df['high'] > (df['open'] * 1.015)), 1.015 - fee, (df['close'] / df['open']) - fee), 1)
        df['ror_bear'] = np.where((df['bear'] == 1), np.where((df['low'] < (df['open'] * 0.995)), 1.015 - fee, (df['open'] / df['close']) - fee), 1)
        df['hpr'] = df['ror_bull'].cumprod() * df['ror_bear'].cumprod()
        df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        df['trading'] = np.where((df['ror_bull'] == 1) & (df['ror_bear'] == 1), 0, 1)
        df['win'] = np.where((df['ror_bull'] > 1) | (df['ror_bear'] > 1), 1, 0)
        df['total_trading'] = df['trading'].cumsum()
        df['total_win'] = df['win'].cumsum()
        df['승률1'] = df['total_win'] / df['total_trading'] * 100
        f.write(f"stoch(1.5% 익절)\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n승률: {df['승률1'][-2]}\n---------------------------------\n")

        df['bull'] = np.where((df['MACD_OSC'] > 0) & (df['Slow_OSC'] > 0), 1, 0)
        df['bear'] = np.where((df['MACD_OSC'] < 0) & (df['Slow_OSC'] < 0), 1, 0)
        df['ror_bull'] = np.where((df['bull'] == 1), np.where((df['high'] > (df['open'] * 1.015)), 1.015 - fee, (df['close'] / df['open']) - fee), 1)
        df['ror_bear'] = np.where((df['bear'] == 1), np.where((df['low'] < (df['open'] * 0.995)), 1.015 - fee, (df['open'] / df['close']) - fee), 1)
        df['hpr'] = df['ror_bull'].cumprod() * df['ror_bear'].cumprod()
        df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        df['trading'] = np.where((df['ror_bull'] == 1) & (df['ror_bear'] == 1), 0, 1)
        df['win'] = np.where((df['ror_bull'] > 1) | (df['ror_bear'] > 1), 1, 0)
        df['total_trading'] = df['trading'].cumsum()
        df['total_win'] = df['win'].cumsum()
        df['승률2'] = df['total_win'] / df['total_trading'] * 100
        f.write(f"stoch(1.5% 익절)+macd\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n승률: {df['승률2'][-2]}\n---------------------------------\n")

        if df['승률1'][-2] > df['승률2'][-2]:
            count1 += 1
        else:
            count2 += 1

        #  ror_bull = np.where((df.Slow_OSC > 0), df.close / df.open - fee, 1)
        #  ror_bear = np.where((df.Slow_OSC < 0), df.open / df.close - fee, 1)
        #  df['hpr'] = ror_bull.cumprod() * ror_bear.cumprod()
        #  df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        #  trading = np.where((ror_bull == 1) & (ror_bear == 1), 0, 1)
        #  win = np.where((ror_bull > 1) | (ror_bear > 1), 1, 0)
        #  total_trading = trading.cumsum()
        #  total_win = win.cumsum()
        #  df['승률'] = total_win / total_trading * 100
        #  f.write(f"Stochastic\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n승률: {df['승률'][-2]}\n---------------------------------\n")
        #
        #  ror_bull = np.where((df.Slow_OSC > 0) & (df.Slow_K < 80) & (df.MACD_OSC > 0) & (df.open > df.ma), df.close / df.open - fee, 1)
        #  ror_bear = np.where((df.Slow_OSC < 0) & (df.Slow_K > 30) & (df.MACD_OSC < 0) & (df.open < df.ma), df.open / df.close - fee, 1)
        #  df['hpr'] = ror_bull.cumprod() * ror_bear.cumprod()
        #  df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        #  trading = np.where((ror_bull == 1) & (ror_bear == 1), 0, 1)
        #  win = np.where((ror_bull > 1) | (ror_bear > 1), 1, 0)
        #  total_trading = trading.cumsum()
        #  total_win = win.cumsum()
        #  df['승률'] = total_win / total_trading * 100
        #  f.write(f"stoch+ema+macd\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n승률: {df['승률'][-2]}\n---------------------------------\n")

        #  df.to_excel(f"{ticker}-Stochastic(50%).xlsx")

        time.sleep(0.1)
        print("\n")
        f.write("\n")
    f.write(f"Stochastic 이긴 수: {count1}\nStoch+MACD(14,30,10) 이긴 수: {count2}\n")

