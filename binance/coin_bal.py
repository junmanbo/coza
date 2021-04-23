import ccxt
import pprint

with open("binance.txt") as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret = lines[1].strip()

binance = ccxt.binance(config={
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
})

symbol = "USDT/USDT"
#  a = symbol.find('/')
#  symbol = symbol[:a]
#  print(symbol)
coin_balance = binance.fetch_balance(params={"type": "future"})[symbol[:symbol.find('/')]]['free']
print(coin_balance)
