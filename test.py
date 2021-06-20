#!/usr/bin/env python

import json
import ccxt
import pprint
import time
import pandas as pd
from myPackage import indicators as indi

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

#  # 거래소 설정
#  with open('./Api/binance.txt') as f:
#      lines = f.readlines()
#      api_key = lines[0].strip()
#      secret = lines[1].strip()

# 기본 옵션: 선물
binance = ccxt.binance({
    #  'apiKey': api_key,
    #  'secret': secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    }
})

# OHLCV 데이터 가져오기
def getOHLCV(symbol, period):
    ohlcv = binance.fetch_ohlcv(symbol, period)
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    return df

symbols = ['XMR/USDT', 'LUNA/USDT', 'ZEN/USDT', 'HBAR/USDT', 'ZEC/USDT']

for symbol in symbols:
    df = getOHLCV(symbol, '1d')
    stoch_osc_yes, stoch_osc_to = indi.calStochastic(df, 12, 5, 5)
    macd = indi.cal_macd(df, 7, 14, 5)
    print(f'코인: {symbol}\nStochastic: {stoch_osc_yes} {stoch_osc_to} MACD: {macd}')

#  bid_ask = binance.fetch_bids_asks(symbols=symbol)
#  current_price = bid_ask[symbol]['ask']
#  print(current_price)

#  position = binance.fetch_positions(symbol)
#  print(position)
#  binance.fetch_isolated_positions(symbol)

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
