import ccxt

with open("binance.txt") as f:
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
symbols = tickers
print('Loading markets from', binance.id)
binance.load_markets()
print('Loaded markets from', binance.id)

binance.verbose = True
for symbol in symbols:
    market = binance.market(symbol)
    leverage = 4

    response = binance.fapiPrivate_post_leverage({
        'symbol': market['id'],
        'leverage': leverage,
    })
    print(response)