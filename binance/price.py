import ccxt
import pprint
import pandas as pd

#  print(ccxt.exchanges)
#  exchange = ccxt.binance()
#  binance1 = ccxt.binance ({'id': 'binance1'})

# binance initialize
#  binance = ccxt.binance()
#  markets = binance.load_markets()

# 마켓 개수
#  print(markets.keys())
#  print(len(markets))

# 현재가
#  btc = binance.fetch_ticker("BTC/USDT")
#  pprint.pprint(btc)
#
#  # 분봉 조회
#  btc_ohlcv = binance.fetch_ohlcv("BTC/USDT")
#  df = pd.DataFrame(btc_ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
#  df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
#  df.set_index('datetime', inplace=True)
#  print(df)
#
#  # 일봉 조회
#  btc_ohlcv = binance.fetch_ohlcv("BTC/USDT", '1d')
#  df = pd.DataFrame(btc_ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
#  df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
#  df.set_index('datetime', inplace=True)
#  print(df)
#
#  # 시봉 조회
#  btc_ohlcv = binance.fetch_ohlcv("BTC/USDT", '1h')
#  df = pd.DataFrame(btc_ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
#  df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
#  df.set_index('datetime', inplace=True)
#  print(df)

# 파일로부터 apiKey, Secret 읽기
with open("binance.txt") as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret = lines[1].strip()

# binance 객체 생성
binance = ccxt.binance(config={
    'apiKey': api_key,
    'secret': secret
})

# USDT의 잔고 조회
balance = binance.fetch_balance()
print(balance['USDT'])

# 지정가 주문
#  order = binance.create_limit_buy_order(
#      symbol="XRP/USDT",
#      amount=1,
#      price=1
#  )

symbol = 'XRP/USDT'
type = 'limit'  # or 'market', other types aren't unified yet
side = 'buy'
amount = 1  # your amount
price = 1 # your price
# overrides
#  params = {
#      'stopPrice': 1.3,  # your stop price
#      'type': 'stopLimit',
#  }
order = binance.create_order(symbol, type, side, amount, price, {'trading_agreement': 'agree'})

pprint.pprint(order)
