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

# 전략 이름
strategy = 'Swing'
# Coin 목록 불러오기
tickers = ('BTC/USDT', 'ETH/USDT')
symbols = list(tickers)

invest_money = 150

while True:
    now = datetime.datetime.now()
    time.sleep(1)
    # 익절한 코인 및 손절할 코인 체크
    if (now.hour +3) % 4 == 0 and now.minute == 0 and 0 <= now.second <= 1:
        for symbol in symbols:
            try:
                # 일봉 데이터 수집
                df = getOHLCV(symbol, '1d')
                stoch_osc = indi.calStochastic(df, 12, 5, 5)[0]
                stoch_slope = indi.calStochastic(df, 12, 5, 5)[1]
                current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                logging.info(f"{symbol} Stochastic: OSC {stoch_osc} Slope {stoch_slope}")

                # 롱 포지션 청산
                if info[symbol]['position'] == 'long' and stoch_osc < 0:
                    order = binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=info[symbol]['amount'], params={"reduceOnly": True}) # 포지션 청산
                    profit = (current_price - info[symbol]['price']) / info[symbol]['price'] * 100 # 수익률 계산
                    invest_money = info[symbol]['price'] * info[symbol]['amount'] # 투자금액
                    indi.saveHistory(strategy, symbol, info[symbol]['position'], invest_money, profit)
                    info[symbol]['position'] = 'wait'
                    info[symbol]['total_trading'] = 0 # 분할 매수 횟수
                    logging.info(f"{symbol} (롱) 수익률: {profit:.2f}% 청산\n주문: {order}")

                # 숏 포지션 청산
                elif info[symbol]['position'] == 'short' and stoch_osc > 0:
                    binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=info[symbol]['amount'], params={"reduceOnly": True}) # 포지션 청산
                    profit = (info[symbol]['price'] - current_price) / current_price * 100 # 수익률 계산
                    invest_money = info[symbol]['price'] * info[symbol]['amount']
                    indi.saveHistory(strategy, symbol, info[symbol]['position'], invest_money, profit)
                    info[symbol]['position'] = 'wait'
                    info[symbol]['total_trading'] = 0 # 분할 매수 횟수
                    logging.info(f"{symbol} (숏) 수익률: {profit:.2f}% 청산\n주문: {order}")

                # 롱 포지션이면서 마이너스일 경우 추가 매수
                elif info[symbol]['position'] == 'long' and current_price < info[symbol]['price']:
                    amount = invest_money / current_price # 거래할 Coin 갯수
                    order = binance.create_limit_buy_order(symbol, amount, current_price) # 지정가 매수
                    info[symbol]['total_trading'] += 1 # 분할매수 횟수
                    info[symbol]['amount'] += amount # Coin 갯수 저장
                    info[symbol]['price'] = invest_money * info[symbol]['total_trading'] / info[symbol]['amount'] # 평균 매수 단가
                    logging.info(f"{symbol} (롱) 평균매수단가: ${info[symbol]['price']} 총 투자금액: ${info[symbol]['total_trading'] * invest_money} 추가매수\n주문: {order}")

                # 숏 포지션이면서 마이너스일 경우 추가 매도
                elif info[symbol]['position'] == 'short' and current_price > info[symbol]['price']:
                    amount = invest_money / current_price # 거래할 Coin 갯수
                    order = binance.create_limit_sell_order(symbol, amount, current_price) # 지정가 매도
                    info[symbol]['total_trading'] += 1 # 분할매도 횟수
                    info[symbol]['amount'] += amount # Coin 갯수 저장
                    info[symbol]['price'] = invest_money * info[symbol]['total_trading'] / info[symbol]['amount'] # 평균 매도 단가
                    logging.info(f"{symbol} (숏) 평균매도단가: ${info[symbol]['price']} 총 투자금액: ${info[symbol]['total_trading'] * invest_money} 추가매도\n주문: {order}")

                # 조건 만족시 Long Position
                elif info[symbol]['position'] == 'wait' and stoch_osc > 0 and stoch_slope > 0:
                    amount = invest_money / current_price # 거래할 Coin 갯수
                    order = binance.create_limit_buy_order(symbol, amount, current_price) # 지정가 매수
                    info[symbol]['price'] = current_price # 현재가 저장
                    info[symbol]['position'] = 'long' # Position 'long' 으로 변경
                    info[symbol]['amount'] = amount # Coin 갯수 저장
                    info[symbol]['total_trading'] += 1
                    logging.info(f"{symbol} (롱) 매수가: ${current_price} 투자금액: ${invest_money:.2f} 거래\n주문: {order}")

                # 조건 만족시 Short Position
                elif info[symbol]['position'] == 'wait' and values[0] < 0 and values[1] < 0:
                    amount = invest_money / current_price # 거래할 Coin 갯수
                    binance.create_limit_sell_order(symbol, amount, current_price) # 지정가 매도
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'short' # Position 'short' 으로 변경
                    info[symbol]['amount'] = amount # Coin 갯수 저장
                    info[symbol]['total_trading'] += 1
                    logging.info(f"{symbol} (숏) 매도가: ${current_price} 투자금액: ${invest_money:.2f} 거래\n주문: {order}")

            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
                logging.error(f"에러발생 {e}")

        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/binance_swing.txt', 'w') as f:
            f.write(json.dumps(info))