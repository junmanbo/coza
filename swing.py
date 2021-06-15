#!/usr/bin/env python

import ccxt
import datetime
import time
import telegram
import json
import logging
import pandas as pd
from myPackage import indicators as indi

# 로깅 설정
logging.basicConfig(filename='./Log/binance_swing.log', format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

# telegram 설정
with open('./Api/mybot.txt') as f:
    lines = f.readlines()
    my_token = lines[0].strip()
    chat_id = lines[1].strip()
bot = telegram.Bot(token = my_token)

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

# 코인 정보 저장 파일 불러오기
with open('./Data/binance_swing.txt', 'r') as f:
    data = f.read()
    info = json.loads(data)

# OHLCV 데이터 가져오기
def getOHLCV(symbol, period):
    ohlcv = binance.fetch_ohlcv(symbol, period)
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    return df

strategy = 'Swing'
#  tickers = binance.load_markets().keys() # 목록 전체 조회
symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'DOGE/USDT',
        'XRP/USDT', 'DOT/USDT', 'UNI/USDT', 'ICP/USDT', 'BCH/USDT',
        'LINK/USDT', 'LTC/USDT', 'SOL/USDT', 'MATIC/USDT', 'THETA/USDT',
        'XLM/USDT', 'VET/USDT', 'ETC/USDT', 'FIL/USDT', 'EOS/USDT',
        'TRX/USDT', 'XMR/USDT', 'AAVE/USDT', 'NEO/USDT', 'MKR/USDT',
        'KSM/USDT', 'IOTA/USDT', 'ALGO/USDT', 'ATOM/USDT', 'AVAX/USDT',
        'LUNA/USDT', 'BTT/USDT', 'RUNE/USDT', 'XTZ/USDT', 'COMP/USDT',
        'HBAR/USDT', 'DASH/USDT', 'ZEC/USDT', 'EGLD/USDT', 'XEM/USDT',
        'WAVES/USDT', 'YFI/USDT', 'CHZ/USDT', 'HOT/USDT', 'SUSHI/USDT',
        'ZIL/USDT', 'SNX/USDT', 'MANA/USDT', 'NEAR/USDT', 'ENJ/USDT',
        'HNT/USDT', 'BAT/USDT', 'QTUM/USDT', 'ZEN/USDT', 'DGB/USDT',
        'GRT/USDT', 'ONE/USDT', 'ONT/USDT', 'BAKE/USDT', 'SC/USDT']

# 보유하고 있는 코인 갯수
current_hold = 0
for symbol in symbols:
    if info[symbol]['position'] != 'wait':
        current_hold += 1

total_hold = 5 # 투자할 코인 총 갯수
bull_loss = 0.9 # 롱 포지션 손실률
bear_loss = 2 - bull_loss # 숏 포지션 손실률
leverage = 4
fee = 0.2 / 100

logging.info(f"{strategy}\n현재보유: {current_hold}개\n투자할 코인: {total_hold-current_hold}개")
bot.sendMessage(chat_id=chat_id, text=f"{strategy}\nHolding: {current_hold}")

