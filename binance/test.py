import ccxt
#
#  with open("binance.txt") as f:
#      lines = f.readlines()
#      api_key = lines[0].strip()
#      secret = lines[1].strip()
#
#  binance = ccxt.binance({
#      'apiKey': api_key,
#      'secret': secret,
#      'enableRateLimit': True,
#      'options': {
#          'defaultType': 'future',
#      }
#  })
binance = ccxt.binance

tickers = ('TRX/USDT', 'QTUM/USDT', 'XRP/USDT', 'EOS/USDT')

symbols = list(tickers)

temp = {}

for symbol in symbols:
    price1 = ccxt.binance().fetch_ticker(symbol)['ask'] # 매도 1호가(현재가)
    amount = 1500 / price1 # 매수할 코인 개수
    temp[symbol] = {}
    temp[symbol]['amount'] = amount
    temp[symbol]['hold'] = False
    print(temp[symbol]['hold'])
