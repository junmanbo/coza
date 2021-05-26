import numpy as np
import pandas as pd

# OHLCV 데이터 가져오기
def getOHLCV(exchange, symbol, period):
    """
    exchange=거래소
    symbol=코인 티커
    period=기간 (일봉=1d, 4시간봉=4h)
    """
    ohlcv = exchange.fetch_ohlcv(symbol, period)
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    return df

# 지수 이동평균 계산
def calEMA(df, n):
    """
    지수 이동평균 계산
    n = n일의 지수 이동평균
    """
    df['ema'] = df['close'].ewm(span=n).mean()
    return df['ema'][-1]

# Stochastic 계산
def calStochastic(df, n, m, t):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    slow_osc_slope = slow_osc - slow_osc.shift(1)
    df['slow_osc'] = slow_osc
    df['slow_osc_slope'] = slow_osc_slope
    return df['slow_osc'][-1], df['slow_osc_slope'][-1]

# MACD 계산
def calMACD(df, n_Fast, n_Slow, n_Signal):
    EMAFast = df.close.ewm( span = n_Fast, min_periods = n_Fast - 1 ).mean()
    EMASlow = df.close.ewm( span = n_Slow, min_periods = n_Slow - 1 ).mean()
    MACD = EMAFast - EMASlow
    MACDSignal = MACD.ewm( span = n_Signal, min_periods = n_Signal - 1 ).mean()
    MACDOSC = MACD - MACDSignal
    df['macd_osc'] = MACDOSC - MACDOSC.shift(1)
    return df['macd_osc'][-1]

# RSI 계산
def calRSI(df, n):

    df['U'] = np.where(df.close.diff(1) > 0, df.close.diff(1), 0)
    df['D'] = np.where(df.close.diff(1) < 0, df.close.diff(1) * (-1), 0)
    df['AU'] = df['U'].rolling( window=n, min_periods=n).mean()
    df['AD'] = df['D'].rolling( window=n, min_periods=n).mean()
    df['RSI'] = df['AU'] / (df['AD']+df['AU']) * 100
    return df['RSI'][-1]
