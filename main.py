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
        'BCH/USDT', 'XRP/USDT', 'EOS/USDT', 'LTC/USDT', 'TRX/USDT',
        'ETC/USDT', 'LINK/USDT', 'XLM/USDT', 'BTC/USDT', 'BAKE/USDT',
        'ADA/USDT', 'XMR/USDT', 'DASH/USDT', 'ZEC/USDT', 'XTZ/USDT',
        'BNB/USDT', 'ATOM/USDT', 'ONT/USDT', 'BAT/USDT', 'VET/USDT',
        'NEO/USDT', 'QTUM/USDT', 'THETA/USDT', 'ALGO/USDT', 'ZIL/USDT',
        'ZRX/USDT', 'OMG/USDT', 'WAVES/USDT', 'MKR/USDT', 'SNX/USDT',
        'DOT/USDT', 'YFI/USDT', 'RUNE/USDT', 'SUSHI/USDT', 'EGLD/USDT',
        'SOL/USDT', 'ICX/USDT', 'UNI/USDT', 'AVAX/USDT', 'FTM/USDT',
        'HNT/USDT', 'ENJ/USDT', 'KSM/USDT', 'NEAR/USDT', 'AAVE/USDT',
        'FIL/USDT', 'MATIC/USDT', 'ZEN/USDT', 'GRT/USDT', 'CHZ/USDT',
        'ANKR/USDT', 'LUNA/USDT', 'RVN/USDT', 'XEM/USDT', 'MANA/USDT',
        'HBAR/USDT', 'HOT/USDT', 'BTT/USDT', 'SC/USDT', 'DGB/USDT',
        'ETH/USDT', 'ICP/USDT'
        )
symbols = list(tickers)

# 보유하고 있는 코인 갯수
current_hold = 0
for symbol in symbols:
    if info[symbol]['position'] != 'wait':
        current_hold += 1

total_hold = 3 # 투자할 코인 총 갯수
bull_profit = 1.05 # 롱 포지션 수익률
bull_loss = 0.96 # 롱 포지션 손실률
bear_profit = 0.95 # 숏 포지션 수익률
bear_loss = 1.04 # 숏 포지션 손실률
leverage = 5 # 현재 레버리지 값 x5
amount = 800 # 1회 투자 금액

logging.info(f"{strategy}\n현재보유: {current_hold}개\n투자할 코인: {total_hold-current_hold}개\n기대 수익률: {(bull_profit-1)*100:.2f}%")
bot.sendMessage(chat_id=chat_id, text=f"{strategy}\n현재보유: {current_hold}개\n투자할 코인: {total_hold-current_hold}개\n기대 수익률: {(bull_profit-1)*100:.2f}%")

