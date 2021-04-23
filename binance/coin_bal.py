import ccxt
import pprint

with open("binance.txt") as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret = lines[1].strip()

#  binance = ccxt.binance({
#      'apiKey': api_key,
#      'secret': secret,
#      'enableRateLimit': True,
#      'options': {
#          'defaultType': 'future',
#      }
#  })
#
#  symbol = "BTC/USDT"
#  #  a = symbol.find('/')
#  #  symbol = symbol[:a]
#  print(symbol)
#  coin_balance = binance.fetch_balance(params={"type": "future"})['USDT']
#  #  [symbol[:symbol.find('/')]]['used']
#  print(coin_balance)
#
#  symbol = 'ADA/USDT'
#  market = binance.market(symbol)
#  print(market)
#  leverage = 1
#
#  response = binance.fapiPrivate_post_leverage({
#      'symbol': market['id'],
#      'leverage': leverage,
#  })
#
#  print(response)
#  #  binance.set_sandbox_mode(True)  # comment if you're not using the testnet
#  markets = binance.load_markets()
#  binance.verbose = True  # debug output
#
#  balance = binance.fetch_balance()
#  positions = balance['info']['positions']
#  pprint(positions)
symbols = ["BTC/USDT", "ETH/USDT", "TRX/USDT"]
while True:
    for symbol in symbols:
        print(symbol)
        symbols = symbols.clear()
        symbols = [symbol]
