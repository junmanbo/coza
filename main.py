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
tickers = (
        'BCH/USDT', 'EOS/USDT', 'LTC/USDT', 'TRX/USDT', 'ETC/USDT',
        'XLM/USDT', 'BAKE/USDT', 'ICP/USDT', 'XMR/USDT', 'DASH/USDT',
        'ZEC/USDT', 'XTZ/USDT', 'ATOM/USDT', 'ONT/USDT', 'BAT/USDT',
        'NEO/USDT', 'QTUM/USDT', 'THETA/USDT', 'ALGO/USDT', 'ZIL/USDT',
        'ZRX/USDT', 'OMG/USDT', 'WAVES/USDT', 'MKR/USDT', 'SNX/USDT',
        'VET/USDT', 'YFI/USDT', 'RUNE/USDT', 'SUSHI/USDT', 'EGLD/USDT',
        'SOL/USDT', 'ICX/USDT', 'UNI/USDT', 'AVAX/USDT', 'FTM/USDT',
        'HNT/USDT', 'ENJ/USDT', 'KSM/USDT', 'NEAR/USDT', 'AAVE/USDT',
        'FIL/USDT', 'MATIC/USDT', 'ZEN/USDT', 'GRT/USDT', 'CHZ/USDT',
        'ANKR/USDT', 'LUNA/USDT', 'RVN/USDT', 'XEM/USDT', 'MANA/USDT',
        'HBAR/USDT', 'HOT/USDT', 'BTT/USDT', 'SC/USDT', 'DGB/USDT'
        )
symbols = list(tickers)

# 보유하고 있는 코인 갯수
current_hold = 0
for symbol in symbols:
    if info[symbol]['position'] != 'wait':
        current_hold += 1

total_hold = 3 # 투자할 코인 총 갯수
bull_profit = 1.03 # 롱 포지션 수익률
bull_loss = 0.96 # 롱 포지션 손실률
bear_profit = 0.97 # 숏 포지션 수익률
bear_loss = 1.04 # 숏 포지션 손실률
leverage = 5 # 현재 레버리지 값 x5

logging.info(f"{strategy}\n현재보유: {current_hold}개\n투자할 코인: {total_hold-current_hold}개\n기대 수익률: {(bull_profit-1)*100:.2f}%")
bot.sendMessage(chat_id=chat_id, text=f"{strategy}\n현재보유: {current_hold}개\n투자할 코인: {total_hold-current_hold}개\n기대 수익률: {(bull_profit-1)*100:.2f}%")

