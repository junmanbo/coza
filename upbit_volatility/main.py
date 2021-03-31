#!/usr/bin/python3

import pyupbit
import time
import datetime

tickers = pyupbit.get_tickers("KRW") # 코인 전체 불러오기
# 시가총액 높은 순서로 35코인
#tickers = ["KRW-BTC", "KRW-ETH", "KRW-ADA", "KRW-XRP", "KRW-LTC", "KRW-LINK", "KRW-BCH", "KRW-XLM", "KRW-VET", "KRW-DOGE", "KRW-TRX", "KRW-ATOM", "KRW-THETA", "KRW-DOT", "KRW-CRO", "KRW-EOS", "KRW-BSV", "KRW-BTT", "KRW-XTZ", "KRW-XEM", "KRW-NEO", "KRW-CHZ", "KRW-HBAR", "KRW-TFUEL", "KRW-ENJ", "KRW-NPXS", "KRW-ZIL", "KRW-BAT", "KRW-MANA", "KRW-ETC", "KRW-WAVES", "KRW-ICX", "KRW-ONT", "KRW-ANKR", "KRW-QTUM"]

# 목표가 구하기
def cal_target(ticker):
    df = pyupbit.get_ohlcv(ticker, "day")
    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    yesterday_range = yesterday['high'] - yesterday['low']
    noise = 1 - abs(yesterday['open'] - yesterday['close']) / (yesterday['high'] - yesterday['low'])
    target = today['open'] + (yesterday_range * noise)
    return target

# 5일치 이동평균선 구하기
def get_yesterday_ma5(ticker):
    df = pyupbit.get_ohlcv(ticker)
    close = df['close']
    ma = close.rolling(window=5).mean()
    return ma[-2]

# 객체 생성
f = open("upbit.txt")
lines = f.readlines()
access = lines[0].strip()
secret = lines[1].strip()
f.close()
upbit = pyupbit.Upbit(access, secret)

# 5만원 이상있으면 작동
def op_mode(my_balance):
    if my_balance < 50000:
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
#def cancel_order(ticker):
#    try:
#        ret = upbit.get_order(ticker)[0].get('uuid')
#        upbit.cancel_order(ret)
#        print(f"{ticker}의 미체결된 거래내역을 취소했습니다.")
#    except:
#        pass

# 미체결 주문 조회
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
            time.sleep(1)
            price = pyupbit.get_current_price(ticker)  # 코인 현재가
            ma = get_yesterday_ma5(ticker)  # 코인 5일 이동평균선

            profit = round((target * 1.03), 0) # 익절 가격
            limit = round((target * 0.98), 0)  # 손절 가격

            # 전날 거래 전량 매도
            if now.hour == 8 and 29 <= now.minute <= 59:
                if hold(coin_balance) == True:
                    upbit.sell_market_order(ticker, coin_balance)
                    print(f"현재시간 {now} 하루가 끝났습니다.\n{ticker} 를 매도 하겠습니다. 오늘은 좋은 결과가 있기를!\n")

            elif now.hour == 9 and now.minute == 0 and 0 <= now.second <= 30:
                tickers = pyupbit.get_tickers("KRW") # 코인 전체 불러오기
                time.sleep(30)

            # 조건을 확인한 후 매수
            elif op_mode(my_balance) == True and hold(coin_balance) == False and order_state(ticker) == False and target <= price <= (target * 1.002) and ma < price:
#                upbit.buy_market_order(ticker, 50000)
                unit = 50000 / target
                upbit.buy_limit_order(ticker, target, unit)
                print(f"현재시간 {now} 코인 {ticker} 을 {price} 가격에 50000원 어치 예약 매수했습니다.")

            # 목표가 도달하면 시장가 매도
            elif hold(coin_balance) == True and price > profit:
                upbit.sell_market_order(ticker, coin_balance)
                rate_of_profit = (price - target) / target * 100
                print(f"목표를 달성했습니다! {ticker}를 매수가격: {target} -> 목표가격: {price} 으로 매도했습니다.\n 수익률은 {rate_of_profit}% 입니다.")
                tickers.remove(ticker)

            # 목표가에서 2% 이상 하락하면 손절
            elif hold(coin_balance) == True and price < limit:
                upbit.sell_market_order(ticker, coin_balance)
                rate_of_profit = (price - target) / target * 100
                print(f"현재시간 {now} 너무 많이 떨어졌네요. {ticker}를 매도 하겠습니다.\n수익률은 {rate_of_profit}% 입니다.")
                tickers.remove(ticker)

    except:
        pass
