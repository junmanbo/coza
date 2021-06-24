#!/usr/bin/env python

import ccxt
import pandas as pd
import matplotlib.pyplot as plt
from mpl_finance import candlestick_ohlc
import matplotlib.dates as mdates
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

tickers = ['LUNA/USDT', 'ZEN/USDT', 'BTC/USDT', 'ETH/USDT', 'ETC/USDT', 'BNB/USDT', 'XRP/USDT', 'LTC/USDT', 'LINK/USDT', 'DOT/USDT', 'QTUM/USDT']

#  for symbol in symbols:
#      df = getOHLCV(symbol, '1d')
#      stoch_osc_yes, stoch_osc_to = indi.calStochastic(df, 12, 5, 5)
#      macd = indi.cal_macd(df, 7, 14, 5)
#      print(f'코인: {symbol}\nStochastic: {stoch_osc_yes} {stoch_osc_to} MACD: {macd}')

avg_profit = 0
for ticker in tickers:
    df = getOHLCV(ticker, '1d')
    min_price = df['low'].min()
    line = min_price * 0.9

    # Volume EMA
    vol_ema_short = df.volume.ewm(span=7).mean()
    vol_ema_long = df.volume.ewm(span=14).mean()

    # MACD
    ema_short = df.close.ewm(span=7).mean()
    ema_long = df.close.ewm(span=14).mean()
    macd = ema_short - ema_long
    signal = macd.ewm(span=10).mean()
    macdhist = macd - signal
    df = df.assign(ema_long=ema_long, ema_short=ema_short, vol_ema_long=vol_ema_long, vol_ema_short=vol_ema_short, macd=macd).dropna()
    df['number'] = df.index.map(mdates.date2num)
    ohlc = df[['number', 'open', 'high', 'low', 'close']]

    # Stochastic
    ndays_high = df.high.rolling(window=12, min_periods=1).max()
    ndays_low = df.low.rolling(window=12, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=5).mean()
    slow_d = slow_k.ewm(span=5).mean()
    slow_osc = slow_k - slow_d
    df = df.assign(fast_k=fast_k, slow_k=slow_k, slow_d=slow_d, slow_osc=slow_osc).dropna()

    # MFI (Money Flow Index)
    df['TP'] = (df['high'] + df['low'] + df['close']) / 3
    df['PMF'] = 0
    df['NMF'] = 0
    for i in range(len(df.close)-1):
        if df.TP.values[i] < df.TP.values[i+1]:
            df.PMF.values[i+1] = df.TP.values[i+1] * df.volume.values[i+1]
            df.NMF.values[i+1] = 0
        else:
            df.NMF.values[i+1] = df.TP.values[i+1] * df.volume.values[i+1]
            df.PMF.values[i+1] = 0
    df['MFR'] = df.PMF.rolling(window=10).sum() / df.NMF.rolling(window=10).sum()
    df['MFI10'] = 100 - 100 / (1+df['MFR'])

    plt.figure(figsize=(27,20))
    p1 = plt.subplot(3, 1, 1)
    plt.title(f'Swing Trading ({ticker})')
    plt.grid(True)
    candlestick_ohlc(p1, ohlc.values, width=0.5, colorup='red', colordown='blue')

    p1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.plot(df.number, df['ema_short'], color='m', label='EMA Short')
    plt.plot(df.number, df['ema_long'], color='g', label='EMA Long')

    hold = 'wait'
    price = 1
    money = 1000000 # 단위 (원)
    start_money = money
    fee = 0.2 / 100
    check_price = 1

    for i in range(1, len(df.close)):
        # 롱
        if df.slow_osc.values[i-1] < -1 and df.slow_osc.values[i] > 1 and df.macd.values[i] > 0 and hold == 'wait':
            plt.plot(df.number.values[i], line, 'r^')
            hold = 'long'
            price = df.close.values[i]

        elif hold == 'long' and df.slow_osc.values[i-1] > 0 and df.slow_osc.values[i] < 0 and df.MFI10.values[i] > 70:
            plt.plot(df.number.values[i], line, 'cv')
            profit = (df.close.values[i] - price) / price - fee
            realized_profit = money * profit
            money += realized_profit
            hold = 'wait'
            print(f'(롱) Stochastic 반환점 실현이익: {realized_profit:.2f} 수익률: {profit*100:.2f}%\n현재잔액: {money:.2f}원\n')

        elif hold == 'long' and df.macd.values[i] < 0:
            plt.plot(df.number.values[i], line, 'cv')
            profit = (df.close.values[i] - price) / price - fee
            realized_profit = money * profit
            money += realized_profit
            hold = 'wait'
            print(f'(롱) MACD 반환점: {realized_profit:.2f} 수익률: {profit*100:.2f}%\n현재잔액: {money:.2f}원\n')

        elif hold == 'long' and i == len(df.close) - 1:
            plt.plot(df.number.values[i], line, 'cv')
            profit = (df.close.values[i] - price) / price - fee
            realized_profit = money * profit
            money += realized_profit
            hold = 'wait'
            print(f'(롱) 마지막 날: {realized_profit:.2f} 수익률: {profit*100:.2f}%\n현재잔액: {money:.2f}원\n')

        # 숏
        elif df.slow_osc.values[i-1] > 1 and df.slow_osc.values[i] < -1 and df.macd.values[i] < 0 and hold == 'wait':
            plt.plot(df.number.values[i], line, 'bv')
            hold = 'short'
            price = df.close.values[i]

        elif hold == 'short' and df.slow_osc.values[i-1] < 0 and df.slow_osc.values[i] > 0 and df.MFI10.values[i] < 30:
            plt.plot(df.number.values[i], line, 'c^')
            profit = (price - df.close.values[i]) / df.close.values[i] - fee
            realized_profit = money * profit
            money += realized_profit
            hold = 'wait'
            print(f'(숏) Stochastic 반환점 실현이익: {realized_profit:.2f} 수익률: {profit*100:.2f}%\n현재잔액: {money:.2f}원\n')

        elif hold == 'short' and df.macd.values[i] > 0:
            plt.plot(df.number.values[i], line, 'c^')
            profit = (price - df.close.values[i]) / df.close.values[i] - fee
            realized_profit = money * profit
            money += realized_profit
            hold = 'wait'
            print(f'(숏) MACD 반환점 실현이익: {realized_profit:.2f} 수익률: {profit*100:.2f}%\n현재잔액: {money:.2f}원\n')

        elif hold == 'short' and i == len(df.close) - 1:
            plt.plot(df.number.values[i], line, 'c^')
            profit = (price - df.close.values[i]) / df.close.values[i] - fee
            realized_profit = money * profit
            money += realized_profit
            hold = 'wait'
            print(f'(숏) 마지막 날: {realized_profit:.2f} 수익률: {profit*100:.2f}%\n현재잔액: {money:.2f}원\n')

    profit = (money - start_money) / start_money * 100
    print(f'{ticker} 시작금액: {start_money:.2f} -> 최종잔액: {money:.2f} 총 수익률: {profit:.2f}%\n')
    plt.legend(loc='best')

    p2 = plt.subplot(3, 1, 2)
    plt.grid(True)
    p2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.plot(df.number, df['MFI10'], color='r', label='MFI10')
    plt.yticks([0, 30, 70, 100])
    plt.legend(loc='best')

    p3 = plt.subplot(3, 1, 3)
    plt.grid(True)
    p3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.plot(df.number, df['slow_k'], color='c', label='%K')
    plt.plot(df.number, df['slow_d'], color='k', label='%D')
    plt.yticks([0, 20, 80, 100])
    plt.legend(loc='best')
    plt.show()

    avg_profit += profit
    time.sleep(0.5)

avg_profit /= len(tickers)
print(f'평균 수익률: {avg_profit:.2f}%')
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
