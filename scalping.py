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
logging.basicConfig(filename='./Log/binance_scalp.log', format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

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
with open('./Data/binance_scalp.txt', 'r') as f:
    data = f.read()
    info = json.loads(data)

# OHLCV 데이터 가져오기
def getOHLCV(symbol, period):
    ohlcv = binance.fetch_ohlcv(symbol, period)
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    return df

strategy = 'Scalping'
#  tickers = binance.load_markets().keys() # 목록 전체 조회
symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT',
        'UNI/USDT', 'ICP/USDT', 'BCH/USDT', 'LINK/USDT', 'LTC/USDT',
        'SOL/USDT', 'THETA/USDT', 'ETC/USDT', 'FIL/USDT', 'EOS/USDT',
        'XMR/USDT', 'AAVE/USDT', 'NEO/USDT', 'MKR/USDT', 'KSM/USDT',
        'ATOM/USDT', 'AVAX/USDT', 'LUNA/USDT', 'RUNE/USDT', 'XTZ/USDT',
        'COMP/USDT', 'DASH/USDT', 'ZEC/USDT', 'EGLD/USDT', 'WAVES/USDT',
        'YFI/USDT', 'SUSHI/USDT', 'SNX/USDT', 'HNT/USDT', 'QTUM/USDT',
        'ZEN/USDT']

bull_loss = 0.996 # 롱 포지션 손실률
bear_loss = 1.004 # 숏 포지션 손실률
amount = 10000
start_price = 1
fee = 0.2 / 100

logging.info(f"{strategy} Start")
bot.sendMessage(chat_id=chat_id, text=f"{strategy} Start!")

while True:
    now = datetime.datetime.now()
    time.sleep(0.1)
    symbol = symbols[now.hour]

    if 28 <= now.second <= 29 or 58 <= now.second <= 59:
        try:
            current_price = binance.fetch_ticker(symbol)['close'] # 현재가 조회

            df = getOHLCV(symbol, '1m')
            stoch_osc_before, stoch_osc_now = indi.calStochastic(df, 9, 3, 3)
            macd_osc = indi.calMACD(df, 12, 26, 9)
            mfi_slope = indi.cal_mfi(df, 10)

            logging.info(f'코인: {symbol}\nStochastic Before: {stoch_osc_before} Stochastic Now: {stoch_osc_now}\nMACD OSC: {macd_osc} MFI Slope: {mfi_slope}')

            if now.minute == 59 and now.second > 30:
                if info[symbol]['position'] == 'long':
                    cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                    time.sleep(2)
                    stop_loss_params = {'stopPrice': current_price, 'closePosition': True} # 손절 예약 주문
                    stop_order = binance.create_order(symbol, 'stop_market', 'sell', None, None, stop_loss_params)
                    info[symbol]['position'] = 'wait'

                elif info[symbol]['position'] == 'short':
                    cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                    time.sleep(2)
                    stop_loss_params = {'stopPrice': current_price, 'closePosition': True} # 손절 예약 주문
                    stop_order = binance.create_order(symbol, 'stop_market', 'buy', None, None, stop_loss_params)
                    info[symbol]['position'] = 'wait'

            # 이익실현 / 손절체크
            elif info[symbol]['position'] == 'long' and df['low'][-1] < info[symbol]['price'] * bull_loss:
                profit = (info[symbol]['price'] * bull_loss - start_price) / start_price * 100 - fee
                info[symbol]['position'] = 'wait'
                logging.info(f"{symbol} (롱) 포지션 종료 수익률: {profit:.2f}")
                bot.sendMessage(chat_id = chat_id, text=f"{symbol} (롱) 포지션 종료\n수익률: {profit:.2f}")

            elif info[symbol]['position'] == 'short' and df['high'][-1] > info[symbol]['price'] * bear_loss:
                profit = (start_price - info[symbol]['price'] * bear_loss) / (info[symbol]['price'] * bear_loss) * 100 - fee
                info[symbol]['position'] = 'wait'
                logging.info(f"{symbol} (숏) 포지션 종료. 수익률: {profit:.2f}")
                bot.sendMessage(chat_id = chat_id, text=f"{symbol} (숏) 포지션 종료\n수익률: {profit:.2f}")

            # + 수익일 경우 본절로스 갱신
            elif info[symbol]['position'] == 'long' and current_price > info[symbol]['price']:
                cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                time.sleep(2)
                info[symbol]['price'] = current_price
                stop_loss_params = {'stopPrice': current_price * bull_loss, 'closePosition': True} # 손절 예약 주문
                stop_order = binance.create_order(symbol, 'stop_market', 'sell', None, None, stop_loss_params)
                logging.info(f"{symbol} (롱) + 진행중! 본절로스 갱신")

            elif info[symbol]['position'] == 'short' and current_price < info[symbol]['price']:
                cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                time.sleep(2)
                info[symbol]['price'] = current_price
                stop_loss_params = {'stopPrice': current_price * bear_loss, 'closePosition': True} # 손절 예약 주문
                stop_order = binance.create_order(symbol, 'stop_market', 'buy', None, None, stop_loss_params)
                logging.info(f"{symbol} (숏) + 진행중! 본절로스 갱신")

            # 조건 만족시 Long Position
            elif info[symbol]['position'] == 'wait' and stoch_osc_before < 0 and stoch_osc_now > 0 and mfi_slope > 0:
                # 투자를 위한 세팅
                bid_ask = binance.fetch_bids_asks(symbols=symbol)
                current_price = bid_ask[symbol]['ask']
                quantity = amount / current_price
                order = binance.create_limit_buy_order(symbol, quantity, current_price) # 지정가 매수 주문
                stop_loss_params = {'stopPrice': current_price * bull_loss, 'closePosition': True} # 손절 예약 주문
                stop_order = binance.create_order(symbol, 'stop_market', 'sell', None, None, stop_loss_params)

                # 매수가, 포지션 상태, 코인 매수 양 저장
                start_price = current_price
                info[symbol]['price'] = current_price
                info[symbol]['position'] = 'long'
                info[symbol]['quantity'] = quantity
                logging.info(f"{symbol} (롱)\n투자금액: ${amount:.2f}")
                bot.sendMessage(chat_id=chat_id, text=f"{strategy} {symbol} (Long)\nAmount: ${amount:.2f}")

            # 조건 만족시 Short Position
            elif info[symbol]['position'] == 'wait' and stoch_osc_before > 0 and stoch_osc_now < 0 and mfi_slope < 0:
                # 투자를 위한 세팅
                bid_ask = binance.fetch_bids_asks(symbols=symbol)
                current_price = bid_ask[symbol]['bid']
                quantity = amount / current_price
                order = binance.create_limit_sell_order(symbol, quantity, current_price) # 지정가 매도 주문
                stop_loss_params = {'stopPrice': current_price * bear_loss, 'closePosition': True} # 손절 예약 주문
                stop_order = binance.create_order(symbol, 'stop_market', 'buy', None, None, stop_loss_params)

                # 매수가, 포지션 상태, 코인 매수 양 저장
                start_price = current_price
                info[symbol]['price'] = current_price
                info[symbol]['position'] = 'short'
                info[symbol]['quantity'] = quantity
                logging.info(f"{symbol} (숏)\n투자금액: ${amount:.2f}")
                bot.sendMessage(chat_id=chat_id, text=f"{strategy} {symbol} (Short)\nAmount: ${amount:.2f}")

            time.sleep(3)

        except Exception as e:
            bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
            logging.error(e)

        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/binance_scalp.txt', 'w') as f:
            f.write(json.dumps(info))
