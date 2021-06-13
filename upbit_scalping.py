#!/usr/bin/env python

import pyupbit
import datetime
import time
import telegram
import json
import logging
import pandas as pd
from myPackage import indicators as indi

# 로깅 설정
logging.basicConfig(filename='./Log/upbit_scalp.log', format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

# telegram 설정
with open('./Api/mybot.txt') as f:
    lines = f.readlines()
    my_token = lines[0].strip()
    chat_id = lines[1].strip()
bot = telegram.Bot(token = my_token)

# 거래소 설정
with open('./Api/upbit.txt') as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret = lines[1].strip()

upbit = pyupbit.Upbit(api_key, secret)

# 코인 정보 저장 파일 불러오기
with open('./Data/upbit_scalp.txt', 'r') as f:
    data = f.read()
    info = json.loads(data)

strategy = 'Scalping'
#  symbols = pyupbit.get_tickers('KRW') # 코인 목록 전체 조회
symbols = ['KRW-BCH', 'KRW-ETC', 'KRW-BTG', 'KRW-QTUM', 'KRW-NEO', 'KRW-LTC', 'KRW-ATOM']

bull_loss = 0.9967 # 롱 포지션 손실률
amount = 500000
start_price = 1
fee = 0.1 / 100

logging.info(f"{strategy} Start")
bot.sendMessage(chat_id=chat_id, text=f"{strategy} Start!")

while True:
    now = datetime.datetime.now()
    time.sleep(0.1)
    for symbol in symbols:
        try:
            current_price = pyupbit.get_current_price(symbol)

            df = pyupbit.get_ohlcv(symbol, interval='minute15')
            stoch_osc = indi.calStochastic(df, 9, 3, 3)[1]
            df = pyupbit.get_ohlcv(symbol, interval='minute1')
            stoch_osc_before, stoch_osc_now = indi.calStochastic(df, 9, 3, 3)
            mfi = indi.cal_mfi(df, 15)

            logging.info(f'코인: {symbol}\nStochastic Before: {stoch_osc_before} Stochastic Now: {stoch_osc_now}\nStochastic 5m: {stoch_osc} MFI: {mfi}')

            # 이익실현 / 손절체크
            if info[symbol]['position'] == 'long' and current_price < info[symbol]['price'] * bull_loss:
                order = upbit.sell_limit_order(symbol, current_price, info[symbol]['quantity'])
                info[symbol]['position'] = 'wait'
                logging.info(f"{symbol} 매도 손절가 도달!")
                bot.sendMessage(chat_id = chat_id, text=f"{symbol} 매도 손절가 도달!")

            # 가격 업데이트
            elif info[symbol]['position'] == 'long' and current_price > info[symbol]['price']:
                info[symbol]['price'] = current_price
                logging.info(f"{symbol} 상승중! 목표가 업데이트")

            # 조건 만족시 Long Position
            elif info[symbol]['position'] == 'wait' and stoch_osc_before < 0 and stoch_osc_now > 0 and stoch_osc > 0 and mfi < 25:
                # 투자를 위한 세팅
                quantity = amount / current_price
                order = upbit.buy_limit_order(symbol, current_price, quantity) # 지정가 매수 주문

                # 매수가, 포지션 상태, 코인 매수 양 저장
                info[symbol]['price'] = current_price
                info[symbol]['position'] = 'long'
                info[symbol]['quantity'] = quantity
                logging.info(f"{symbol} (롱)\n투자금액: ${amount:.2f}")
                bot.sendMessage(chat_id=chat_id, text=f"{strategy} {symbol} (Long)\nAmount: ${amount:.2f}")
            time.sleep(1)

        except Exception as e:
            bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
            logging.error(e)

        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/upbit.txt', 'w') as f:
            f.write(json.dumps(info))
