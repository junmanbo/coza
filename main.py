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
logging.basicConfig(filename='./Log/binance_trading.log', format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

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
with open('./Data/binance_trading.txt', 'r') as f:
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
tickers = binance.load_markets().keys() # 목록 전체 조회
symbols = list(tickers)

# 보유하고 있는 코인 갯수
current_hold = 0
for symbol in symbols:
    if info[symbol]['position'] != 'wait':
        current_hold += 1

total_hold = 5 # 투자할 코인 총 갯수
bull_profit = 1.1 # 롱 포지션 수익률
bull_loss = 0.96 # 롱 포지션 손실률
bear_profit = 0.9 # 숏 포지션 수익률
bear_loss = 1.04 # 숏 포지션 손실률

invest_money = 300
leverage = 5 # 현재 레버리지 값
logging.info(f"{strategy}\n현재보유: {current_hold}개\n투자할 코인: {total_hold-current_hold}개\n기대 수익률: {(bull_profit-1)*100:.2f}%")
bot.sendMessage(chat_id=chat_id, text=f"{strategy}\n현재보유: {current_hold}개\n투자할 코인: {total_hold-current_hold}개\n기대 수익률: {(bull_profit-1)*100:.2f}%")

while True:
    now = datetime.datetime.now()
    time.sleep(1)

    if (now.hour + 3) % 2 == 0 and now.minute == 1 and 0 <= now.second <= 5:
        for symbol in symbols:
            try:
                current_price = binance.fetch_ticker(symbol)['close'] # 현재가 조회
                # 일봉 데이터 수집
                df = getOHLCV(symbol, '1d')
                stoch_osc = indi.calStochastic_OSC(df, 12, 5, 5)
                stoch_slope = indi.calStochastic_Slope(df, 12, 5, 5)
                macd_osc = indi.calMACD_OSC(df, 14, 30, 10)
                macd_slope = indi.calMACD_Slope(df, 14, 30, 10)
                rsi = indi.calRSI(df, 7)
                logging.info(f'코인: {symbol}\n지표: {stoch_osc} {stoch_slope} {macd_osc} {macd_slope} RSI: {rsi}')

                # 조건 만족시 Long Position
                if info[symbol]['position'] == 'wait' and current_hold < total_hold and \
                        stoch_osc < -2 and stoch_slope > 0 and macd_slope > 0 and rsi < 80:
                    # 투자를 위한 세팅
                    amount = invest_money / current_price
                    #  order = binance.create_limit_buy_order(symbol, amount, current_price) # 지정가 매수 주문
                    order = binance.create_market_buy_order(symbol, amount) # 시장가 매수 주문
                    take_profit_params = {'stopPrice': current_price * bull_profit} # 이익실현 예약 주문
                    order1 = binance.create_order(symbol, 'take_profit_market', 'sell', amount, None, take_profit_params)
                    stop_loss_params = {'stopPrice': current_price * bull_loss} # 손절 예약 주문
                    order2 = binance.create_order(symbol, 'stop_market', 'sell', amount, None, stop_loss_params)
                    # 매수가, 포지션 상태, 코인 매수 양 저장
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'long'
                    info[symbol]['amount'] = amount
                    info[symbol]['total_trading'] = 1
                    info[symbol]['total_invest'] = invest_money
                    current_hold += 1
                    logging.info(f"{symbol} (롱)\n투자금액: ${invest_money:.2f}\n현재보유: {current_hold}개\n주문: {order}")
                    bot.sendMessage(chat_id=chat_id, text=f"{symbol} (롱)\n투자금액: ${invest_money:.2f}\n현재보유: {current_hold}개")

                # 조건 만족시 Short Position
                elif info[symbol]['position'] == 'wait' and current_hold < total_hold and \
                        stoch_osc < 0 and stoch_slope < 0 and macd_osc < 0 and macd_slope < 0 and rsi > 30:
                    # 투자를 위한 세팅
                    amount = invest_money / current_price
                    #  order = binance.create_limit_sell_order(symbol, amount, current_price) # 지정가 매도 주문
                    order = binance.create_market_sell_order(symbol, amount) # 시장가 매도 주문
                    take_profit_params = {'stopPrice': current_price * bear_profit} # 이익실현 예약 주문
                    order1 = binance.create_order(symbol, 'take_profit_market', 'buy', amount, None, take_profit_params)
                    stop_loss_params = {'stopPrice': current_price * bear_loss} # 손절 예약 주문
                    order2 = binance.create_order(symbol, 'stop_market', 'buy', amount, None, stop_loss_params)
                    # 매수가, 포지션 상태, 코인 매수 양 저장
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'short'
                    info[symbol]['amount'] = amount
                    info[symbol]['total_trading'] = 1
                    info[symbol]['total_invest'] = invest_money
                    current_hold += 1
                    logging.info(f"{symbol} (숏)\n투자금액: ${invest_money:.2f}\n현재보유: {current_hold}개\n주문: {order}")
                    bot.sendMessage(chat_id=chat_id, text=f"{symbol} (숏)\n투자금액: ${invest_money:.2f}\n현재보유: {current_hold}개")

            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
                logging.error(e)
            time.sleep(0.1)

        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/binance_trading.txt', 'w') as f:
            f.write(json.dumps(info))

    elif now.hour % 4 == 0 and now.minute == 1 and 0 <= now.second <= 5:
        for symbol in symbols:
            try:
                if info[symbol]['position'] != 'wait':
                    current_price = binance.fetch_ticker(symbol)['close'] # 현재가 조회
                    # 일봉 데이터 수집
                    df = getOHLCV(symbol, '1d')
                    stoch_osc = indi.calStochastic_OSC(df, 12, 5, 5)
                    stoch_slope = indi.calStochastic_Slope(df, 12, 5, 5)
                    rsi = indi.calRSI(df, 7)
                    logging.info(f'코인: {symbol}\n지표: {stoch_osc} {stoch_slope} RSI: {rsi}')

                    if info[symbol]['position'] == 'long' and stoch_slope < -1 and rsi > 50:
                        order = binance.create_market_sell_order(symbol, info[symbol]['amount'])
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        # 매수가, 포지션 상태, 코인 매수 양 저장
                        profit = (current_price - info[symbol]['price']) / info[symbol]['price'] * 100
                        indi.saveHistory(strategy, symbol, info[symbol]['position'], info[symbol]['total_invest'], profit) # 엑셀 파일에 저장
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        logging.info(f"{symbol} (롱) 수익률: {profit:.2f}%\n주문: {order}")
                        bot.sendMessage(chat=chat_id, text=f"{symbol} (롱) 수익률: {profit:.2f}%")

                    elif info[symbol]['position'] == 'short' and stoch_osc > -2:
                        order = binance.create_market_buy_order(symbol, info[symbol]['amount'])
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        # 매도가, 포지션 상태, 코인 매수 양 저장
                        profit = (info[symbol]['price'] - current_price) / current_price * 100
                        indi.saveHistory(strategy, symbol, info[symbol]['position'], info[symbol]['total_invest'], profit) # 엑셀 파일에 저장
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        logging.info(f"{symbol} (숏) 수익률: {profit:.2f}%\n주문: {order}")
                        bot.sendMessage(chat=chat_id, text=f"{symbol} (숏) 수익률: {profit:.2f}%")

                    # 추가 매수
                    elif info[symbol]['position'] == 'long' and current_price < info[symbol]['price'] and info[symbol]['total_trading'] < 5:
                        amount = invest_money / current_price
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        order = binance.create_market_buy_order(symbol, amount) # 시장가 매수 주문
                        info[symbol]['amount'] += amount
                        info[symbol]['total_invest'] += invest_money
                        info[symbol]['price'] = info[symbol]['total_invest'] / info[symbol]['amount'] # 평균 단가
                        take_profit_params = {'stopPrice': info[symbol]['price'] * bull_profit} # 이익실현 예약 주문
                        order1 = binance.create_order(symbol, 'take_profit_market', 'sell', info[symbol]['amount'], None, take_profit_params)
                        stop_loss_params = {'stopPrice': info[symbol]['price'] * bull_loss} # 손절 예약 주문
                        order2 = binance.create_order(symbol, 'stop_market', 'sell', info[symbol]['amount'], None, stop_loss_params)
                        info[symbol]['total_trading'] += 1
                        logging.info(f"{symbol} (롱)추매\n투자금액: ${info[symbol]['total_invest']}\n매수횟수: {info[symbol]['total_trading']}\n주문: {order}")
                        bot.sendMessage(chat_id=chat_id, text=f"{symbol}(롱)추매\n투자금액: ${info[symbol]['total_invest']}\n매수횟수: {info[symbol]['total_trading']}")

                    # 추가 매도
                    elif info[symbol]['position'] == 'short' and current_price > info[symbol]['price'] and info[symbol]['total_trading'] < 5:
                        amount = invest_money / current_price
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        order = binance.create_market_sell_order(symbol, amount) # 시장가 매도 주문
                        info[symbol]['amount'] += amount
                        info[symbol]['total_invest'] += invest_money
                        info[symbol]['price'] = info[symbol]['total_invest'] / info[symbol]['amount'] # 평균 단가
                        take_profit_params = {'stopPrice': info[symbol]['price'] * bear_profit} # 이익실현 예약 주문
                        order1 = binance.create_order(symbol, 'take_profit_market', 'buy', info[symbol]['amount'], None, take_profit_params)
                        stop_loss_params = {'stopPrice': info[symbol]['price'] * bear_loss} # 손절 예약 주문
                        order2 = binance.create_order(symbol, 'stop_market', 'buy', info[symbol]['amount'], None, stop_loss_params)
                        info[symbol]['total_trading'] += 1
                        logging.info(f"{symbol} (숏)추매\n투자금액: ${info[symbol]['total_invest']}\n매도횟수: {info[symbol]['total_trading']}\n주문: {order}")
                        bot.sendMessage(chat_id=chat_id, text=f"{symbol}(숏)추매\n투자금액: ${info[symbol]['total_invest']}\n매도횟수: {info[symbol]['total_trading']}")

            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
                logging.error(e)
            time.sleep(0.1)

        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/binance_trading.txt', 'w') as f:
            f.write(json.dumps(info))

    elif now.minute % 30 == 0 and 0 <= now.second <= 5:
        for symbol in symbols:
            try:
                if info[symbol]['position'] != 'wait':
                    current_price = binance.fetch_ticker(symbol)['close'] # 현재가 조회
                    # 30분봉 데이터 수집
                    df = getOHLCV(symbol, '30m')
                    high = df['high'][-1]
                    low = df['low'][-1]
                    logging.info(f'코인: {symbol}\nHigh: {high} Low: {low}')

                    # 롱 포지션 이익실현 / 손절 체크
                    if info[symbol]['position'] == 'long' and high > info[symbol]['price'] * bull_profit:
                        profit = (bull_profit - 1) * 100
                        indi.saveHistory(strategy, symbol, info[symbol]['position'], info[symbol]['total_invest'], profit) # 엑셀 파일에 저장
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        logging.info(f"{symbol} (롱) 수익률: {profit:.2f}% 성공\n취소주문: {cancel_order}")
                        bot.sendMessage(chat_id=chat_id, text=f"{symbol} (롱) 수익률: {profit:.2f}% 성공")

                    elif info[symbol]['position'] == 'long' and low < info[symbol]['price'] * bull_loss:
                        profit = (bull_loss - 1) * 100
                        indi.saveHistory(strategy, symbol, info[symbol]['position'], info[symbol]['total_invest'], profit) # 엑셀 파일에 저장
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        logging.info(f"{symbol} (롱) 수익률: {profit:.2f}% 실패\n취소주문: {cancel_order}")
                        bot.sendMessage(chat_id=chat_id, text=f"{symbol} (롱) 수익률: {profit:.2f}% 실패")

                    # 숏 포지션 이익실현 / 손절 체크
                    elif info[symbol]['position'] == 'short' and low < info[symbol]['price'] * bear_profit:
                        profit = (1 - bear_profit) * 100
                        indi.saveHistory(strategy, symbol, info[symbol]['position'], info[symbol]['total_invest'], profit) # 엑셀 파일에 저장
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        logging.info(f"{symbol} (숏) 수익률: {profit:.2f}% 성공\n취소주문: {cancel_order}")
                        bot.sendMessage(chat_id=chat_id, text=f"{symbol} (숏) 수익률: {profit:.2f}% 성공")

                    elif info[symbol]['position'] == 'short' and high > info[symbol]['price'] * bear_loss:
                        profit = (1 - bear_loss) * 100
                        indi.saveHistory(strategy, symbol, info[symbol]['position'], info[symbol]['total_invest'], profit) # 엑셀 파일에 저장
                        cancel_order = binance.cancel_all_orders(symbol) # 남은 주문 취소
                        info[symbol]['position'] = 'wait'
                        current_hold -= 1
                        logging.info(f"{symbol} (숏)\n수익률: {profit:.2f}% 실패\n취소주문: {cancel_order}")
                        bot.sendMessage(chat_id=chat_id, text=f"{symbol} (숏)\n수익률: {profit:.2f}% 실패")

            except Exception as e:
                bot.sendMessage(chat_id=chat_id, text=f"에러발생 {e}")
                logging.error(e)
            time.sleep(0.1)

        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/binance_trading.txt', 'w') as f:
            f.write(json.dumps(info))
