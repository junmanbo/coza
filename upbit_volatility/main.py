#!/usr/bin/python3

import pyupbit
import time
import datetime
from macd import *

#tickers = pyupbit.get_tickers("KRW") # 코인 전체 불러오기
# 시가총액 높은 순서로 35코인
tickers = ["KRW-BTC", "KRW-ETH", "KRW-ADA", "KRW-XRP", "KRW-LTC", "KRW-LINK", "KRW-BCH", "KRW-XLM", "KRW-VET", "KRW-DOGE", "KRW-TRX", "KRW-ATOM", "KRW-THETA", "KRW-DOT", "KRW-CRO", "KRW-EOS", "KRW-BSV", "KRW-BTT", "KRW-XTZ", "KRW-XEM", "KRW-NEO", "KRW-CHZ", "KRW-HBAR", "KRW-TFUEL", "KRW-ENJ", "KRW-NPXS", "KRW-ZIL", "KRW-BAT", "KRW-MANA", "KRW-ETC", "KRW-WAVES", "KRW-ICX", "KRW-ONT", "KRW-ANKR", "KRW-QTUM"]

# 목표가 구하기
def cal_target(ticker):
    df = pyupbit.get_ohlcv(ticker, "day")
    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    yesterday_range = yesterday['high'] - yesterday['low']
    noise = 1 - abs(yesterday['open'] - yesterday['close']) / (yesterday['high'] - yesterday['low'])
#    if noise < 0.5:
#        noise = 0.5
    target = today['open'] + (yesterday_range * noise)
    return target

# 5일치 이동평균선 구하기
def get_yesterday_ma5(ticker):
    df = pyupbit.get_ohlcv(ticker)
    close = df['close']
    ma = close.rolling(window=5).mean()
    return ma[-2]

# 원화 마켓 주문 가격 단위
def price_unit(price):
    if price < 10:
        price = round(price, 2)
    elif 10 <= price < 100:
        price = round(price, 1)
    elif 100 <= price < 1000:
        price = round(price)
    elif 1000 <= price < 100000:
        price = round(price, -1)
    elif 100000 <= price < 1000000:
        price = round(price, -2)
    elif price >= 1000000:
        price = round(price, -3)
    return price

# 오늘 고가가 익절가 보다 높으면 제외
def profit_high(ticker, profit):
    df = pyupbit.get_ohlcv(ticker, "day")
    today = df.iloc[-1]
    if profit < today['high']:
        tickers.remove(ticker)

# 객체 생성
f = open("upbit.txt")
lines = f.readlines()
access = lines[0].strip()
secret = lines[1].strip()
f.close()
upbit = pyupbit.Upbit(access, secret)

# 5만원 이상있으면 작동
def op_mode(my_balance):
    if my_balance < 100000:
        return False
    else:
        return True

# 코인잔고 조회
def hold(coin_balance):
    if coin_balance > 0:
        hold = True
    else:
        hold = False
    return hold

# 지정가 예약 주문 취소
def cancel_order(ticker):
    try:
        ret = upbit.get_order(ticker)[0].get('uuid')
        upbit.cancel_order(ret)
        print(f"{ticker}의 미체결된 거래내역을 취소했습니다.")
    except:
        pass

def order_state(ticker):
    try:
        state = upbit.get_order(ticker)[0].get('state')
        if state == 'wait':
            state = True
        else:
            state = False
    except:
        state = False
    return state

print("자동매매를 시작합니다. 꼭 성투하세요!\n적절한 코인을 찾는중입니다....")

while True:
    try:
        now = datetime.datetime.now()
        for ticker in tickers:
            target = round(cal_target(ticker), 0)  # 목표가격
            my_balance = upbit.get_balance("KRW")  # 원화 잔고
            coin_balance = upbit.get_balance(ticker)  # 코인 잔고
            price = pyupbit.get_current_price(ticker)  # 코인 현재가
            ma = get_yesterday_ma5(ticker)  # 코인 5일 이동평균선

            profit = round((target * 1.004), 0) # 익절 가격
            limit = round((target * 0.998), 0)  # 손절 가격
            profit_high(ticker, profit)

            # 전날 거래 전량 매도
#            if now.hour == 8 and 45 <= now.minute <= 59:
#                if order_state(ticker) == True:
#                    cancel_order(ticker)
#                    time.sleep(3)
#                    coin_balance = upbit.get_balance(ticker)
#                    upbit.sell_market_order(ticker, coin_balance)
#                    print(f"현재시간 {now} 하루가 끝났습니다.\n{ticker} 를 매도 하겠습니다. 오늘은 좋은 결과가 있기를!\n")

#            if now.hour == 9 and now.minute == 0 and 0 <= now.second <= 10:
#                tickers = pyupbit.get_tickers("KRW") # 코인 전체 불러오기
#                print("코인 목록을 초기화 합니다.")
#                time.sleep(10)

            # 조건을 확인한 후 매수
            if op_mode(my_balance) == True and hold(coin_balance) == False and order_state(ticker) == False and target <= price <= (target * 1.001) and ma < price and cal_macd(ticker) == 'buy':
                target = price_unit(target)
                unit = 100000 / target
                upbit.buy_limit_order(ticker, target, unit)
                print(f"현재시간 {now} 코인 {ticker} 을 {price} 가격에 100000원 어치 예약 매수했습니다.")

            elif hold(coin_balance) == True and limit <= price <= profit:
                profit = price_unit(profit)
                upbit.sell_limit_order(ticker, profit, coin_balance) # 목표가로 지정가 예약 매도
                print(f"{ticker}를 매수가격: {target} -> 목표가격: {profit} 으로 예약 매도 주문했습니다.\n")

            # 목표가에서 0.2% 이상 하락하면 손절
            elif hold(coin_balance) == False and order_state(ticker) == True and limit > price:
                cancel_order(ticker)
                time.sleep(2)
                coin_balance = upbit.get_balance(ticker)
                upbit.sell_market_order(ticker, coin_balance)
                print(f"현재시간 {now} 너무 많이 떨어졌네요. {ticker}를 매도 하겠습니다.\n")
            time.sleep(1)
    except:
        pass
