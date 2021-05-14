import pyupbit
import pandas as pd
import numpy as np
import time
import openpyxl

def calTarget(df):
    y_range = (df.high - df.low) * (1 - abs(df.open - df.close) / (df.high - df.low))
    df['t_bull'] = df.open + y_range.shift(1)
    df['t_bear'] = df.open - y_range.shift(1)

def calMA5(df, fast=5):
    df['ma5'] = df.close.ewm(span=fast).mean().shift(1)

def calStochastic(df, n=9, m=3, t=3):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    #  df = df.assign(fast_k=fast_k, fast_d=slow_k, slow_k=slow_k, slow_d=slow_d, slow_osc=slow_osc)
    df['Slow_OSC'] = slow_osc.shift(1)

def calMACD(df, m_NumFast=12, m_NumSlow=26, m_NumSignal=9):
    EMAFast = df.close.ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
    EMASlow = df.close.ewm( span = m_NumSlow, min_periods = m_NumSlow - 1 ).mean()
    MACD = EMAFast - EMASlow
    MACDSignal = MACD.ewm( span = m_NumSignal, min_periods = m_NumSignal - 1 ).mean()
    df['MACD_OSC'] = MACD.shift(1) - MACDSignal.shift(1)

with open("AnalysisStrategies.txt", 'w') as f:
    tickers = ['KRW-BTC', 'KRW-ETH', 'KRW-ETC', 'KRW-XRP', 'KRW-QTUM', 'KRW-EOS', 'KRW-BCH', 'KRW-LTC', 'KRW-BTG']
    start_date = '2020-04-12'
    end_date = '2021-04-24'
    print(f"분석 날짜 {start_date} ~ {end_date}\n")
    for ticker in tickers:
        print(f"코인: {ticker}")
        df = pyupbit.get_ohlcv(ticker=ticker, interval="day")
        calTarget(df)
        calMA5(df)
        calStochastic(df)
        calMACD(df)
# 기간 제한
        #  df=df.loc[start_date:end_date]
        #  Just Hold
        f.write(f"분석 기간: {start_date} ~ {end_date}\n코인: {ticker} >>>>>\n\n")

        #  df['ror'] = np.where((1>0), df['close'] / df['open'], 1)
        #  df['hpr'] = df['ror'].cumprod()
        #  df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        #  f.write(f"단순히 보유하는 전략\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n---------------------------------\n")

        fee = 0.02 / 100
#  # Calculate Profit
        #  df['ror_bull'] = np.where((df['high'] > df['t_bull']) & (df['open'] > df['ma5']), df['close'] / df['t_bull'] - fee, 1)
        #  df['ror_bear'] = np.where((df['low'] < df['t_bear']) & (df['open'] < df['ma5']), df['t_bear'] / df['close'] - fee, 1)
        #  df['hpr'] = df['ror_bull'].cumprod() * df['ror_bear'].cumprod()
        #  df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        #  df['Trading'] = np.where((df['ror_bull'] == 1) & (df['ror_bear'] == 1), 0, 1)
        #  df['Win'] = np.where((df['ror_bull'] > 1) | (df['ror_bear'] > 1), 1, 0)
        #  #  df['Win'] = np.where(((df['ror_bull'] > 1) | (df['ror_bear'] > 1), 1, 0))
        #  f.write(f"변동성 돌파 전략(ma5) - 매수+공매도\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n-----------------------------------------------\n")

        #  df['ror_bull'] = np.where((df['Slow_OSC'] > 0) & (df['high'] > df['t_bull']) & (df['open'] > df['ma5']), df['close'] / df['t_bull'] - fee, 1)
        #  df['ror_bear'] = np.where((df['Slow_OSC'] < 0) & (df['low'] < df['t_bear']) & (df['open'] < df['ma5']), df['t_bear'] / df['close'] - fee, 1)
        #  df['hpr'] = df['ror_bull'].cumprod() * df['ror_bear'].cumprod()
        #  df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        #  df['Trading'] = np.where((df['ror_bull'] == 1) & (df['ror_bear'] == 1), 0, 1)
        #  df['Win'] = np.where((df['ror_bull'] > 1) | (df['ror_bear'] > 1), 1, 0)
        #  df['Total_Trading'] = df['Trading'].cumsum()
        #  df['Total_Win'] = df['Win'].cumsum()
        #  f.write(f"변동성 돌파 전략(ma5) + Stochastic - 매수+공매도\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n-----------------------------------------------\n")
        #
        #  df['ror_bull'] = np.where((df['Slow_OSC'] > 0), df['close'] / df['open'], 1)
        #  df['ror_bear'] = np.where((df['Slow_OSC'] < 0), df['open'] / df['close'], 1)
        #  df['hpr'] = df['ror_bull'].cumprod() * df['ror_bear'].cumprod()
        #  df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        #  df['Trading'] = np.where((df['ror_bull'] == 1) & (df['ror_bear'] == 1), 0, 1)
        #  df['Win'] = np.where((df['ror_bull'] > 1) | (df['ror_bear'] > 1), 1, 0)
        #  df['Total_Trading'] = df['Trading'].cumsum()
        #  df['Total_Win'] = df['Win'].cumsum()
        #  f.write(f"Stochastic 전략\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n-----------------------------------------------\n")
        #
        #  df['ror_bull'] = np.where((df['Slow_OSC'] > 0) & (df['open'] > df['ma5']), df['close'] / df['open'] - fee, 1)
        #  df['ror_bear'] = np.where((df['Slow_OSC'] < 0) & (df['open'] < df['ma5']), df['open'] / df['close'] - fee, 1)
        #  df['hpr'] = df['ror_bull'].cumprod() * df['ror_bear'].cumprod()
        #  df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        #  df['Trading'] = np.where((df['ror_bull'] == 1) & (df['ror_bear'] == 1), 0, 1)
        #  df['Win'] = np.where((df['ror_bull'] > 1) | (df['ror_bear'] > 1), 1, 0)
        #  df['Total_Trading'] = df['Trading'].cumsum()
        #  df['Total_Win'] = df['Win'].cumsum()
        #  f.write(f"Stochastic + EMA7 전략\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n-----------------------------------------------\n")

        df['ror_bull'] = np.where((df['Slow_OSC'] > 1) & (df['open'] > df['ma5']) & (df['MACD_OSC'] > 0) & (df['high'] > df['t_bull']), df['close'] / df['t_bull'] - fee, 1)
        df['ror_bear'] = np.where((df['Slow_OSC'] < -1) & (df['open'] < df['ma5']) & (df['MACD_OSC'] < 0) & (df['low'] < df['t_bear']), df['t_bear'] / df['close'] - fee, 1)
        df['hpr'] = df['ror_bull'].cumprod() * df['ror_bear'].cumprod()
        df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        df['Trading'] = np.where((df['ror_bull'] == 1) & (df['ror_bear'] == 1), 0, 1)
        df['Win'] = np.where((df['ror_bull'] > 1) | (df['ror_bear'] > 1), 1, 0)
        df['Total_Trading'] = df['Trading'].cumsum()
        df['Total_Win'] = df['Win'].cumsum()
        #  f.write(f"Stochastic + EMA7 전략\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n-----------------------------------------------\n")

        df.to_excel(f"{ticker}-Stochastic+ma5+macd+변동성.xlsx")

        time.sleep(0.5)
        print("\n")
        f.write("\n")

