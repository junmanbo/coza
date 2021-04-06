from upbit_scalping.macd import cal_macd
from upbit_scalping.stoch_rsi import cal_stoch_rsi
from macd import *
from stoch_rsi import *
import pyupbit
import time
import datetime

tickers = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-LTC", "KRW-LINK", "KRW-BCH", "KRW-XLM", "KRW-TRX", "KRW-VET", "KRW-EOS", "KRW-BTT", "KRW-BSV", "KRW-NEO", "KRW-XEM"]

# 객체 생성
f = open("upbit.txt")
lines = f.readlines()
access = lines[0].strip()
secret = lines[1].strip()
f.close()
upbit = pyupbit.Upbit(access, secret)

start_balance = upbit.get_balance("KRW")
end_balance = upbit.get_balance("KRW")

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

# 예약주문 상태
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

print("자동매매를 시작합니다. 편히 쉬고 계세요 돈은 제가 벌겠습니다 :)")

while True:
    for ticker in tickers:
        try:
            now = datetime.datetime.now()
            price = pyupbit.get_current_price(ticker) # 현재 코인 가격
            stochastic_value = cal_stoch_rsi(ticker)
            macd_value = cal_macd(ticker)
            my_balance = upbit.get_balance("KRW")  # 원화 잔고
            coin_balance = upbit.get_balance(ticker)  # 코인 잔고
            profit = price * 1.007 # 익절 가격
            op = op_mode(my_balance)
            hold_state = hold(coin_balance)
            order = order_state(ticker)

            if stochastic_value == 'buy' and macd_value == 'buy' and op == True and hold == False and order == False:
                price = price_unit(price) # 호가 단위 맞추기
                unit = 100000 / price # 매수할 코인 갯수 계산
                upbit.buy_limit_order(ticker, price, unit) # 지정가 매수
                print(f"코인 {ticker}를 {price} 가격에 10만원 어치 예약매수 했습니다.")

            elif hold(coin_balance) == True:
                profit = price_unit(profit) # 호가 단위 맞추기
                upbit.sell_limit_order(ticker, profit, coin_balance) # 예약 매도
                print(f"{ticker}를 매수가격: {price} -> 목표가격: {profit} 으로 예약 매도 주문했습니다.\n")

            elif (now.minute == 15 or now.minute == 30 or now.minute == 45 or now.minute == 0) and order == True and hold_state == False:
                cancel_order(ticker)
                coin_balance = upbit.get_balance(ticker)
                upbit.sell_market_order(ticker, coin_balance)
                print(f"15분이 지나서 {ticker}를 매도했습니다.")
        except:
            pass
        time.sleep(1)