while True:
    now = datetime.datetime.now()
    time.sleep(1)

    if now.minute % 30 == 0 and 0 <= now.second <= 5:
        # 1코인 1번당 투자 금액 (3번 분할 매수)
        total_balance = binance.fetch_balance()['USDT']['total']
        amount = total_balance / total_hold / 6
        logging.info('30분 정기 체크 - 매수, 매도 조건 확인 및 이익실현, 손절 확인')
        for symbol in symbols:
            try:
                current_price = binance.fetch_ticker(symbol)['close'] # 현재가 조회
                # 1일, 4시간, 1시간, 30분 데이터 수집
                df = getOHLCV(symbol, '1d')
                stoch_osc, stoch_slope = indi.calStochastic(df, 12, 5, 5)
                df = getOHLCV(symbol, '4h')
                stoch_osc_4h = indi.calStochastic(df, 9, 3, 3)[0]
                df = getOHLCV(symbol, '1h')
                stoch_osc_1h = indi.calStochastic(df, 9, 3, 3)[0]
                df = getOHLCV(symbol, '30m')
                stoch_osc_30m = indi.calStochastic(df, 9, 3, 3)[0]
                logging.info(f'코인: {symbol}\n지표: {stoch_osc} {stoch_slope} {stoch_osc_1h} {stoch_osc_4h} {stoch_osc_30m}')

                # 조건 만족시 Long Position
                if info[symbol]['position'] == 'wait' and current_hold < total_hold and \
                        stoch_osc > 15 and stoch_slope > 0 and stoch_osc_30m > 0 and stoch_osc_1h > 0 and stoch_osc_4h > 0:
                    # 투자를 위한 세팅
                    quantity = amount / current_price
                    order = binance.create_market_buy_order(symbol, quantity) # 시장가 매수 주문
                    order1 = binance.create_limit_buy_order(symbol, quantity, current_price * 0.99) # -1% 분할 매수
                    order2 = binance.create_limit_buy_order(symbol, quantity, current_price * 0.98) # -2% 분할 매수

                    take_profit_params = {'stopPrice': current_price * bull_profit, 'closePosition': True} # 이익실현 예약 주문
                    stop_order1 = binance.create_order(symbol, 'take_profit_market', 'sell', None, None, take_profit_params)
                    stop_loss_params = {'stopPrice': current_price * bull_loss, 'closePosition': True} # 손절 예약 주문
                    stop_order2 = binance.create_order(symbol, 'stop_market', 'sell', None, None, stop_loss_params)

                    # 매수가, 포지션 상태, 코인 매수 양 저장
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'long'
                    info[symbol]['quantity'] = quantity
                    current_hold += 1
                    logging.info(f"{symbol} (롱)\n투자금액: ${amount:.2f}\n현재보유: {current_hold}개\n주문: {order}")
                    bot.sendMessage(chat_id=chat_id, text=f"{symbol} (롱)\n투자금액: ${amount:.2f}\n현재보유: {current_hold}개")

                # 조건 만족시 Short Position
                elif info[symbol]['position'] == 'wait' and current_hold < total_hold and \
                        stoch_osc < -15 and stoch_slope < 0 and stoch_osc_30m < 0 and stoch_osc_1h < 0 and stoch_osc_4h < 0:
                    # 투자를 위한 세팅
                    quantity = amount / current_price
                    order = binance.create_market_sell_order(symbol, quantity) # 시장가 매도 주문
                    order1 = binance.create_limit_sell_order(symbol, quantity, current_price * 1.01) # -1% 분할 매수
                    order2 = binance.create_limit_sell_order(symbol, quantity, current_price * 1.02) # -2% 분할 매수

                    take_profit_params = {'stopPrice': current_price * bear_profit, 'closePosition': True} # 이익실현 예약 주문
                    stop_order1 = binance.create_order(symbol, 'take_profit_market', 'buy', None, None, take_profit_params)
                    stop_loss_params = {'stopPrice': current_price * bear_loss, 'closePosition': True} # 손절 예약 주문
                    stop_order2 = binance.create_order(symbol, 'stop_market', 'buy', None, None, stop_loss_params)

                    # 매수가, 포지션 상태, 코인 매수 양 저장
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'short'
                    info[symbol]['quantity'] = quantity
                    current_hold += 1
                    logging.info(f"{symbol} (롱)\n투자금액: ${amount:.2f}\n현재보유: {current_hold}개\n주문: {order}")
                    bot.sendMessage(chat_id=chat_id, text=f"{symbol} (롱)\n투자금액: ${amount:.2f}\n현재보유: {current_hold}개")

                # 이익실현 / 손절 체크
                elif info[symbol]['position'] == 'long':
                    if df['high'][-2] > info[symbol]['price'] * bull_profit or df['low'][-2] < info[symbol]['price'] * bull_loss:
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        logging.info(f"{symbol} (롱) 포지션 종료\n취소주문: {cancel_order}")

                elif info[symbol]['position'] == 'short':
                    if df['low'][-2] < info[symbol]['price'] * bear_profit or df['high'][-2] > info[symbol]['price'] * bear_loss:
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        logging.info(f"{symbol} (숏) 포지션 종료\n취소주문: {cancel_order}")

            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
                logging.error(e)
            time.sleep(0.1)

        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/binance_short.txt', 'w') as f:
            f.write(json.dumps(info))