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
        )
symbols = list(tickers)

# 보유하고 있는 코인 갯수
current_hold = 0
for symbol in symbols:
    if info[symbol]['position'] != 'wait':
        current_hold += 1

total_hold = 5 # 투자할 코인 총 갯수
bull_profit = 1.05 # 롱 포지션 수익률
bull_loss = 0.96 # 롱 포지션 손실률
bear_profit = 0.95 # 숏 포지션 수익률
bear_loss = 1.04 # 숏 포지션 손실률

leverage = 5 # 현재 레버리지 값 x6
logging.info(f"{strategy}\n현재보유: {current_hold}개\n투자할 코인: {total_hold-current_hold}개\n기대 수익률: {(bull_profit-1)*100:.2f}%")

while True:
    now = datetime.datetime.now()
    time.sleep(1)

    # 익절한 코인 및 손절할 코인 체크
    if now.hour % 2 == 0 and now.minute == 1 and 0 <= now.second <= 9:
        for symbol in symbols:
            try:
                current_price = binance.fetch_ticker(symbol)['close'] # 현재가 조회
                # 일봉 데이터 수집
                df = getOHLCV(symbol, '1d')
                stoch_osc_d = indi.calStochastic(df, 12, 5, 5)[0]
                stoch_slope_d = indi.calStochastic(df, 12, 5, 5)[1]
                macd_osc = indi.calMACD(df, 14, 30, 10)
                mfi = indi.calMFI(df, 14)

                # 4시봉 데이터 수집
                df = getOHLCV(symbol, '4h')
                stoch_osc_4h = indi.calStochastic(df, 12, 5, 5)[0]
                stoch_slope_4h = indi.calStochastic(df, 12, 5, 5)
                logging.info(f'코인: {symbol}\n지표: {stoch_osc_d} {stoch_slope_d} {stoch_osc_4h} {stoch_slope_4h} {macd_osc} {mfi}')

                # 조건 만족시 Long Position
                if info[symbol]['position'] == 'wait' and current_hold < total_hold and \
                        stoch_osc_d > 0 and stoch_slope_d > 0 and stoch_osc_4h > 0 and \
                        stoch_slope_4h > 0 and macd_osc > 0 and mfi > 0:
                    # 투자를 위한 세팅
                    free_balance = binance.fetch_balance()['USDT']['free'] - 50
                    invest_money = free_balance * leverage / (total_hold - current_hold)
                    amount = invest_money / current_price
                    # 지정가 매수 주문
                    #  order = binance.create_limit_buy_order(symbol, amount, current_price)
                    # 시장가 매수 주문
                    order = binance.create_market_buy_order(symbol, amount)
                    # 이익실현 예약 주문
                    take_profit_params = {'stopPrice': current_price * bull_profit}
                    order1 = binance.create_order(symbol, 'take_profit_market', 'sell', amount, None, take_profit_params)
                    # 손절 예약 주문
                    stop_loss_params = {'stopPrice': current_price * bull_loss}
                    order2 = binance.create_order(symbol, 'stop_market', 'sell', amount, None, stop_loss_params)
                    # 매수가, 포지션 상태, 코인 매수 양 저장
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'long'
                    info[symbol]['amount'] = amount
                    current_hold += 1
                    logging.info(f"{symbol} (롱)\n투자금액: ${invest_money:.2f}\n현재보유: {current_hold}개\n주문: {order} 이익실현 주문: {order1} 손절 주문: {order2}")

                # 조건 만족시 Short Position
                elif info[symbol]['position'] == 'wait' and current_hold < total_hold and \
                        stoch_osc_d < 0 and stoch_slope_d < 0 and  stoch_osc_4h < 0 and \
                        stoch_slope_4h < 0 and macd_osc < 0 and mfi < 0:
                    # 투자를 위한 세팅
                    free_balance = binance.fetch_balance()['USDT']['free'] - 50
                    invest_money = free_balance * leverage / (total_hold - current_hold)
                    amount = invest_money / current_price
                    # 지정가 매수 주문
                    #  order = binance.create_limit_sell_order(symbol, amount, current_price)
                    # 시장가 매도 주문
                    order = binance.create_market_sell_order(symbol, amount)
                    # 이익실현 예약 주문
                    take_profit_params = {'stopPrice': current_price * bear_profit}
                    order1 = binance.create_order(symbol, 'take_profit_market', 'buy', amount, None, take_profit_params)
                    # 손절 예약 주문
                    stop_loss_params = {'stopPrice': current_price * bear_loss}
                    order2 = binance.create_order(symbol, 'stop_market', 'buy', amount, None, stop_loss_params)
                    # 매수가, 포지션 상태, 코인 매수 양 저장
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'short'
                    info[symbol]['amount'] = amount
                    current_hold += 1
                    logging.info(f"{symbol} (숏)\n투자금액: ${invest_money:.2f}\n현재보유: {current_hold}개\n주문: {order} 이익실현 주문: {order1} 손절 주문: {order2}")

            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
                logging.error(e)
            time.sleep(0.1)

        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/binance_short.txt', 'w') as f:
            f.write(json.dumps(info))

    # 15분 마다 익절 / 손절 체크
    elif now.minute % 15 == 0 and 0 <= now.second <= 2:
        for symbol in symbols:
            try:
                if info[symbol]['position'] != 'wait':
                    df = getOHLCV(symbol, '15m')
                    if info[symbol]['position'] == 'long':
                        logging.info(f"{symbol} (롱) 고가: {df['high'][-1]} 저가: {df['low'][-1]}\n매수가: {info[symbol]['price']} 목표가: {info[symbol]['price']*bull_profit}")
                    elif info[symbol]['position'] == 'short':
                        logging.info(f"{symbol} (숏) 고가: {df['high'][-1]} 저가: {df['low'][-1]}\n매도가: {info[symbol]['price']} 목표가: {info[symbol]['price']*bear_profit}")

                    # 롱 포지션 이익실현 / 손절 체크
                    if info[symbol]['position'] == 'long' and df['high'][-1] > info[symbol]['price'] * bull_profit:
                        profit = (bull_profit - 1) * 100
                        invest_money = info[symbol]['price'] * info[symbol]['amount']
                        indi.saveHistory(strategy, symbol, info[symbol]['position'], invest_money, profit) # 엑셀 파일에 저장
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        logging.info(f"{symbol} (롱) 수익률: {profit:.2f}% 성공\n취소주문: {cancel_order}")

                    elif info[symbol]['position'] == 'long' and df['low'][-1] < info[symbol]['price'] * bull_loss:
                        profit = (bull_loss - 1) * 100
                        invest_money = info[symbol]['price'] * info[symbol]['amount']
                        indi.saveHistory(strategy, symbol, info[symbol]['position'], invest_money, profit) # 엑셀 파일에 저장
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        logging.info(f"{symbol} (롱) 수익률: {profit:.2f}% 실패\n취소주문: {cancel_order}")

                    # 숏 포지션 이익실현 / 손절 체크
                    elif info[symbol]['position'] == 'short' and df['low'][-1] < info[symbol]['price'] * bear_profit:
                        profit = (1 - bear_profit) * 100
                        invest_money = info[symbol]['price'] * info[symbol]['amount']
                        indi.saveHistory(strategy, symbol, info[symbol]['position'], invest_money, profit) # 엑셀 파일에 저장
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        logging.info(f"{symbol} (숏) 수익률: {profit:.2f}% 성공\n취소주문: {cancel_order}")

                    elif info[symbol]['position'] == 'short' and df['high'][-1] > info[symbol]['price'] * bear_loss:
                        profit = (1 - bear_loss) * 100
                        invest_money = info[symbol]['price'] * info[symbol]['amount']
                        indi.saveHistory(strategy, symbol, info[symbol]['position'], invest_money, profit) # 엑셀 파일에 저장
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        logging.info(f"{symbol} (숏)\n수익률: {profit:.2f}% 실패\n취소주문: {cancel_order}")

            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
                logging.error(e)
            time.sleep(0.1)

        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/binance_short.txt', 'w') as f:
            f.write(json.dumps(info))
