#!/usr/bin/env python

import ccxt
import pandas as pd
import numpy as np
import datetime
import time
import telegram
import json
import logging
import os

# 경로 설정
home = os.getcwd()
path_log = home + '/Log/'
path_api = home + '/Api/'
path_data = home + '/Data/'

# 로깅 설정
logging.basicConfig(filename=path_log+'binance_short.log', format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

# telegram 설정
with open(path_api+'mybot.txt') as f:
    lines = f.readlines()
    my_token = lines[0].strip()
    chat_id = lines[1].strip()
bot = telegram.Bot(token = my_token)

# 거래소 설정
with open(path_api+'binance.txt') as f:
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
with open(path_data+'binance_short.txt', 'r') as f:
    data = f.read()
    info = json.loads(data)

# 지수 이동평균 계산
def calMA(df, fast=14):
    df['ma'] = df['close'].ewm(span=fast).mean()
    return df['ma'][-1]

# Stochastic 계산
def calStochastic(df, n=12, m=5, t=5):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    slow_osc_slope = slow_osc - slow_osc.shift(1)
    df['slow_osc'] = slow_osc
    df['slow_osc_slope'] = slow_osc_slope
    return df['slow_osc'][-1], df['slow_osc_slope'][-1]

# MACD 계산
def calMACD(df, m_NumFast=14, m_NumSlow=30, m_NumSignal=10):
    EMAFast = df.close.ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
    EMASlow = df.close.ewm( span = m_NumSlow, min_periods = m_NumSlow - 1 ).mean()
    MACD = EMAFast - EMASlow
    MACDSignal = MACD.ewm( span = m_NumSignal, min_periods = m_NumSignal - 1 ).mean()
    MACDOSC = MACD - MACDSignal
    df['macd_osc'] = MACDOSC - MACDOSC.shift(1)
    return df['macd_osc'][-1]

# RSI 계산
def calRSI(df, N=14):

    df['U'] = np.where(df.close.diff(1) > 0, df.close.diff(1), 0)
    df['D'] = np.where(df.close.diff(1) < 0, df.close.diff(1) * (-1), 0)
    df['AU'] = df['U'].rolling( window=N, min_periods=N).mean()
    df['AD'] = df['D'].rolling( window=N, min_periods=N).mean()
    df['RSI'] = df['AU'] / (df['AD']+df['AU']) * 100
    return df['RSI'][-1]

# 코인별 정보값 info 딕셔너리에 저장
def save_info():
    logging.info('Stochastic + MACD + EMA + RSI 데이터 분석중...')
    for symbol in symbols:
        # 일봉 데이터 수집
        ohlcv = binance.fetch_ohlcv(symbol, '1d')
        df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)

        info[symbol]['sotch_osc_d'] = calStochastic(df)[0]
        info[symbol]['stoch_slope_d'] = calStochastic(df)[1]
        info[symbol]['macd_osc'] = calMACD(df)
        info[symbol]['ma'] = calMA(df)
        info[symbol]['rsi'] = calRSI(df)
        info[symbol]['close'] = df['close'][-1]
        info[symbol]['high'] = df['high'][-1]
        info[symbol]['low'] = df['low'][-1]

        # 4시봉 데이터 수집
        ohlcv = binance.fetch_ohlcv(symbol, '4h')
        df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)

        info[symbol]['stoch_slope_4h'] = calStochastic(df)[1]

        # 1시봉 데이터 수집
        ohlcv = binance.fetch_ohlcv(symbol, '1h')
        df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)

        info[symbol]['stoch_slope_1h'] = calStochastic(df)[1]

        time.sleep(0.1)
    logging.info('분석 끝, 저장 완료')

# Coin 목록 불러오기
tickers = binance.load_markets().keys()
symbols = list(tickers)

# 보유하고 있는 코인 갯수
current_hold = 0
for symbol in symbols:
    if info[symbol]['position'] != 'wait':
        current_hold += 1

total_hold = 2 # 투자할 코인 총 갯수
bull_profit = 1.012 # 롱 포지션 수익률
bear_profit = 0.988 # 숏 포지션 수익률
check = False

# 거래에서 제외하고 싶은 코인
except_coin = ['BTC/USDT', 'ETH/USDT']
for coin in except_coin:
    symbols.remove(coin)

bot.sendMessage(chat_id = chat_id, text=f"스토캐스틱(단타)\n현재보유: {current_hold}개\n투자할 코인: {total_hold-current_hold}개\n기대 수익률: {(bull_profit-1)*100:.2f}%")
logging.info(f"스토캐스틱(단타)\n현재보유: {current_hold}개\n투자할 코인: {total_hold-current_hold}개\n기대 수익률: {(bull_profit-1)*100:.2f}%")

