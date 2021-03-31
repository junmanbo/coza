import pyupbit

ticker = "KRW-MTL"

# 객체 생성
f = open("upbit.txt")
lines = f.readlines()
access = lines[0].strip()
secret = lines[1].strip()
f.close()
upbit = pyupbit.Upbit(access, secret)

def cal_target(ticker):
    df = pyupbit.get_ohlcv(ticker, "day")
    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    yesterday_range = yesterday['high'] - yesterday['low']
    noise = 1 - abs(yesterday['open'] - yesterday['close']) / (yesterday['high'] - yesterday['low'])
    target = today['open'] + (yesterday_range * noise)
    return target

target = round(cal_target(ticker), 0)  # 목표가격
price = pyupbit.get_current_price(ticker)
profit = int(round(target * 1.05, 0))
coin_balance = upbit.get_balance(ticker)  # 코인 잔고

print(upbit.sell_limit_order(ticker, profit, coin_balance))# 목표가로 지정가 예약 매도
print(f"현재가: {price} 익절가격: {profit} 코인잔고: {coin_balance}")
