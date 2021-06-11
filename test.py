#!/usr/bin/env python

import ccxt
import pprint

# 거래소 설정
with open('./Api/binance.txt') as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret = lines[1].strip()

# 기본 옵션: 선물
binance = ccxt.binance({
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    }
})

#  symbol = 'BTC/USDT'
#  bid_ask = binance.fetch_bids_asks(symbols=symbol)
#  for coin in bid_ask:
#      if coin == symbol:
#          ask = coin['ask']
#          print(bid_ask, coin, ask)



#  balance = binance.fetch_balance()
#  positions = balance['info']['positions']
#  characters = "/"
#
#  for position in positions:
#      symbol = ''.join( x for x in symbol if x not in characters )
#      if position["symbol"] == symbol:
#          print(symbol)
#          pprint.pprint(position['entryPrice'])
#          if float(position['entryPrice']) == 0:
#              print('none')
#          else:
#              print('yes')
