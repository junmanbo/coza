import pyupbit

ticker = 'KRW-XRP'

# 목표가 구하기
def cal_target(ticker):
    df = pyupbit.get_ohlcv(ticker, "day")
    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    yesterday_range = yesterday['high'] - yesterday['low']
    noise = 1 - abs(yesterday['open'] - yesterday['close']) / (yesterday['high'] - yesterday['low'])
    target = today['open'] + (yesterday_range * noise)
    return target

print(cal_target(ticker))

# 5일치 이동평균선 구하기
def get_yesterday_ma5(ticker):
    df = pyupbit.get_ohlcv(ticker, "day")
    close = df['close']
    ma = close.rolling(window=5).mean()
    return ma[-2]
