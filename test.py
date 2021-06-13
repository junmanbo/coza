#!/usr/bin/env python

import json
import ccxt
import pprint
import time

#  while True:
#      hold = False
#      with open('./Data/binance_short.txt', 'r') as f:
#          data = f.read()
#          check = json.loads(data)
#      for ticker in check.keys():
#          #  ticker['position']
#          #  print(check[ticker]['position'])
#          if check[ticker]['position'] != 'wait':
#              hold = True
#              print(f'current_hold: {hold} Continue')
#      if hold == False:
#          print(f'current_hold: {hold} Stop')
#          break
#      time.sleep(1)

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

symbol = 'XRP/USDT'
bid_ask = binance.fetch_bids_asks(symbols=symbol)
current_price = bid_ask[symbol]['ask']
print(current_price)

#  amount = 10
#  symbol = 'LINK/USDT'
#  current_price = 20
#  quantity = amount / current_price
#  order2 = binance.create_limit_buy_order(symbol, quantity, current_price) # 지정가 매수 주문
#  order = binance.create_limit_sell_order(symbol, quantity, current_price * 3.1)
#  cancel_order = binance.cancel_order(order['id'], symbol)
#
#  stop_loss_params = {'stopPrice': current_price * 0.9, 'reduceOnly': True} # 손절 예약 주문
#  stop_order = binance.create_order(symbol, 'stop', 'sell', quantity, current_price * 0.9, stop_loss_params)

#  take_profit_params = {'stopPrice': current_price * 1.1, 'reduceOnly': True} # 이익실현 예약 주문
#  stop_order = binance.create_order(symbol, 'take_profit', 'sell', quantity, current_price * 1.1, take_profit_params)

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
#  binance.cancel_order()
