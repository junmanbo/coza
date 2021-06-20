import numpy as np
import pandas as pd
import datetime
import openpyxl

# 지수 이동평균 계산
def calEMA(df, n):
    """
    지수 이동평균 계산
    n: n일의 지수 이동평균
    """

    df['ema'] = df['close'].ewm(span=n).mean()
    EMA_yes = float(df.ema.values[-2])
    EMA_to = float(df.ema.values[-1])
    return EMA_yes, EMA_to

def cal_vol_ema(df, n):
    """
    거래량 지수 이동평균 계산
    n: n일의 지수 이동평균
    """

    df['vol_ema'] = df['close'].ewm(span=n).mean()
    vol_ema = float(df.vol_ema.values[-1])
    return vol_ema

# Stochastic 계산
def calStochastic(df, n, m, t):
    """
    df = dataframe
    n = 기간
    m = %k
    t = %d
    보통 (9,3,3) (12,5,5) 이용
    """

    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    df['slow_osc'] = slow_osc
    return df.slow_osc.values[-2], df.slow_osc.values[-1]

# MACD 계산
def cal_macd(df, n_Fast, n_Slow, n_Signal):
    """
    df = dataframe
    n_Fast = 단기추세
    n_Slow = 장기추세
    n_Signal = 신호
    보통 (12, 26, 9) (5, 20, 5) 이용
    """

    EMAFast = df.close.ewm( span = n_Fast, min_periods = n_Fast - 1 ).mean()
    EMASlow = df.close.ewm( span = n_Slow, min_periods = n_Slow - 1 ).mean()
    MACD = EMAFast - EMASlow
    MACDSignal = MACD.ewm( span = n_Signal, min_periods = n_Signal - 1 ).mean()
    MACDOSC = MACD - MACDSignal
    df['macd'] = MACD
    df['macd_osc'] = MACDOSC
    return df.macd.values[-1]

# RSI 계산
def calRSI(df, n):
    """
    과매수 과매도 판단 (70이상 과매수 / 30이하 과매도)
    n = 기간
    """

    df['U'] = np.where(df.close.diff(1) > 0, df.close.diff(1), 0)
    df['D'] = np.where(df.close.diff(1) < 0, df.close.diff(1) * (-1), 0)
    df['AU'] = df['U'].rolling( window=n, min_periods=n).mean()
    df['AD'] = df['D'].rolling( window=n, min_periods=n).mean()
    df['RSI'] = df['AU'] / (df['AD']+df['AU']) * 100
    return df['RSI'][-1]

# MFI (Money Flow Index)
def cal_mfi(df, n):
    """
    Money Flow Index
    n = 기간
    """
    df['TP'] = (df['high'] + df['low'] + df['close']) / 3
    df['PMF'] = 0
    df['NMF'] = 0
    for i in range(len(df.close)-1):
        if df.TP.values[i] < df.TP.values[i+1]:
            df.PMF.values[i+1] = df.TP.values[i+1] * df.volume.values[i+1]
            df.NMF.values[i+1] = 0
        else:
            df.NMF.values[i+1] = df.TP.values[i+1] * df.volume.values[i+1]
            df.PMF.values[i+1] = 0
    df['MFR'] = df.PMF.rolling(window=n).sum() / df.NMF.rolling(window=n).sum()
    df['MFI'] = 100 - 100 / (1+df['MFR'])
    return df.MFI.values[-1]

def saveHistory(strategy, symbol, position, amount, rate_profit):
    """
    strategy = 전략 이름
    symbol = 코인 심볼
    position = 현재 포지션 상태
    amount = 투자 금액
    rate_profit = 수익률 (1.5% -> 1.5)
    """

    now = datetime.datetime.today()
    fee = 0.1 / 100 # 사고 팔고 0.05% 씩 두 번 계산
    rate_profit = rate_profit / 100
    realized_profit = amount * (rate_profit - fee)
    win = 0
    if realized_profit > 0:
        win = 1

    date = [str(now.year)+"-"+str(now.month)+"-"+str(now.day)]
    index = pd.to_datetime(date)

    df = pd.read_excel(io='./Data/coin.xlsx', index_col='date')
    new_data = [ (strategy, symbol.split('/')[0], position, amount, rate_profit, realized_profit, win) ]
    dfNew = pd.DataFrame(data=new_data, columns=df.columns, index=index)

    #append one dataframe to othher
    df = df.append(dfNew)
    print(df)
    df.to_excel('./Data/coin.xlsx', index_label='date')
