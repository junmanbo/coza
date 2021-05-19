import ccxt
import pandas as pd

# with open("binance.txt") as f:
#     lines = f.readlines()
#     api_key = lines[0].strip()
#     secret = lines[1].strip()

binance = ccxt.binance({
   #  'apiKey': api_key,
   #  'secret': secret,
   #  'enableRateLimit': True,
   #  'options': {
   #      'defaultType': 'future',
   #  }
})
symbols = ['TRX/USDT', 'QTUM/USDT', 'BTC/USDT', 'ETH/USDT']

# Stochastic Slow Oscilator 값 계산
def calStochastic(df, n=9, m=5, t=3):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    df['slow_osc'] = slow_k - slow_d
    return df['slow_osc'][-1]

for symbol in symbols:
    ohlcv = binance.fetch_ohlcv(symbol, '1d')
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    calStochastic(df)
    print(symbol)
    print(df)
    print(calStochastic(df))
