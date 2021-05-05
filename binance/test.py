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

for symbol in symbols:
    #  high = binance.fetch_ticker(symbol)['high']
    #  low = binance.fetch_ticker(symbol)['low']
    #  print(f"Coin: {symbol} High: {high} Low: {low}")
    symbols.remove(symbol)
    print(symbols)
