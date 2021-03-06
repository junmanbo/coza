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

bull_profit = 1.007
bull_loss = 0.9967 # 롱 포지션 손실률
bear_profit = 0.993
bear_loss = 1.0033 # 숏 포지션 손실률
amount = 1000
start_price = 1
stop_order = {}
take_order = {}
fee = 0.2 / 100

logging.info(f"{strategy} Start")
bot.sendMessage(chat_id=chat_id, text=f"{strategy} Start!")

logging.info('스윙 전략이 끝날 때 까지 기다리는 중')
bot.sendMessage(chat_id = chat_id, text=f"전략: {strategy} 스윙 전략 끝날 때 까지 기다리는 중")
while True:
    hold = False
    with open('./Data/binance_swing.txt', 'r') as f:
        data = f.read()
        check = json.loads(data)
    for ticker in check.keys():
        if check[ticker]['position'] != 'wait':
            hold = True
    if hold == False:
        logging.info(f'스윙 포지션 전부 종료: {hold} Stop\n스캘핑 전략 재개')
        bot.sendMessage(chat_id = chat_id, text=f"스윙 포지션 전부 종료: {hold} Stop\n스캘핑 전략 재개")
        time.sleep(60)
        break
    time.sleep(60)

while True:
    now = datetime.datetime.now()
    time.sleep(0.1)
    symbol = symbols[now.hour]

    if now.hour == 9 and now.minute == 0:
        time.sleep(300)
        logging.info('스윙 전략이 끝날 때 까지 기다리는 중')
        bot.sendMessage(chat_id = chat_id, text=f"전략: {strategy} 스윙전략 끝날 때까지 기다리는 중")
        while True:
            hold = False
            with open('./Data/binance_swing.txt', 'r') as f:
                data = f.read()
                check = json.loads(data)
            for ticker in check.keys():
                if check[ticker]['position'] != 'wait':
                    hold = True
            if hold == False:
                logging.info(f'스윙 포지션 전부 종료: {hold} Stop\n스캘핑 전략 재개')
                bot.sendMessage(chat_id = chat_id, text=f"스윙 포지션 전부 종료: {hold} Stop\n스캘핑 전략 재개")
                time.sleep(60)
                break
            time.sleep(60)

    elif 28 <= now.second <= 29 or 58 <= now.second <= 59:
        try:
            current_price = binance.fetch_ticker(symbol)['close'] # 현재가 조회

            df = getOHLCV(symbol, '15m')
            stoch_osc = indi.calStochastic(df, 9, 3, 3)[1]

            df = getOHLCV(symbol, '1m')
            stoch_osc_before, stoch_osc_now = indi.calStochastic(df, 12, 5, 5)
            mfi = indi.cal_mfi(df, 10)
            vol_short = indi.cal_vol_ema(df, 5)
            vol_long = indi.cal_vol_ema(df, 10)

            #logging.info(f'Coin: {symbol} Stochastic: {stoch_osc_before:.2f} {stoch_osc_now:.2f} {stoch_osc:.2f} MFI: {mfi:.2f} Volume: {vol_short:.2f} {vol_long:.2f}')

            if info[symbol]['position'] == 'long':
                # 1시간 단위로 코인 변경(이전 코인 청산)
                if now.minute == 59 and now.second > 50:
                    cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                    time.sleep(5)
                    stop_loss_params = {'stopPrice': current_price, 'reduceOnly': True} # 손절 예약 주문
                    stop_order = binance.create_order(symbol, 'stop', 'sell', info[symbol]['quantity'], current_price, stop_loss_params)
                    info[symbol]['position'] = 'wait'
                    bot.sendMessage(chat_id = chat_id, text=f"{symbol} 1시간 경과 - 코인 변경 시간으로 마무리 정리")

                # 이익실현 / 손절체크
                elif df.low.values[-1] < info[symbol]['price'] * bull_loss:
                    cancel_order = binance.cancel_order(take_order['id'], symbol) # 남은 주문 취소
                    profit = (info[symbol]['price'] * bull_loss - start_price) / start_price * 100 - fee
                    info[symbol]['position'] = 'wait'
                    logging.info(f"{symbol} (롱) 포지션 종료 수익률: {profit:.2f}")
                    bot.sendMessage(chat_id = chat_id, text=f"{symbol} (롱) 포지션 종료\n수익률: {profit:.2f}")
                elif df.high.values[-1] > start_price * bull_profit:
                    cancel_order = binance.cancel_order(stop_order['id'], symbol) # 남은 주문 취소
                    profit = (bull_profit - 1) * 100 - fee
                    info[symbol]['position'] = 'wait'
                    logging.info(f"{symbol} (롱) 포지션 종료 수익률: {profit:.2f}")
                    bot.sendMessage(chat_id = chat_id, text=f"{symbol} (롱) 포지션 종료\n수익률: {profit:.2f}")

                # + 수익일 경우 본절로스 갱신
                elif current_price > info[symbol]['price']:
                    cancel_order = binance.cancel_order(stop_order['id'], symbol) # 남은 주문 취소
                    time.sleep(2)
                    info[symbol]['price'] = current_price
                    stop_loss_params = {'stopPrice': current_price * bull_loss, 'reduceOnly': True} # 손절 예약 주문
                    stop_order = binance.create_order(symbol, 'stop', 'sell', info[symbol]['quantity'], current_price * bull_loss, stop_loss_params)
                    logging.info(f"{symbol} (롱) + 진행중! 본절로스 갱신")

            elif info[symbol]['position'] == 'short':
                # 1시간 단위로 코인 변경(이전 코인 청산)
                if now.minute == 59 and now.second > 50:
                    cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                    time.sleep(5)
                    stop_loss_params = {'stopPrice': current_price, 'reduceOnly': True} # 손절 예약 주문
                    stop_order = binance.create_order(symbol, 'stop', 'buy', info[symbol]['quantity'], current_price, stop_loss_params)
                    info[symbol]['position'] = 'wait'
                    bot.sendMessage(chat_id = chat_id, text=f"{symbol} 1시간 경과 - 코인 변경 시간으로 마무리 정리")

                # 이익실현 / 손절체크
                elif df.high.values[-1] > info[symbol]['price'] * bear_loss:
                    cancel_order = binance.cancel_order(take_order['id'], symbol) # 남은 주문 취소
                    profit = (start_price - info[symbol]['price'] * bear_loss) / (info[symbol]['price'] * bear_loss) * 100 - fee
                    info[symbol]['position'] = 'wait'
                    logging.info(f"{symbol} (숏) 포지션 종료. 수익률: {profit:.2f}")
                    bot.sendMessage(chat_id = chat_id, text=f"{symbol} (숏) 포지션 종료\n수익률: {profit:.2f}")
                elif df.low.values[-1] < start_price * bear_profit:
                    cancel_order = binance.cancel_order(stop_order['id'], symbol) # 남은 주문 취소
                    profit = (1 - bear_profit) * 100 - fee
                    info[symbol]['position'] = 'wait'
                    logging.info(f"{symbol} (숏) 포지션 종료. 수익률: {profit:.2f}")
                    bot.sendMessage(chat_id = chat_id, text=f"{symbol} (숏) 포지션 종료\n수익률: {profit:.2f}")

                # + 수익일 경우 본절로스 갱신
                elif current_price < info[symbol]['price']:
                    cancel_order = binance.cancel_order(stop_order['id'], symbol) # 남은 주문 취소
                    time.sleep(2)
                    info[symbol]['price'] = current_price
                    stop_loss_params = {'stopPrice': current_price * bear_loss, 'reduceOnly': True} # 손절 예약 주문
                    stop_order = binance.create_order(symbol, 'stop', 'buy', info[symbol]['quantity'], current_price * bear_loss, stop_loss_params)
                    logging.info(f"{symbol} (숏) + 진행중! 본절로스 갱신")

            # 조건 만족시 Long Position
            elif info[symbol]['position'] == 'wait' and stoch_osc_before < 0 and stoch_osc_now > 0 and \
                    stoch_osc > 0 and vol_short > vol_long and mfi < 30 and now.minute < 50:
                # 투자를 위한 세팅
                bid_ask = binance.fetch_bids_asks(symbols=symbol)
                current_price = bid_ask[symbol]['ask']
                quantity = amount / current_price
                order = binance.create_limit_buy_order(symbol, quantity, current_price) # 지정가 매수 주문
                take_order = binance.create_limit_sell_order(symbol, quantity, current_price * bull_profit) # 이익실현 매도 주문
                stop_loss_params = {'stopPrice': current_price * bull_loss, 'reduceOnly': True} # 손절 예약 주문
                stop_order = binance.create_order(symbol, 'stop', 'sell', quantity, current_price * bull_loss, stop_loss_params)

                # 매수가, 포지션 상태, 코인 매수 양 저장
                start_price = current_price
                info[symbol]['price'] = current_price
                info[symbol]['position'] = 'long'
                info[symbol]['quantity'] = quantity
                logging.info(f"{symbol} (롱)\n투자금액: ${amount:.2f}")
                bot.sendMessage(chat_id=chat_id, text=f"{strategy} {symbol} (Long)\nAmount: ${amount:.2f}")

            # 조건 만족시 Short Position
            elif info[symbol]['position'] == 'wait' and stoch_osc_before > 0 and stoch_osc_now < 0 and \
                    stoch_osc < 0 and vol_short > vol_long and mfi > 80 and now.minute < 50:
                # 투자를 위한 세팅
                bid_ask = binance.fetch_bids_asks(symbols=symbol)
                current_price = bid_ask[symbol]['bid']
                quantity = amount / current_price
                order = binance.create_limit_sell_order(symbol, quantity, current_price) # 지정가 매도 주문
                take_order = binance.create_limit_buy_order(symbol, quantity, current_price * bear_profit)
                stop_loss_params = {'stopPrice': current_price * bear_loss, 'reduceOnly': True} # 손절 예약 주문
                stop_order = binance.create_order(symbol, 'stop', 'buy', quantity, current_price * bear_loss, stop_loss_params)

                # 매수가, 포지션 상태, 코인 매수 양 저장
                start_price = current_price
                info[symbol]['price'] = current_price
                info[symbol]['position'] = 'short'
                info[symbol]['quantity'] = quantity
                logging.info(f"{symbol} (숏)\n투자금액: ${amount:.2f}")
                bot.sendMessage(chat_id=chat_id, text=f"{strategy} {symbol} (Short)\nAmount: ${amount:.2f}")

            time.sleep(2)

        except Exception as e:
            bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
            logging.error(e)

        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/binance_scalp.txt', 'w') as f:
            f.write(json.dumps(info))
