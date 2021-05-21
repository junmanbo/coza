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
    df['ndays_high'] = df['high'].rolling(window=n, min_periods=1).max()
    df['ndays_low'] = df['low'].rolling(window=n, min_periods=1).min()
    df['fast_k'] = ((df['close'] - df['ndays_low']) / (df['ndays_high'] - df['ndays_low'])) * 100
    df['slow_k'] = df['fast_k'].ewm(span=m).mean()
    df['slow_d'] = df['slow_k'].ewm(span=t).mean()
    df['slow_osc'] = df['slow_k'] - df['slow_d']
    #  df['Slow_OSC'] = df['slow_osc'].shift(1)
    df['Slow_OSC'] = df['slow_osc']

def calMACD(df, m_NumFast=14, m_NumSlow=30, m_NumSignal=10):
    EMAFast = df.close.ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
    EMASlow = df.close.ewm( span = m_NumSlow, min_periods = m_NumSlow - 1 ).mean()
    MACD = EMAFast - EMASlow
    MACDSignal = MACD.ewm( span = m_NumSignal, min_periods = m_NumSignal - 1 ).mean()
    df['MACD_OSC'] = MACD.shift(1) - MACDSignal.shift(1)

count_win = 0
count_dd = 0
with open("AnalysisStrategies.txt", 'w') as f:
    #  tickers = pyupbit.get_tickers("KRW")
    tickers = ['KRW-BTC', 'KRW-ETH', 'KRW-NEO', 'KRW-MTL', 'KRW-LTC', 'KRW-XRP', 'KRW-ETC', 'KRW-OMG', 'KRW-SNT', 'KRW-WAVES', 'KRW-XEM', 'KRW-QTUM', 'KRW-LSK', 'KRW-STEEM', 'KRW-XLM', 'KRW-ARDR', 'KRW-KMD', 'KRW-ARK', 'KRW-STORJ', 'KRW-GRS', 'KRW-REP', 'KRW-EMC2', 'KRW-ADA', 'KRW-SBD', 'KRW-POWR', 'KRW-BTG', 'KRW-ICX', 'KRW-EOS', 'KRW-TRX', 'KRW-SC', 'KRW-IGNIS', 'KRW-ONT', 'KRW-ZIL', 'KRW-POLY', 'KRW-ZRX', 'KRW-LOOM', 'KRW-BCH', 'KRW-ADX', 'KRW-BAT', 'KRW-IOST', 'KRW-DMT', 'KRW-RFR', 'KRW-CVC', 'KRW-IQ', 'KRW-IOTA', 'KRW-MFT', 'KRW-ONG', 'KRW-GAS', 'KRW-UPP', 'KRW-ELF', 'KRW-KNC', 'KRW-BSV', 'KRW-THETA', 'KRW-EDR', 'KRW-QKC', 'KRW-BTT', 'KRW-MOC', 'KRW-ENJ', 'KRW-TFUEL', 'KRW-MANA', 'KRW-ANKR', 'KRW-AERGO', 'KRW-ATOM', 'KRW-TT', 'KRW-CRE', 'KRW-SOLVE', 'KRW-MBL', 'KRW-TSHP', 'KRW-WAXP', 'KRW-HBAR', 'KRW-MED', 'KRW-MLK', 'KRW-STPT', 'KRW-ORBS', 'KRW-VET', 'KRW-CHZ', 'KRW-PXL', 'KRW-STMX', 'KRW-DKA', 'KRW-HIVE', 'KRW-KAVA', 'KRW-AHT', 'KRW-LINK', 'KRW-XTZ', 'KRW-BORA', 'KRW-JST', 'KRW-CRO', 'KRW-TON', 'KRW-SXP', 'KRW-LAMB'] 
    for ticker in tickers:
        print(f"코인: {ticker}")
        df = pyupbit.get_ohlcv(ticker=ticker, interval="day")
        calStochastic(df)
# 기간 제한
        #  df=df.loc[start_date:end_date]
        f.write(f"코인: {ticker} >>>>>\n\n")

        df['ror'] = np.where((1>0), df['close'] / df['open'], 1)
        df['hpr'] = df['ror'].cumprod()
        df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        f.write(f"Just Holding\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n---------------------------------\n")

        fee = 0.01 / 100

        df['ror_bull'] = np.where((df.Slow_OSC > 0), df.close / df.open - fee, 1)
        df['ror_bear'] = np.where((df.Slow_OSC < 0), df.open / df.close - fee, 1)
        df['hpr'] = df['ror_bull'].cumprod() * df['ror_bear'].cumprod()
        df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        df['trading'] = np.where((df['ror_bull'] == 1) & (df['ror_bear'] == 1), 0, 1)
        df['win'] = np.where((df['ror_bull'] > 1) | (df['ror_bear'] > 1), 1, 0)
        df['total_trading'] = df['trading'].cumsum()
        df['total_win'] = df['win'].cumsum()
        df['승률'] = df['total_win'] / df['total_trading'] * 100
        f.write(f"Stochastic\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n승률: {df['승률'][-2]}\n---------------------------------\n")

        if df['승률'][-2] < 50:
            count_win += 1
        if df['dd'].max() > 25:
            count_dd += 1

        #  df.to_excel(f"{ticker}-Stochastic(50%).xlsx")
        print("\n")
        f.write("\n")
    f.write(f"승률50 이하: {count_win} MDD25 이상: {count_dd}\n")