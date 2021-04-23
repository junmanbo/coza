# 이 전략은 심플한 전략입니다.
# 단순히 5일치 이동평균을 구해서 이동평균보다 낮으면 이동평균보다 높으면 파는 전략입니다.
# 1일~5일치로 이루어지는 단타 전략입니다.
from upbitlib import *
import pyupbit
import time

# 객체 생성
f = open("upbit.txt")
lines = f.readlines()
access = lines[0].strip()
secret = lines[1].strip()
f.close()
upbit = pyupbit.Upbit(access, secret)

tickers = pyupbit.get_tickers("KRW") # 코인 전체 불러오기
money = 1000 # 한 코인당 구매 금액

print("자동매매를 시작하겠습니다. 돈 벌어 올테니 코~ 자고 계세요!\n매매할 코인을 찾는 중입니다.....")
while True:
    try:
        for ticker in tickers:
                ma5 = get_yesterday_ma5(ticker)
                price = pyupbit.get_current_price(ticker)
                coin_balance = upbit.get_balance(ticker)
                time.sleep(1)

                if price < ma5 and hold(coin_balance) == False:
                    upbit.buy_market_order(ticker, money)
                    print(f"평균치 {ma5} 보다 낮은 금액 {price}원 입니다. 매수하겠습니다.")

                elif price > ma5 and hold(coin_balance) == True:
                    upbit.sell_market_order(ticker, coin_balance)
                    print(f"평균치 {ma5} 보다 높은 금액 {price}원 입니다. 매도하겠습니다.")
    except:
        pass