while True:
    now = datetime.datetime.now()
    time.sleep(1)

    if now.hour % 4 == 0 and now.minute == 59 and 0 <= now.second <= 5:
        # 1코인 1번당 투자 금액
        total_balance = binance.fetch_balance()['USDT']['total']
        amount = total_balance * leverage / total_hold
        logging.info('4hourly checking')
        for symbol in symbols:
            try:
                current_price = binance.fetch_ticker(symbol)['close'] # 현재가 조회

                df = getOHLCV(symbol, '1d')
                stoch_osc_yes, stoch_osc_to = indi.calStochastic(df, 12, 5, 5)
                mfi = indi.cal_mfi(df, 14)
                ema_yes, ema_to = indi.calEMA(df, 7)

                logging.info(f'코인: {symbol}\nStochastic: {stoch_osc_yes} {stoch_osc_to} MFI: {mfi} EMA: {ema_yes} {ema_to}')

                if info[symbol]['position'] == 'wait' and current_hold < total_hold:
                    if stoch_osc_yes < 0 and stoch_osc_to > 0 and mfi < 50 and ema_yes < ema_to:
                        quantity = amount / current_price
                        order = binance.create_limit_buy_order(symbol, quantity, current_price) # 지정가 매수 주문
                        stop_loss_params = {'stopPrice': current_price * bull_loss, 'reduceOnly': True} # 손절 예약 주문
                        stop_order = binance.create_order(symbol, 'stop', 'sell', quantity, current_price * bull_loss, stop_loss_params)

                        # 매수가, 포지션 상태, 코인 매수 양 저장
                        info[symbol]['price'] = current_price
                        info[symbol]['start_price'] = current_price
                        info[symbol]['position'] = 'long'
                        info[symbol]['quantity'] = quantity
                        current_hold += 1
                        logging.info(f"{symbol} (롱)\n투자금액: ${amount:.2f}\n현재보유: {current_hold}개\n주문: {order}")
                        bot.sendMessage(chat_id=chat_id, text=f"{strategy} {symbol} (Long)\nAmount: ${amount:.2f}\nHolding: {current_hold}")

                    elif stoch_osc_yes > 0 and stoch_osc_to < 0 and mfi > 80 and ema_yes > ema_to:
                        quantity = amount / current_price
                        order = binance.create_limit_sell_order(symbol, quantity, current_price) # 지정가 매도 주문
                        stop_loss_params = {'stopPrice': current_price * bear_loss, 'reduceOnly': True} # 손절 예약 주문
                        stop_order = binance.create_order(symbol, 'stop', 'buy', quantity, current_price * bear_loss, stop_loss_params)

                        # 매수가, 포지션 상태, 코인 매수 양 저장
                        info[symbol]['price'] = current_price
                        info[symbol]['start_price'] = current_price
                        info[symbol]['position'] = 'short'
                        info[symbol]['quantity'] = quantity
                        current_hold += 1
                        logging.info(f"{symbol} (숏)\n투자금액: ${amount:.2f}\n현재보유: {current_hold}개\n주문: {order}")
                        bot.sendMessage(chat_id=chat_id, text=f"{strategy} {symbol} (Short)\nAmount: ${amount:.2f}\nHolding: {current_hold}")

                elif info[symbol]['position'] == 'long':
                    if df.low.values[-1] < info[symbol]['price'] * bull_loss:
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        profit = (info[symbol]['price'] * bull_loss - info[symbol]['start_price']) / info[symbol]['start_price'] * 100
                        logging.info(f"{symbol} (롱) 손절! 수익률: {profit:.2f}%")
                        bot.sendMessage(chat_id = chat_id, text=f"{symbol} (롱) 손절! 수익률: {profit:.2f}%")

                    elif stoch_osc_yes > 0 and stoch_osc_to < 0 and mfi > 60:
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        time.sleep(2)
                        order = binance.create_limit_sell_order(symbol, info[symbol]['quantity'], current_price) # 지정가 매도 주문
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        profit = (current_price - info[symbol]['start_price']) / info[symbol]['start_price'] * 100
                        logging.info(f"{symbol} (롱) 반환점 도달! 수익률: {profit:.2f}%")
                        bot.sendMessage(chat_id = chat_id, text=f"{symbol} (롱) 반환점 도달! 수익률: {profit:.2f}%")

                    elif current_price > info[symbol]['price']:
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        time.sleep(2)
                        info[symbol]['price'] = current_price
                        stop_loss_params = {'stopPrice': current_price * bull_loss, 'reduceOnly': True} # 손절 예약 주문
                        stop_order = binance.create_order(symbol, 'stop', 'sell', info[symbol]['quantity'], current_price * bull_loss, stop_loss_params)
                        logging.info(f"{symbol} (롱) + 진행중! 본절로스 갱신")
                        bot.sendMessage(chat_id = chat_id, text=f"{symbol} (롱) + 진행중! 본절로스 갱신")

                elif info[symbol]['position'] == 'short':
                    if df.high.values[-1] > info[symbol]['price'] * bear_loss:
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        profit = (info[symbol]['start_price'] - info[symbol]['price'] * bear_loss) / (info[symbol]['price'] * bear_loss) * 100
                        logging.info(f"{symbol} (숏) 손절! 수익률: {profit:.2f}%")
                        bot.sendMessage(chat_id = chat_id, text=f"{symbol} (숏) 손절! 수익률: {profit:.2f}%")

                    elif stoch_osc_yes < 0 and stoch_osc_to > 0 and mfi < 70:
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        time.sleep(2)
                        order = binance.create_limit_buy_order(symbol, info[symbol]['quantity'], current_price) # 지정가 매수 주문
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        profit = (info[symbol]['start_price'] - current_price) / current_price * 100
                        logging.info(f"{symbol} (숏) 반환점 도달! 수익률: {profit:.2f}%")
                        bot.sendMessage(chat_id = chat_id, text=f"{symbol} (숏) 반환점 도달! 수익률: {profit:.2f}%")

                    elif current_price < info[symbol]['price']:
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        time.sleep(2)
                        info[symbol]['price'] = current_price
                        stop_loss_params = {'stopPrice': current_price * bear_loss, 'reduceOnly': True} # 손절 예약 주문
                        stop_order = binance.create_order(symbol, 'stop', 'buy', info[symbol]['quantity'], current_price * bear_loss, stop_loss_params)
                        logging.info(f"{symbol} (숏) + 진행중! 본절로스 갱신")
                        bot.sendMessage(chat_id = chat_id, text=f"{symbol} (숏) + 진행중! 본절로스 갱신")

            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
                logging.error(e)
            time.sleep(0.5)

        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/binance_swing.txt', 'w') as f:
            f.write(json.dumps(info))

