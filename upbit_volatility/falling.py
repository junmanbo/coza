import pyupbit
import time

#  def is_bullish(ticker, price):
#      df = pyupbit.get_ohlcv(ticker, "minute1")
#      yesterday = df.iloc[-2]
#      bullish = price - yesterday['close']
#      result = ''
#      if bullish > 0:
#          result = True
#      elif bullish < 0:
#          result = False
#      return result

def is_bullish(ticker):
    df = pyupbit.get_ohlcv(ticker, "minute1")
    close = df['close']
    ma = close.rolling(window=60).mean()
    return ma[-2]

tickers = pyupbit.get_tickers("KRW")
for ticker in tickers:
    price = pyupbit.get_current_price(ticker)
    if price > is_bullish(ticker):
        print(f"{ticker}는 지금 상승장입니다.")
    elif price < is_bullish(ticker):
        print(f"{ticker}는 지금 하락장입니다.")
    time.sleep(0.1)
