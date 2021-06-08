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
    EMA = float(df['ema'][-1])
    return EMA

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
    slow_osc_slope = slow_osc - slow_osc.shift(1)
    df['slow_osc'] = slow_osc
    df['slow_osc_slope'] = slow_osc_slope
    stoch_osc = float(df['slow_osc'][-1])
    stoch_slope = float(df['slow_osc_slope'][-1])
    return stoch_osc, stoch_slope

# MACD 계산
def calMACD(df, n_Fast, n_Slow, n_Signal):
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
    df['macd_slope'] = MACDOSC - MACDOSC.shift(1)
    df['macd_osc'] = MACDOSC
    return df['macd_slope'][-1]
    #  return df['macd_osc'][-1]

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

# # MFI 계산
def calMFI(df, period):
    typical_price = (df['close'] + df['high'] + df['low']) / 3 # 대표 주가 계산
    money_flow = typical_price * df['volume'] # 자금 흐름 계산
    # 양의 자금 흐름과 음의 자금 흐름 계산
    positive_flow = []
    negative_flow = []
    for i in range(1, len(typical_price)):
        # 현재 대표 주가가 어제 대표 주가보다 높을 때
        if typical_price[i] > typical_price[i - 1]:
            positive_flow.append(money_flow[i - 1])
            negative_flow.append(0)
        # 현재 대표 주가가 어제 대표 주가보다 낮을 때
        elif typical_price[i] < typical_price[i - 1]:
            negative_flow.append(money_flow[i - 1])
            positive_flow.append(0)
        # 대표 주가의 변동이 없을 때
        else:
            positive_flow.append(0)
            negative_flow.append(0)
    # 지정된 기간 내 양의 자금 흐름과 음의 자금 흐름 계산
    positive_mf = []
    negative_mf = []

    # 기간내 모든 양의 자금흐름
    for i in range(period - 1, len(positive_flow)):
        positive_mf.append(sum(positive_flow[i + 1 - period : i + 1]))

    # 기간내 모든 음의 자금흐름
    for i in range(period - 1, len(negative_flow)):
        negative_mf.append(sum(negative_flow[i + 1 - period : i + 1]))
    # 자금 흐름 지수 (MFI) 계산
    mfi = 100 * (np.array(positive_mf) / (np.array(positive_mf) + np.array(negative_mf)))
    mfi_slope = mfi[-1] - mfi[-2]
    return mfi_slope

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