while True:
    now = datetime.datetime.now()
    time.sleep(1)

    if now.minute % 30 == 0 and 0 <= now.second <= 5:
        logging.info('30분 정기 체크 - 매수, 매도 조건 확인 및 이익실현, 손절 확인')
        for symbol in symbols:
            try:
                current_price = binance.fetch_ticker(symbol)['close'] # 현재가 조회
                # 1일, 4시간, 1시간, 30분 데이터 수집
                df = getOHLCV(symbol, '1d')
                stoch_osc = indi.calStochastic(df, 12, 5, 5)[0]
                stoch_slope = indi.calStochastic(df, 12, 5, 5)[1]

                df = getOHLCV(symbol, '4h')
                stoch_osc_4h = indi.calStochastic(df, 9, 3, 3)[0]

                df = getOHLCV(symbol, '1h')
                stoch_osc_1h = indi.calStochastic(df, 9, 3, 3)[0]

                df = getOHLCV(symbol, '30m')
                stoch_osc_30m = indi.calStochastic(df, 9, 3, 3)[0]

                logging.info(f'코인: {symbol}\n지표: {stoch_osc} {stoch_slope} {stoch_osc_1h} {stoch_osc_4h} {stoch_osc_30m}')

                # 조건 만족시 Long Position
                if info[symbol]['position'] == 'wait' and current_hold < total_hold and \
                        stoch_osc > 10 and stoch_slope > 0 and stoch_osc_30m > 0 and stoch_osc_1h > 0 and stoch_osc_4h > 0:
                    # 투자를 위한 세팅
                    #  free_balance = binance.fetch_balance()['USDT']['free']
                    #  amount = free_balance * leverage / (total_hold - current_hold) / 3
                    quantity = amount / current_price
                    order = binance.create_market_buy_order(symbol, quantity) # 시장가 매수 주문
                    take_profit_params = {'stopPrice': current_price * bull_profit} # 이익실현 예약 주문
                    order1 = binance.create_order(symbol, 'take_profit_market', 'sell', quantity, None, take_profit_params)
                    stop_loss_params = {'stopPrice': current_price * bull_loss} # 손절 예약 주문
                    order2 = binance.create_order(symbol, 'stop_market', 'sell', quantity, None, stop_loss_params)
                    # 매수가, 포지션 상태, 코인 매수 양 저장
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'long'
                    info[symbol]['quantity'] = quantity
                    info[symbol]['total_trading'] = 1
                    current_hold += 1
                    logging.info(f"{symbol} (롱)\n투자금액: ${amount:.2f}\n현재보유: {current_hold}개\n주문: {order}")
                    bot.sendMessage(chat_id=chat_id, text=f"{symbol} (롱)\n투자금액: ${amount:.2f}\n현재보유: {current_hold}개")

                # 조건 만족시 Short Position
                elif info[symbol]['position'] == 'wait' and current_hold < total_hold and \
                        stoch_osc < -10 and stoch_slope < 0 and stoch_osc_30m < 0 and stoch_osc_1h < 0 and stoch_osc_4h < 0:
                    # 투자를 위한 세팅
                    #  free_balance = binance.fetch_balance()['USDT']['free']
                    #  amount = free_balance * leverage / (total_hold - current_hold) / 3
                    quantity = amount / current_price
                    order = binance.create_market_sell_order(symbol, quantity) # 시장가 매도 주문
                    take_profit_params = {'stopPrice': current_price * bear_profit} # 이익실현 예약 주문
                    order1 = binance.create_order(symbol, 'take_profit_market', 'buy', quantity, None, take_profit_params)
                    stop_loss_params = {'stopPrice': current_price * bear_loss} # 손절 예약 주문
                    order2 = binance.create_order(symbol, 'stop_market', 'buy', quantity, None, stop_loss_params)
                    # 매수가, 포지션 상태, 코인 매수 양 저장
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'short'
                    info[symbol]['quantity'] = quantity
                    info[symbol]['total_trading'] = 1
                    current_hold += 1
                    logging.info(f"{symbol} (숏)\n투자금액: ${amount:.2f}\n현재보유: {current_hold}개\n주문: {order}")
                    bot.sendMessage(chat_id=chat_id, text=f"{symbol} (숏)\n투자금액: ${amount:.2f}\n현재보유: {current_hold}개")

                # 롱 포지션 이익실현 / 손절 체크
                elif info[symbol]['position'] == 'long' and df['high'][-2] > info[symbol]['price'] * bull_profit:
                    profit = (bull_profit - 1) * 100
                    total_amount = amount * info[symbol]['total_trading']
                    indi.saveHistory(strategy, symbol, info[symbol]['position'], total_amount, profit) # 엑셀 파일에 저장
                    cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                    info[symbol]['position'] = 'wait'
                    current_hold -= 1
                    logging.info(f"{symbol} (롱) 수익률: {profit:.2f}% 성공\n취소주문: {cancel_order}")
                    bot.sendMessage(chat_id=chat_id, text=f"{symbol} (롱) 수익률: {profit:.2f}% 성공")

                elif info[symbol]['position'] == 'long' and df['low'][-2] < info[symbol]['price'] * bull_loss:
                    profit = (bull_loss - 1) * 100
                    total_amount = amount * info[symbol]['total_trading']
                    indi.saveHistory(strategy, symbol, info[symbol]['position'], total_amount, profit) # 엑셀 파일에 저장
                    cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                    info[symbol]['position'] = 'wait'
                    current_hold -= 1
                    logging.info(f"{symbol} (롱) 수익률: {profit:.2f}% 실패\n취소주문: {cancel_order}")
                    bot.sendMessage(chat_id=chat_id, text=f"{symbol} (롱) 수익률: {profit:.2f}% 실패")

                # 숏 포지션 이익실현 / 손절 체크
                elif info[symbol]['position'] == 'short' and df['low'][-2] < info[symbol]['price'] * bear_profit:
                    profit = (1 - bear_profit) * 100
                    total_amount = amount * info[symbol]['total_trading']
                    indi.saveHistory(strategy, symbol, info[symbol]['position'], total_amount, profit) # 엑셀 파일에 저장
                    cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                    info[symbol]['position'] = 'wait'
                    current_hold -= 1
                    logging.info(f"{symbol} (숏) 수익률: {profit:.2f}% 성공\n취소주문: {cancel_order}")
                    bot.sendMessage(chat_id=chat_id, text=f"{symbol} (숏) 수익률: {profit:.2f}% 성공")

                elif info[symbol]['position'] == 'short' and df['high'][-2] > info[symbol]['price'] * bear_loss:
                    profit = (1 - bear_loss) * 100
                    total_amount = info[symbol]['price'] * info[symbol]['quantity']
                    indi.saveHistory(strategy, symbol, info[symbol]['position'], total_amount, profit) # 엑셀 파일에 저장
                    cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                    info[symbol]['position'] = 'wait'
                    current_hold -= 1
                    logging.info(f"{symbol} (숏)\n수익률: {profit:.2f}% 실패\n취소주문: {cancel_order}")
                    bot.sendMessage(chat_id=chat_id, text=f"{symbol} (숏)\n수익률: {profit:.2f}% 실패")

            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
                logging.error(e)
            time.sleep(0.1)

        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/binance_short.txt', 'w') as f:
            f.write(json.dumps(info))

    # 추가 매수/매도
    elif now.minute == 59 and 0 <= now.second <= 5:
        logging.info('59분 정기 체크 - 추가 매수, 매도 확인')
        for symbol in symbols:
            try:
                if info[symbol]['position'] != 'wait':
                    current_price = binance.fetch_ticker(symbol)['close'] # 현재가 조회

                    # 롱 포지션 수익률 마이너스 1% 당 1회씩 추가 매수
                    if info[symbol]['position'] == 'long' and info[symbol]['total_trading'] < 3 and current_price < info[symbol]['price'] * 0.99:
                        amount = 800 # 1회 투자 금액
                        quantity = amount / current_price # 이번 거래에 매수할 양
                        order = binance.create_market_buy_order(symbol, quantity) # 시장가 매수 주문
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        info[symbol]['total_trading'] += 1 # 추가 매수 횟수
                        info[symbol]['quantity'] += quantity # 총 매수량
                        info[symbol]['price'] = amount * info[symbol]['total_trading'] / info[symbol]['quantity'] # 평균 매수 단가
                        take_profit_params = {'stopPrice': info[symbol]['price'] * bull_profit} # 이익실현 예약 주문
                        order1 = binance.create_order(symbol, 'take_profit_market', 'sell', info[symbol]['quantity'], None, take_profit_params)
                        stop_loss_params = {'stopPrice': info[symbol]['price'] * bull_loss} # 손절 예약 주문
                        order2 = binance.create_order(symbol, 'stop_market', 'sell', info[symbol]['quantity'], None, stop_loss_params)
                        logging.info(f"{symbol} (롱)\n투자금액: ${amount * info[symbol]['total_trading']}\n현재보유: {current_hold}개\n주문: {order}")
                        bot.sendMessage(chat_id=chat_id, text=f"{symbol} (롱)\n투자금액: ${amount * info[symbol]['total_trading']}\n현재보유: {current_hold}개")

                    # 숏 포지션 수익률 마이너스 1% 당 1회씩 추가 매도
                    elif info[symbol]['position'] == 'short' and info[symbol]['total_trading'] < 3 and current_price > info[symbol]['price'] * 1.01:
                        amount = 800 # 1회 투자 금액
                        quantity = amount / current_price # 이번 거래에 매수할 양
                        order = binance.create_market_sell_order(symbol, quantity) # 시장가 매수 주문
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        info[symbol]['total_trading'] += 1 # 추가 매수 횟수
                        info[symbol]['quantity'] += quantity # 총 매수량
                        info[symbol]['price'] = amount * info[symbol]['total_trading'] / info[symbol]['quantity'] # 평균 매도 단가
                        take_profit_params = {'stopPrice': info[symbol]['price'] * bear_profit} # 이익실현 예약 주문
                        order1 = binance.create_order(symbol, 'take_profit_market', 'buy', info[symbol]['quantity'], None, take_profit_params)
                        stop_loss_params = {'stopPrice': info[symbol]['price'] * bear_loss} # 손절 예약 주문
                        order2 = binance.create_order(symbol, 'stop_market', 'buy', info[symbol]['quantity'], None, stop_loss_params)
                        logging.info(f"{symbol} (숏)\n투자금액: ${amount * info[symbol]['total_trading']}\n현재보유: {current_hold}개\n주문: {order}")
                        bot.sendMessage(chat_id=chat_id, text=f"{symbol} (롱)\n투자금액: ${amount * info[symbol]['total_trading']}\n현재보유: {current_hold}개")

            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
                logging.error(e)
            time.sleep(0.1)

        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/binance_short.txt', 'w') as f:
            f.write(json.dumps(info))
