import pyupbit

# 키 값 입력받기
f = open("upbit.txt")
lines = f.readlines()
access = lines[0].strip()
secret = lines[1].strip()
f.close()
upbit = pyupbit.Upbit(access, secret)

# 변동성 돌파 전략 목표가 구하기
def cal_target(ticker):
    df = pyupbit.get_ohlcv(ticker, "day")
    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    yesterday_range = yesterday['high'] - yesterday['low']
    noise = 1 - abs(yesterday['open'] - yesterday['close']) / (yesterday['high'] - yesterday['low'])
    if noise < 0.5:
        noise = 0.5
    target = today['open'] + (yesterday_range * noise)
    return target

# 5일치 이동평균선 구하기
def get_yesterday_ma5(ticker):
    df = pyupbit.get_ohlcv(ticker)
    close = df['close']
    ma = close.rolling(window=5).mean()
    return ma[-2]

# 계좌 잔고 조회 후 5만원 이상있으면 작동
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

# 지정가 예약 주문 취소
def cancel_order(ticker):
    try:
        ret = upbit.get_order(ticker)[0].get('uuid')
        upbit.cancel_order(ret)
        print(f"{ticker}의 미체결된 거래내역을 취소했습니다.")
    except:
        print("취소할 주문이 없습니다.")
        pass
