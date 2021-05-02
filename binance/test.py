# import ccxt

# with open("binance.txt") as f:
#     lines = f.readlines()
#     api_key = lines[0].strip()
#     secret = lines[1].strip()

# exchange = ccxt.binance({
#     'apiKey': api_key,
#     'secret': secret,
#     'enableRateLimit': True,
#     'options': {
#         'defaultType': 'future',
#     }
# })
tickers = ('TRX/USDT', 'QTUM/USDT', 'XRP/USDT', 'EOS/USDT')

symbols = list(tickers)
#
#  temp = {}
#
#  for symbol in symbols:
#      price1 = ccxt.binance().fetch_ticker(symbol)['ask'] # 매도 1호가(현재가)
#      amount = 1500 / price1 # 매수할 코인 개수
#      temp[symbol] = {}
#      temp[symbol]['amount'] = amount
#      temp[symbol]['hold'] = False
#      print(temp[symbol]['hold'])
# symbol = 'TRX/USDT'
# positions = exchange.private_get_position()
# exchange.private_post_order_closeposition({'symbol': position['symbol']})
total_hold = 2
n = 2
temp = {'TRX/USDT': {'hold': True}, 'QTUM/USDT': {'hold': False}, 'XRP/USDT': {'hold': True}, 'EOS/USDT': {'hold': False}}
if total_hold == 2 and n == 2:
    symbols.clear()
    for symbol in tickers:
        if temp[symbol]['hold'] == True:
            symbols.append(symbol)
    n = 15
    print(n, symbols)

elif total_hold < 2 and n == 15:
    symbols.clear()
    symbols = list(tickers)
    n = 2
    print(n, symbols)