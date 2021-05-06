import ccxt
import pandas as pd
import datetime
import time

#  def calStochastic(m_Df, cName, m_Period, m_Ma, strFk, strFd, strSk, strSd):
#      max5 = m_Df[cName].rolling(window=m_Period).max()
#      min5 = m_Df[cName].rolling(window=m_Period).min()
#      max5.fillna(0)
#      min5.fillna(0)
#      m_Df[strFk] = (((m_Df[cName] - min5) / (max5 - min5)) * 100).round(2)
#      fastD = pd.DataFrame(m_Df['FastK'].rolling(window=m_Ma).mean()).round(2)
#      m_Df.insert(len(m_Df.columns), strFd, fastD)
#      # Slow Stochastic (슬로우 스토캐스틱 Slow%K3)
#      slowK = pd.DataFrame(m_Df.columns['FastD'].rolling(window=m_Ma).mean()).round(2)
#      m_Df.insert(len(m_Df.columns), strSk, slowK)
#      # Slow Stochastic (슬로우 스토캐스틱 Slow%D3)
#      slowD = pd.DataFrame(m_Df[strSk].rolling(window=m_Ma).mean()).round(2)
#      m_Df.insert(len(m_Df.columns), strSd, slowD)
#      return m_Df

def Stochastic(df, n=5, m=3, t=3):
    # 입력받은 값이 dataframe 이라는 것을 정의해줌
    df = pd.DataFrame(df)

    # n일중 최고가
    ndays_high = df.high.rolling(window=n, min_periods=1).max()

    # n일중 최저가
    ndays_low = df.low.rolling(window=n, min_periods=1).min()

    # Fast%K 계산
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100

    # Fast%D (=Slow%K) 계산
    slow_k = fast_k.ewm(span=m).mean()

    # Slow%D 계산
    slow_d = slow_k.ewm(span=t).mean()

    # Stochastic Slow Signal (차이값)
    slow_signal = slow_k - slow_d

    # dataframe에 행 추가
    df = df.assign(fast_k=fast_k, fast_d=slow_k, slow_k=slow_k, slow_d=slow_d, slow_signal=slow_signal)

    return df


binance = ccxt.binance()
tickers = ['BTC/USDT', 'BCH/USDT']
symbols = list(tickers)

for symbol in symbols:
    ohlcv = binance.fetch_ohlcv(symbol, '1d')
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)

    df = Stochastic(df)
    print(df)