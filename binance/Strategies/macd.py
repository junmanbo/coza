import pandas_datareader.data as web
import pandas as pd
import datetime
import ccxt

binance = ccxt.binance()
symbol = "ETH/USDT"

def cal_MACD(symbol, m_NumFast=12, m_NumSlow=26, m_NumSignal=9):
    ohlcv = binance.fetch_ohlcv(symbol, '1d')
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    df['EMAFast'] = df['close'].ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
    df['EMASlow'] = df['close'].ewm( span = m_NumSlow, min_periods = m_NumSlow - 1 ).mean()
    df['MACD'] = df['EMAFast'] - df['EMASlow']
    df['MACD_Signal'] = df['MACD'].ewm( span = m_NumSignal, min_periods = m_NumSignal - 1 ).mean()
    df['MACD_OSC'] = df['MACD'] - df['MACD_Signal']
    bullish = df['MACD_OSC'][-1] - df['MACD_OSC'][-2]
    return bullish
print(cal_MACD(symbol))
