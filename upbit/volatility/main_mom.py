#!/usr/bin/python3

import pyupbit
import time
import datetime
import telegram

tickers = pyupbit.get_tickers("KRW") # 코인 전체 불러오기
#  tickers = ["KRW-BTC", "KRW-ETH", "KRW-ADA", "KRW-XRP", "KRW-LTC", "KRW-LINK", "KRW-BCH", "KRW-XLM", "KRW-VET", "KRW-DOGE", "KRW-ATOM", "KRW-THETA", "KRW-DOT", "KRW-CRO", "KRW-EOS", "KRW-BSV", "KRW-BTT", "KRW-XTZ", "KRW-XEM", "KRW-NEO", "KRW-CHZ", "KRW-HBAR", "KRW-TFUEL", "KRW-ENJ", "KRW-ZIL", "KRW-BAT", "KRW-MANA", "KRW-ETC", "KRW-WAVES", "KRW-ICX", "KRW-ONT", "KRW-ANKR", "KRW-QTUM"]

# telegram setting
my_token = '1725701346:AAFoCMr7xeQwjaqvBsOPoIS99PyRFwVFK_E'
bot = telegram.Bot(token = my_token)
chat_id = '1459236537'

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
    df = pyupbit.get_ohlcv(ticker, "day")
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

# 객체 생성
f = open("upbit.txt")
lines = f.readlines()
access = lines[0].strip()
secret = lines[1].strip()
f.close()
upbit = pyupbit.Upbit(access, secret)

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

bot.sendMessage(chat_id = chat_id, text="추격매수 전략을 실행합니다. 오늘 목표 수익률 단1%!!")

# 거래 횟수
count_trading = 0
count_loose = 0
count_success = 0

hold = False

while True:
    try:
        for ticker in tickers:
            now = datetime.datetime.now()
            time.sleep(0.2)
            target = cal_target(ticker)  # 목표가격
            my_balance = upbit.get_balance("KRW")  # 원화 잔고
            price = pyupbit.get_current_price(ticker)  # 코인 현재가
            ma = get_yesterday_ma5(ticker)  # 코인 5일 이동평균선

            profit = target * 1.015 # 익절 가격
            limit = target * 0.99  # 손절 가격
            print(f"현재시간: {now} 현재잔고: {my_balance} 코인: {ticker}\n현재가: {price} -> 목표가: {target}\n")

            if now.hour == 8 and now.minute == 59 and 50 <= now.second <= 59:
                my_balance = int(my_balance)
                bot.sendMessage(chat_id = chat_id, text=f"잔고: {my_balance}원\n거래횟수: {count_trading}번\n성공횟수: {count_success}\n실패횟수: {count_loose}번")
                count_trading = 0
                count_loose = 0
                count_success = 0
                time.sleep(10)

            # 변동성 돌파전략 조건을 만족하면 지정가 매수
            elif my_balance > 300000 and hold == False and target <= price <= (target * 1.001) and ma < price:
                target = price_unit(target)
                unit = 300000 / target
                upbit.buy_limit_order(ticker, target, unit)
                count_trading += 1
                bot.sendMessage(chat_id = chat_id, text=f"코인: {ticker} 예약매수\n현재가: {price} 거래횟수: {count_trading}번")
                tickers.clear()
                tickers = [ticker]
                hold = True

            # 코인 보유하고 있고 예약매도 없을 경우 지정가 예약매도
            elif hold == True and order_state(ticker) == False and limit < price < profit:
                profit = price_unit(profit)
                coin_balance = upbit.get_balance(ticker)  # 코인 잔고
                upbit.sell_limit_order(ticker, profit, coin_balance) # 목표가로 지정가 예약 매도
                bot.sendMessage(chat_id = chat_id, text=f"코인: {ticker} 예약매도\n매수가: {target} -> 매도가: {profit}")

            elif hold == True and order_state(ticker) == False and profit < price:
                count_success += 1
                my_balance = upbit.get_balance("KRW")  # 원화 잔고
                bot.sendMessage(chat_id = chat_id, text=f"코인: {ticker} 목표달성\n성공횟수: {count_success}번\n잔고: {my_balance}")
                tickers.clear()
                tickers = pyupbit.get_tickers("KRW") # 코인 전체 불러오기
                hold = False

            # 목표가에서 2% 이상 하락하면 손절
            elif hold == True and order_state(ticker) == True and limit >= price:
                cancel_order(ticker)
                time.sleep(1)
                coin_balance = upbit.get_balance(ticker)
                upbit.sell_market_order(ticker, coin_balance)
                time.sleep(1)
                my_balance = upbit.get_balance("KRW")  # 원화 잔고
                count_loose += 1
                bot.sendMessage(chat_id = chat_id, text=f"코인: {ticker} 손절매\n실패횟수: {count_loose}번\n잔고: {my_balance}")
                tickers.clear()
                tickers = pyupbit.get_tickers("KRW") # 코인 전체 불러오기
                hold = False
    except Exception as e:
        print("예외발생", e)
