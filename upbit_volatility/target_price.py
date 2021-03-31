import pyupbit

def cal_target(ticker):
    df = pyupbit.get_ohlcv(ticker, "day")
    yesterday = df.iloc[-2]
    yesterday_price = yesterday['close']
    today = df.iloc[-1]
    yesterday_range = yesterday['high'] - yesterday['low']
    noise = 1 - abs(yesterday['open'] - yesterday['close']) / (yesterday['high'] - yesterday['low'])
#    if noise < 0.5:
#        noise = 0.5
    target = today['open'] + (yesterday_range * noise)
    difference = (target - yesterday_price) / yesterday_price * 100
    print(f"어제 종가: {yesterday_price} 목표가: {target} 오늘 시가와의 차이: {difference}% noise: {noise}")
    #return target

print(cal_target("KRW-TRX"))