while True:
    now = datetime.datetime.now()
    time.sleep(1)
    # 익절한 코인 및 손절할 코인 체크
    if now.minute == 55 and 0 <= now.second <= 9:
        save_info() # 분석 정보 저장
        for symbol in symbols:
            try:
                # 익절한 Coin 체크
                if info[symbol]['position'] == 'long' and info[symbol]['high'] > info[symbol]['price'] * bull_profit:
                    current_hold -= 1
                    info[symbol]['position'] = 'wait'
                    profit = (bull_profit - 1) * 100
                    bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} (롱)\n수익률: {profit:.2f}%\n성공")

                elif info[symbol]['position'] == 'short' and info[symbol]['low'] < info[symbol]['price'] * bear_profit:
                    current_hold -= 1
                    info[symbol]['position'] = 'wait'
                    profit = (1 - bear_profit) * 100
                    bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} (숏)\n수익률: {profit:.2f}%\n성공")

                # 롱 포지션 청산
                elif info[symbol]['position'] == 'long' and info[symbol]['stoch_slope_4h'] < 0:
                    binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=info[symbol]['amount'], params={"reduceOnly": True})
                    current_hold -= 1
                    info[symbol]['position'] = 'wait'
                    current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                    profit = (current_price - info[symbol]['price']) / info[symbol]['price'] * 100 # 수익률 계산
                    bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} (롱)\n수익률: {profit:.2f}%\n실패")

                # 숏 포지션 청산
                elif info[symbol]['position'] == 'short' and info[symbol]['stoch_slope_4h'] > 0:
                    binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=info[symbol]['amount'], params={"reduceOnly": True}) # 포지션 청산
                    current_hold -= 1
                    info[symbol]['position'] = 'wait'
                    current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                    profit = (info[symbol]['price'] - current_price) / current_price * 100 # 수익률 계산
                    bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} (숏)\n수익률: {profit:.2f}%\n실패")
            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"Occured an error {e}")
                logging.error(f"Occured an error {e}")
        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open(path_data+'binance_short.txt', 'w') as f:
            f.write(json.dumps(info))
        if now.hour == 8:
            check = True

    elif check == True and current_hold < total_hold:
        free_balance = binance.fetch_balance()['USDT']['free']
        invest_money = free_balance * 4 / (total_hold - current_hold)
        logging.info('체크 끝 - 당일 거래 시작')
        for symbol in symbols:
            try:
                current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                # 조건 만족시 Long Position
                if info[symbol]['position'] == 'wait' and info[symbol]['rsi'] < 70 and \
                        info[symbol]['stoch_osc_d'] > 0 and info[symbol]['stoch_slope_d'] > 0 and \
                        info[symbol]['macd_osc'] > 0 and info[symbol]['close'] > info[symbol]['ma'] and \
                        info[symbol]['stoch_slope_4h'] > 0 and info[symbol]['stoch_slope_1h'] > 0:
                    amount = invest_money / current_price # 거래할 Coin 갯수
                    binance.create_limit_buy_order(symbol, amount, current_price) # 지정가 매수
                    take_profit_params = {'stopPrice': current_price * bull_profit} # 이익실현 옵션
                    binance.create_order(symbol, 'take_profit_market', 'sell', amount, None, take_profit_params) # 이익실현 예약 주문
                    info[symbol]['price'] = current_price # 현재가 저장
                    info[symbol]['position'] = 'long' # Position 'long' 으로 변경
                    info[symbol]['amount'] = amount # Coin 갯수 저장
                    current_hold += 1
                    bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} (롱)\n투자금액: ${invest_money:.2f}\n현재보유: {current_hold}개\n거래")
                    logging.info(f"{symbol} (롱)\n매수가: ${current_price}\n투자금액: ${invest_money:.2f}\n현재보유: {current_hold}개\n거래")

                # 조건 만족시 Short Position
                elif info[symbol]['position'] == 'wait' and info[symbol]['rsi'] > 30 and \
                        info[symbol]['stoch_osc_d'] < 0 and info[symbol]['stoch_slope_d'] < 0 and \
                        info[symbol]['macd_osc'] < 0 and info[symbol]['close'] < info[symbol]['ma'] and \
                        info[symbol]['stoch_slope_4h'] < 0 and info[symbol]['stoch_slope_1h'] < 0:
                    amount = invest_money / current_price # 거래할 Coin 갯수
                    binance.create_limit_sell_order(symbol, amount, current_price) # 지정가 매도
                    take_profit_params = {'stopPrice': current_price * bear_profit} # 이익실현 옵션
                    binance.create_order(symbol, 'take_profit_market', 'buy', amount, None, take_profit_params) # 이익실현 예약 주문
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'short' # Position 'short' 으로 변경
                    info[symbol]['amount'] = amount # Coin 갯수 저장
                    current_hold += 1
                    bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} (숏)\n투자금액: ${invest_money:.2f}\n현재보유: {current_hold}개\n거래")
                    logging.info(f"{symbol} (숏)\n매도가: ${current_price}\n투자금액: ${invest_money:.2f}\n현재보유: {current_hold}개\n거래")
            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"Occured an error {e}")
                logging.info(f"Occured an error {e}")
        with open(path_data+'binance_short.txt', 'w') as f:
            f.write(json.dumps(info))
        logging.info('거래 끝')
        check = False
