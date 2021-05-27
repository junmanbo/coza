#!/usr/bin/env python

import ccxt
import datetime
import time
import telegram
import json
import logging
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
with open('./Data/binance_swing.json', 'r') as f:
    data = f.read()
    info = json.loads(data)

# 코인별 정보값 info 딕셔너리에 저장
def save_info(symbol):
    # 일봉 데이터 수집
    df = indi.getOHLCV(binance, symbol, '1d')
    info[symbol]['stoch_osc'] = indi.calStochastic(df, 12, 5, 5)[0]
    info[symbol]['stoch_slope'] = indi.calStochastic(df, 12, 5, 5)[1]

# 전략 이름
strategy = 'Swing'
# Coin 목록 불러오기
tickers = ('BTC/USDT', 'ETH/USDT')
symbols = list(tickers)

invest_money = 100

while True:
    now = datetime.datetime.now()
    time.sleep(1)
    # 익절한 코인 및 손절할 코인 체크
    if (now.hour +3) % 4 == 0 and now.minute == 0 and 0 <= now.second <= 1:
        for symbol in symbols:
            try:
                save_info(symbol)
                current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                # 롱 포지션 청산
                if info[symbol]['position'] == 'long' and info[symbol]['stoch_osc'] < 0:
                    binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=info[symbol]['amount'], params={"reduceOnly": True}) # 포지션 청산
                    current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                    profit = (current_price - info[symbol]['price']) / info[symbol]['price'] * 100 # 수익률 계산
                    invest_money = info[symbol]['price'] * info[symbol]['amount']
                    indi.saveHistory(strategy=strategy, symbol=symbol, position=info[symbol]['position'], invest_money=invest_money, profit_rate=profit)
                    info[symbol]['position'] = 'wait'
                    info[symbol]['total_trading'] = 0
                    logging.info(f"{symbol} (롱)\n수익률: {profit:.2f}%")

                # 숏 포지션 청산
                elif info[symbol]['position'] == 'short' and info[symbol]['stoch_osc'] > 0:
                    binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=info[symbol]['amount'], params={"reduceOnly": True}) # 포지션 청산
                    current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                    profit = (info[symbol]['price'] - current_price) / current_price * 100 # 수익률 계산
                    invest_money = info[symbol]['price'] * info[symbol]['amount']
                    indi.saveHistory(strategy=strategy, symbol=symbol, position=info[symbol]['position'], invest_money=invest_money, profit_rate=profit)
                    info[symbol]['position'] = 'wait'
                    info[symbol]['total_trading'] = 0
                    logging.info(f"{symbol} (숏)\n수익률: {profit:.2f}%")

                # 롱 포지션이면서 마이너스일 경우 추가 매수
                elif info[symbol]['position'] == 'long' and info[symbol]['stoch_slope'] > 0 and current_price < info[symbol]['price']:
                    amount = invest_money / current_price # 거래할 Coin 갯수
                    binance.create_limit_buy_order(symbol, amount, current_price) # 지정가 매수
                    info[symbol]['total_trading'] += 1 # 분할매수 횟수
                    info[symbol]['amount'] += amount # Coin 갯수 저장
                    info[symbol]['price'] = 100 * info[symbol]['total_trading'] / info[symbol]['amount'] # 평균 매수 단가
                    logging.info(f"{symbol} (롱)\n평균매수단가: ${info[symbol]['price']}\n총 투자금액: ${info[symbol]['total_trading'] *100}\n추가매수")

                # 숏 포지션이면서 마이너스일 경우 추가 매수
                elif info[symbol]['position'] == 'short' and info[symbol]['stoch_slope'] < 0 and current_price > info[symbol]['price']:
                    amount = invest_money / current_price # 거래할 Coin 갯수
                    binance.create_limit_sell_order(symbol, amount, current_price) # 지정가 매도
                    info[symbol]['total_trading'] += 1 # 분할매도 횟수
                    info[symbol]['amount'] += amount # Coin 갯수 저장
                    info[symbol]['price'] = 100 * info[symbol]['total_trading'] / info[symbol]['amount'] # 평균 매도 단가
                    logging.info(f"{symbol} (숏)\n평균매도단가: ${info[symbol]['price']}\n총 투자금액: ${info[symbol]['total_trading'] *100}\n추가매도")

                # 조건 만족시 Long Position
                elif info[symbol]['position'] == 'wait' and now.hour == 9 and \
                        info[symbol]['stoch_osc'] > 0 and info[symbol]['stoch_slope'] > 0:
                    amount = invest_money / current_price # 거래할 Coin 갯수
                    binance.create_limit_buy_order(symbol, amount, current_price) # 지정가 매수
                    info[symbol]['price'] = current_price # 현재가 저장
                    info[symbol]['position'] = 'long' # Position 'long' 으로 변경
                    info[symbol]['amount'] = amount # Coin 갯수 저장
                    info[symbol]['total_trading'] += 1
                    logging.info(f"{symbol} (롱)\n매수가: ${current_price}\n투자금액: ${invest_money:.2f}\n거래")

                # 조건 만족시 Short Position
                elif info[symbol]['position'] == 'wait' and now.hour == 9 and \
                        info[symbol]['stoch_osc'] < 0 and info[symbol]['stoch_slope'] < 0:
                    amount = invest_money / current_price # 거래할 Coin 갯수
                    binance.create_limit_sell_order(symbol, amount, current_price) # 지정가 매도
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'short' # Position 'short' 으로 변경
                    info[symbol]['amount'] = amount # Coin 갯수 저장
                    info[symbol]['total_trading'] += 1
                    logging.info(f"{symbol} (숏)\n매도가: ${current_price}\n투자금액: ${invest_money:.2f}\n거래")

            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
                logging.error(f"에러발생 {e}")

        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/binance_swing.json', 'w') as f:
            f.write(json.dumps(info))
