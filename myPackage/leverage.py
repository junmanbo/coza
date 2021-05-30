import ccxt

with open("./Api/binance.txt") as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret = lines[1].strip()

binance = ccxt.binance({
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    }
})

tickers = binance.load_markets().keys()
symbols = list(tickers)
print('Loading markets from', binance.id)
binance.load_markets()
print('Loaded markets from', binance.id)

ex = ['BTC/USDT', 'ETH/USDT', 'FIL/USDT']
for symbol in ex:
    symbols.remove(symbol)

binance.verbose = True
for symbol in symbols:
    market = binance.market(symbol)
    leverage = 10

    response = binance.fapiPrivate_post_leverage({
        'symbol': market['id'],
        'leverage': leverage,
    })
    print(response)
