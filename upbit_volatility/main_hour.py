#!/usr/bin/python3

import pyupbit
import time
import datetime
import telegram

#tickers = pyupbit.get_tickers("KRW") # 코인 전체 불러오기
# 시가총액 높은 순서로 35코인
tickers = ["KRW-BTC", "KRW-ETH", "KRW-ADA", "KRW-XRP", "KRW-LTC", "KRW-LINK", "KRW-BCH", "KRW-XLM", "KRW-VET", "KRW-DOGE", "KRW-TRX", "KRW-ATOM", "KRW-THETA", "KRW-DOT", "KRW-CRO", "KRW-EOS", "KRW-BSV", "KRW-BTT", "KRW-XTZ", "KRW-XEM", "KRW-NEO", "KRW-CHZ", "KRW-HBAR", "KRW-TFUEL", "KRW-ENJ", "KRW-ZIL", "KRW-BAT", "KRW-MANA", "KRW-ETC", "KRW-WAVES", "KRW-ICX", "KRW-ONT", "KRW-ANKR", "KRW-QTUM"]

# telegram setting
my_token = '1623206706:AAHii0cbgXD287hBsNTjSjeTjnOW9R7-zvQ'
bot = telegram.Bot(token = my_token)
chat_id = '1459236537'

# 목표가 구하기
def cal_target(ticker):
    df = pyupbit.get_ohlcv(ticker, "minute60")
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
    df = pyupbit.get_ohlcv(ticker, "minute60")
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

# 10만원 이상있으면 작동
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

# 거래 횟수
count_trading = 0

# 실패 횟수 count
count_loose = 0

while True:
    try:
        now = datetime.datetime.now()
        for ticker in tickers:
            time.sleep(0.2)
            target = cal_target(ticker)  # 목표가격
            my_balance = upbit.get_balance("KRW")  # 원화 잔고
            coin_balance = upbit.get_balance(ticker)  # 코인 잔고
            price = pyupbit.get_current_price(ticker)  # 코인 현재가
            ma = get_yesterday_ma5(ticker)  # 코인 5일 이동평균선

            profit = target * 1.02 # 익절 가격
            limit = target * 0.98  # 손절 가격

            if now.hour == 23 and now.minute == 59:
                my_balance = int(my_balance)
                bot.sendMessage(chat_id = chat_id, text=f"현재 잔액은{my_balance}원 입니다.\n오늘은 총 {count_trading}번 거래했고 {count_loose}번 실패했습니다.")
                count_trading = 0
                count_loose = 0
                time.sleep(60)

            # 변동성 돌파전략 조건을 만족하면 지정가 매수
            elif op_mode(my_balance) == True and hold(coin_balance) == False and order_state(ticker) == False and target <= price <= (target * 1.001) and ma < price:
                target = price_unit(target)
                unit = 100000 / target
                upbit.buy_limit_order(ticker, target, unit)
                count_trading += 1
                print(f"현재시간 {now} 코인 {ticker} 을 {price} 가격에 100000원 어치 예약 매수했습니다.\n현재 거래횟수 {count_trading}번")

            # 코인 보유하고 있고 예약매도 없을 경우 지정가 예약매도
            elif hold(coin_balance) == True:
                profit = price_unit(profit)
                upbit.sell_limit_order(ticker, profit, coin_balance) # 목표가로 지정가 예약 매도
                print(f"{ticker}를 매수가격: {target} -> 목표가격: {profit} 으로 예약 매도 주문했습니다.\n")

            # 목표가에서 2% 이상 하락하면 손절
            elif hold(coin_balance) == False and order_state(ticker) == True and limit >= price:
                cancel_order(ticker)
                time.sleep(1)
                coin_balance = upbit.get_balance(ticker)
                upbit.sell_market_order(ticker, coin_balance)
                count_loose += 1
                print(f"현재시간 {now} 너무 많이 떨어졌네요. {ticker}를 매도 하겠습니다.\n현재 실패횟수 {count_loose}번")
    except:
        pass
