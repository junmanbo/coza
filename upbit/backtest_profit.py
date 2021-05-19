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

def calMA(df, fast=7):
    df['ma'] = df.close.ewm(span=fast).mean().shift(1)

def calStochastic(df, n=9, m=5, t=3):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    df['Slow_K'] = slow_k.shift(1)
    df['Slow_OSC'] = slow_osc.shift(1)
    df['Slow_OSC_Slope'] = slow_osc.shift(1) - slow_osc.shift(2)

def calMACD(df, m_NumFast=14, m_NumSlow=30, m_NumSignal=10):
    EMAFast = df.close.ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
    EMASlow = df.close.ewm( span = m_NumSlow, min_periods = m_NumSlow - 1 ).mean()
    MACD = EMAFast - EMASlow
    MACDSignal = MACD.ewm( span = m_NumSignal, min_periods = m_NumSignal - 1 ).mean()
    df['MACD_OSC'] = MACD.shift(1) - MACDSignal.shift(1)

with open("AnalysisStrategies.txt", 'w') as f:
    #  tickers = pyupbit.get_tickers("KRW")
    tickers = ['KRW-BTC', 'KRW-ETH', 'KRW-NEO', 'KRW-MTL', 'KRW-LTC', 'KRW-XRP', 'KRW-ETC', 'KRW-OMG', 'KRW-SNT', 'KRW-WAVES', 'KRW-QTUM', 'KRW-LSK', 'KRW-STEEM', 'KRW-XLM', 'KRW-ARDR', 'KRW-KMD', 'KRW-ARK', 'KRW-GRS', 'KRW-REP', 'KRW-SBD', 'KRW-POWR', 'KRW-BTG', 'KRW-ICX', 'KRW-EOS', 'KRW-TRX', 'KRW-SC', 'KRW-IGNIS', 'KRW-ONT', 'KRW-POLY', 'KRW-ZRX', 'KRW-LOOM', 'KRW-BCH', 'KRW-ADX', 'KRW-BAT', 'KRW-RFR', 'KRW-CVC', 'KRW-MFT', 'KRW-GAS', 'KRW-UPP', 'KRW-ELF', 'KRW-KNC', 'KRW-BSV', 'KRW-EDR', 'KRW-QKC', 'KRW-BTT', 'KRW-TFUEL', 'KRW-MANA', 'KRW-ANKR', 'KRW-AERGO', 'KRW-ATOM', 'KRW-TT', 'KRW-SOLVE', 'KRW-TSHP', 'KRW-WAXP', 'KRW-HBAR', 'KRW-MED', 'KRW-MLK', 'KRW-STPT', 'KRW-ORBS', 'KRW-VET', 'KRW-CHZ', 'KRW-PXL', 'KRW-STMX', 'KRW-DKA', 'KRW-HIVE', 'KRW-KAVA', 'KRW-AHT', 'KRW-LINK', 'KRW-XTZ', 'KRW-BORA', 'KRW-JST', 'KRW-CRO', 'KRW-SXP', 'KRW-LAMB'] 
    count1 = 0
    count2 = 0
    count_dd1 = 0
    count_dd2 = 0
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

        fee = 0.02 / 100

        df['bull'] = np.where((df['MACD_OSC'] > 0) & (df['Slow_OSC'] > 0) & (df['Slow_OSC_Slope'] > 0) & (df['Slow_K'] < 100), 1, 0)
        df['bear'] = np.where((df['MACD_OSC'] < 0) & (df['Slow_OSC'] < 0) & (df['Slow_OSC_Slope'] < 0) & (df['Slow_K'] > 0), 1, 0)
        df['ror_bull'] = np.where((df['bull'] == 1), np.where((df['high'] > (df['open'] * 1.015)), 1.015 - fee, (df['close'] / df['open'])), 1)
        df['ror_bear'] = np.where((df['bear'] == 1), np.where((df['low'] < (df['open'] * 0.985)), 1.015 - fee, (df['open'] / df['close'])), 1)
        df['hpr'] = df['ror_bull'].cumprod() * df['ror_bear'].cumprod()
        df['dd1'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        df['trading'] = np.where((df['ror_bull'] == 1) & (df['ror_bear'] == 1), 0, 1)
        df['win'] = np.where((df['ror_bull'] > 1) | (df['ror_bear'] > 1), 1, 0)
        df['total_trading'] = df['trading'].cumsum()
        df['total_win'] = df['win'].cumsum()
        df['승률1'] = df['total_win'] / df['total_trading'] * 100
        f.write(f"stoch+macd(2%)\nHPR: {df['hpr'][-2]}\nMDD: {df['dd1'].max()}\n승률: {df['승률1'][-2]}\n---------------------------------\n")

        if df['승률1'][-2] > 80:
            count1 += 1

        if df['dd1'].max() > 25:
            count_dd1 += 1

        #  df.to_excel(f"{ticker}-자동엑셀.xlsx")
        print("\n")
        f.write("\n")
    f.write(f"승률 80 이상: {count1} MDD 25 이상: {count_dd1}")
