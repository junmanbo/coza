from pykrx import stock
import pandas as pd
import numpy as np
import datetime
import time

def calTarget(df):
    df['range'] = (df['고가'] - df['저가']) * (1 - abs(df['시가'] - df['종가']) / (df['고가'] - df['저가']))
    df['t_bull'] = df['시가'] + df['range'].shift(1)
    df['t_bear'] = df['시가'] - df['range'].shift(1)

def calMA(df, fast=5):
    df['ma'] = df['종가'].ewm(span = fast).mean().shift(1)

def calStochastic(df, n=9, m=3, t=3):
    ndays_고가 = df.고가.rolling(window=n, min_periods=1).max()
    ndays_저가 = df.저가.rolling(window=n, min_periods=1).min()
    fast_k = ((df.종가 - ndays_저가) / (ndays_고가 - ndays_저가)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    df['Slow_K'] = slow_k
    df['Slow_OSC'] = slow_osc.shift(1)

def calMACD(df, m_NumFast=5, m_NumSlow=20, m_NumSignal=5):
    df['EMAFast'] = df['종가'].ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
    df['EMASlow'] = df['종가'].ewm( span = m_NumSlow, min_periods = m_NumSlow - 1 ).mean()
    df['MACD'] = df['EMAFast'] - df['EMASlow']
    df['MACD_Signal'] = df['MACD'].ewm( span = m_NumSignal, min_periods = m_NumSignal - 1 ).mean()
    df['MACD_OSC'] = df['MACD'].shift(1) - df['MACD_Signal'].shift(1)


with open("AnlaysisStrategies.txt", 'w') as f:
    #  tickers = stock.get_market_ticker_list("20210506", market="KOSPI")
    tickers = ['000120', '005930', '000660', '051910', '005935', '035420', '207940', '035720', '005380', '006400', '068270', '005490', '000270', '012330', '096770', '028260', '066570', '051900', '105560', '055550', '015760']
    for ticker in tickers:
        df = stock.get_market_ohlcv_by_date('20190803', '20210103', ticker)
        start_date = '20200501' # 시작 날짜
        end_date = '20210101' # 마지막 날짜
        calTarget(df)
        calMA(df)
        calStochastic(df)

        df=df.loc[start_date:end_date]

#  Just Hold
        name = stock.get_market_ticker_name(ticker)
        print(f"분석 기간: {start_date} ~ {end_date}\n종목: {name} >>>\n")
        f.write(f"분석 기간: {start_date} ~ {end_date}\n종목: {name} >>>\n\n")
        f.write(f"{start_date} (시작날) 시가: {df['시가'][0]}\n{end_date} (마지막날) 종가: {df['종가'][-2]}\n")
        df['ror'] = np.where((1>0), df['종가'] / df['시가'], 1)
        df['hpr'] = df['ror'].cumprod()
        df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        f.write(f"단순히 보유하는 전략\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n---------------------------------\n")

        fee = 0.01 / 100
# Calculate Profit
        df['ror_bull'] = np.where((df['고가'] > df['t_bull']) & (df['시가'] > df['ma']), df['종가'] / df['t_bull'] - fee, 1)
        df['hpr'] = df['ror_bull'].cumprod()
        df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        f.write(f"변동성 돌파 전략\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n-----------------------------------------------\n")

        df['ror_bull'] = np.where((df['고가'] > df['t_bull']) & (df['Slow_OSC'] > 0) & (df['시가'] > df['ma']), df['종가'] / df['t_bull'] - fee, 1)
        df['hpr'] = df['ror_bull'].cumprod()
        df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        f.write(f"Stochastic + ema + 변동성 돌파 전략\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n-----------------------------------------------\n")

        df['ror_bull'] = np.where((df['Slow_OSC'] > 0) & (df['시가'] > df['ma']), df['종가'] / df['시가'] - fee, 1)
        df['hpr'] = df['ror_bull'].cumprod()
        df['dd'] = (df['hpr'].cummax() - df['hpr']) / df['hpr'].cummax() * 100
        f.write(f"Stochastic + ema 전략\nHPR: {df['hpr'][-2]}\nMDD: {df['dd'].max()}\n-----------------------------------------------\n\n")
        time.sleep(0.5)
