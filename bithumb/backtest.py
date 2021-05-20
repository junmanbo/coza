from pybithumb import Bithumb
import pandas as pd
import numpy as np
import time
import openpyxl

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

count_win = 0
count_dd = 0
with open("AnalysisStrategies.txt", 'w') as f:
    tickers = ['BTC', 'ETH', 'LTC', 'ETC', 'XRP', 'BCH', 'QTUM', 'BTG', 'EOS', 'ICX', 'TRX', 'ELF', 'OMG', 'KNC', 'GLM', 'ZIL', 'WAXP', 'POWR', 'LRC', 'STEEM', 'STRAX', 'AE', 'ZRX', 'REP', 'XEM', 'SNT', 'ADA', 'CTXC', 'BAT', 'WTC', 'THETA', 'LOOM', 'WAVES', 'TRUE', 'LINK', 'RNT', 'ENJ', 'VET', 'MTL', 'IOST', 'TMTG', 'QKC', 'HDAC', 'AMO', 'BSV', 'DAC', 'ORBS', 'TFUEL', 'VALOR', 'CON', 'ANKR', 'MIX', 'LAMB', 'CRO', 'FX', 'CHR', 'MBL', 'MXC', 'DVP', 'FCT', 'FNB', 'TRV', 'PCM', 'DAD', 'AOA', 'WOM', 'SOC', 'EM', 'QBZ', 'BOA', 'FLETA', 'SXP', 'COS', 'APIX', 'EL', 'BASIC', 'HIVE', 'XPR', 'FIT']
    #  start_date = '2018-05-01'
    #  end_date = '2021-05-20'
    #  print(f"분석 날짜 {start_date} ~ {end_date}\n")
    for ticker in tickers:
        print(f"코인: {ticker}")
        df = Bithumb.get_candlestick(ticker, chart_intervals="1h")
        calMA(df)
        calStochastic(df)
        calMACD(df)
# 기간 제한
        #  df=df.loc[start_date:end_date]
        f.write(f"코인: {ticker} >>>>>\n\n")

        fee = 0.02 / 100

        df['ror_bull'] = np.where((df.Slow_OSC > 0) & (df.MACD_OSC > 0) & (df.open > df.ma), df.close / df.open - fee, 1)
        df['ror_bear'] = np.where((df.Slow_OSC < 0) & (df.MACD_OSC < 0) & (df.open < df.ma), df.open / df.close - fee, 1)
        df['hpr'] = df.ror_bull.cumprod() * df.ror_bear.cumprod()
        df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        df['trading'] = np.where((df.ror_bull == 1) & (df.ror_bear == 1), 0, 1)
        df['win'] = np.where((df.ror_bull > 1) | (df.ror_bear > 1), 1, 0)
        total_trading = df.trading.cumsum()
        total_win = df.win.cumsum()
        df['승률'] = total_win / total_trading * 100
        f.write(f"stoch+ema+macd\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n승률: {df['승률'][-2]}\n---------------------------------\n")

        if df['승률'][-2] > 80:
            count_win += 1

        if df['dd'].max() > 25:
            count_dd += 1

        #  df.to_excel(f"{ticker}-Stochastic(50%).xlsx")

        time.sleep(0.1)
        print("\n")
        f.write("\n")
    f.write(f"승률 80이상 횟수: {count_win}\nMDD 25이상 횟수: {count_dd}")

