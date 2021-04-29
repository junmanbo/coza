import pandas_datareader.data as web
import pandas as pd
import datetime
import ccxt

binance = ccxt.binance()
symbol = "XMR/USDT"

ohlcv = binance.fetch_ohlcv(symbol, '1d')
df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
df.set_index('datetime', inplace=True)
long = 26
#  df['MACD'] = df['close'].ewm(span = long, min_periods = long-1, adjust=False).mean() - df['close'].ewm(span = long, min_periods = long-1, adjust=False).mean()
#  m_NumFast = 12
#  df['EMAFast'] = df['close'].ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
#  print(df)

#  def calMACD(df, short=12, long=26, signal=9):
#      df['MACD'] = df['close'].ewm(span = long, min_periods = long-1, adjust=False).mean() - df['close'].ewm(span = long, min_periods = long-1, adjust=False).mean()
#      df['MACD_Signal'] = df['MACD'].ewm(span = signal, min_periods = signal-1, adjust=False).mean()
#      df['MACD_OSC'] = df['MACD'] - df['MACD_Signal']
#      return df
#
#  print(calMACD(df))

def cal_MACD(symbol, m_NumFast=12, m_NumSlow=26, m_NumSignal=9):
    ohlcv = binance.fetch_ohlcv(symbol, '1h')
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    df['EMAFast'] = df['close'].ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
    df['EMASlow'] = df['close'].ewm( span = m_NumSlow, min_periods = m_NumSlow - 1 ).mean()
    df['MACD'] = df['EMAFast'] - df['EMASlow']
    df['MACD_Signal'] = df['MACD'].ewm( span = m_NumSignal, min_periods = m_NumSignal - 1 ).mean()
    df['MACD_OSC'] = df['MACD'] - df['MACD_Signal']
    return df['MACD_OSC'][-1]

print(cal_MACD(symbol))
