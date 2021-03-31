import requests
import pandas as pd
import pyupbit
import numpy as np
#import time

def cal_macd(ticker):
    url = "https://api.upbit.com/v1/candles/minutes/5"

    querystring = {"market":ticker,"count":"100"}
    response = requests.request("GET", url, params=querystring)
    data = response.json()
    df = pd.DataFrame(data)
    df=df.iloc[::-1]
    df=df['trade_price']

#    df = pyupbit.get_ohlcv(ticker, interval="minute5", count=100)
#    df = df.iloc[-1]
#    df = df['close']

    exp1 = df.ewm(span=12, adjust=False).mean()
    exp2 = df.ewm(span=26, adjust=False).mean()
    macd = exp1-exp2
    exp3 = macd.ewm(span=9, adjust=False).mean()

#    print('MACD: ',macd[0])
#    print('Signal: ',exp3[0])

    test1=exp3[0]-macd[0]
    test2=exp3[1]-macd[1]
    call='no'

    if test1<0 and test2>0:
       call='sell'
    if test1>0 and test2<0:
       call='buy'
    return call
