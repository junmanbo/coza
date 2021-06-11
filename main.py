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
logging.basicConfig(filename='./Log/binance_short.log', format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

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
with open('./Data/binance_short.txt', 'r') as f:
    data = f.read()
    info = json.loads(data)

# OHLCV 데이터 가져오기
def getOHLCV(symbol, period):
    ohlcv = binance.fetch_ohlcv(symbol, period)
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    return df

strategy = 'Short-term'
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

total_hold = 10 # 투자할 코인 총 갯수
bull_profit = 1.022 # 롱 포지션 수익률
bull_loss = 0.96 # 롱 포지션 손실률
bear_profit = 0.978 # 숏 포지션 수익률
bear_loss = 1.04 # 숏 포지션 손실률
leverage = 13

logging.info(f"{strategy}\n현재보유: {current_hold}개\n투자할 코인: {total_hold-current_hold}개")
bot.sendMessage(chat_id=chat_id, text=f"{strategy}\nHolding: {current_hold}")

while True:
    now = datetime.datetime.now()
    time.sleep(1)

    if now.hour == 9 and now.minute == 0 and 0 <= now.second <= 5:
        # 1코인 1번당 투자 금액
        total_balance = binance.fetch_balance()['USDT']['total']
        amount = total_balance * leverage / total_hold
        logging.info('Daily Checking')
        for symbol in symbols:
            try:
                current_price = binance.fetch_ticker(symbol)['close'] # 현재가 조회

                df = getOHLCV(symbol, '1d')
                stoch_osc = indi.calStochastic(df, 12, 5, 5)[1]
                macd_osc = indi.calMACD(df, 14, 30, 10)

                logging.info(f'코인: {symbol}\nStochastic: {stoch_osc} MACD OSC: {macd_osc}')

                # 이익실현 / 손절체크
                if info[symbol]['position'] == 'long':
                    if df['high'][-2] > info[symbol]['price'] * bull_profit or df['low'][-2] < info[symbol]['price'] * bull_loss:
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        logging.info(f"{symbol} (롱) 취소주문: {cancel_order}")
                        bot.sendMessage(chat_id = chat_id, text=f"{symbol} (롱) 성공 or 실패?")

                elif info[symbol]['position'] == 'short':
                    if df['low'][-2] < info[symbol]['price'] * bear_profit or df['high'][-2] > info[symbol]['price'] * bear_loss:
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        logging.info(f"{symbol} (숏) 취소주문: {cancel_order}")
                        bot.sendMessage(chat_id = chat_id, text=f"{symbol} (숏) 성공 or 실패?")

                # 매일 오전 9시 전부 청산
                elif info[symbol]['position'] == 'long':
                    cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                    time.sleep(5)
                    stop_loss_params = {'stopPrice': current_price, 'closePosition': True} # 손절 예약 주문
                    stop_order = binance.create_order(symbol, 'stop_market', 'sell', None, None, stop_loss_params)
                    info[symbol]['position'] = 'wait'
                    current_hold -= 1
                    profit = (current_price - info[symbol]['price']) / info[symbol]['price'] * 100
                    logging.info(f"{symbol} (롱) 2% 도달 실패 수익률: {profit}")
                    bot.sendMessage(chat_id = chat_id, text=f"{symbol} (롱) 2% 도달 실패 수익률: {profit}")

                elif info[symbol]['position'] == 'short':
                    cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                    time.sleep(5)
                    stop_loss_params = {'stopPrice': current_price, 'closePosition': True} # 손절 예약 주문
                    stop_order = binance.create_order(symbol, 'stop_market', 'buy', None, None, stop_loss_params)
                    info[symbol]['position'] = 'wait'
                    current_hold -= 1
                    profit = (info[symbol]['price'] - current_price) / current_price * 100
                    logging.info(f"{symbol} (숏) 2% 도달 실패 수익률: {profit}")
                    bot.sendMessage(chat_id = chat_id, text=f"{symbol} (숏) 2% 도달 실패 수익률: {profit}")

                # 조건 만족시 Long Position
                elif info[symbol]['position'] == 'wait' and current_hold < total_hold and \
                        stoch_osc > 0 and macd_osc > 0:
                    # 투자를 위한 세팅
                    quantity = amount / current_price
                    order = binance.create_limit_buy_order(symbol, quantity, current_price) # 지정가 매수 주문
                    take_profit_params = {'stopPrice': current_price * bull_profit, 'closePosition': True} # 이익실현 예약 주문
                    stop_order = binance.create_order(symbol, 'take_profit_market', 'sell', None, None, take_profit_params)
                    stop_loss_params = {'stopPrice': current_price * bull_loss, 'closePosition': True} # 손절 예약 주문
                    stop_order = binance.create_order(symbol, 'stop_market', 'sell', None, None, stop_loss_params)

                    # 매수가, 포지션 상태, 코인 매수 양 저장
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'long'
                    info[symbol]['quantity'] = quantity
                    current_hold += 1
                    logging.info(f"{symbol} (롱)\n투자금액: ${amount:.2f}\n현재보유: {current_hold}개\n주문: {order}")
                    bot.sendMessage(chat_id=chat_id, text=f"{strategy} {symbol} (Long)\nAmount: ${amount:.2f}\nHolding: {current_hold}")

                # 조건 만족시 Short Position
                elif info[symbol]['position'] == 'wait' and current_hold < total_hold and \
                        stoch_osc < 0 and macd_osc < 0:
                    # 투자를 위한 세팅
                    quantity = amount / current_price
                    order = binance.create_limit_sell_order(symbol, quantity, current_price) # 지정가 매도 주문
                    take_profit_params = {'stopPrice': current_price * bear_profit, 'closePosition': True} # 이익실현 예약 주문
                    stop_order = binance.create_order(symbol, 'take_profit_market', 'buy', None, None, take_profit_params)
                    stop_loss_params = {'stopPrice': current_price * bear_loss, 'closePosition': True} # 손절 예약 주문
                    stop_order = binance.create_order(symbol, 'stop_market', 'buy', None, None, stop_loss_params)

                    # 매수가, 포지션 상태, 코인 매수 양 저장
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'short'
                    info[symbol]['quantity'] = quantity
                    current_hold += 1
                    logging.info(f"{symbol} (숏)\n투자금액: ${amount:.2f}\n현재보유: {current_hold}개\n주문: {order}")
                    bot.sendMessage(chat_id=chat_id, text=f"{strategy} {symbol} (Short)\nAmount: ${amount:.2f}\nHolding: {current_hold}")

            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
                logging.error(e)
            time.sleep(0.5)

        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/binance_short.txt', 'w') as f:
            f.write(json.dumps(info))
