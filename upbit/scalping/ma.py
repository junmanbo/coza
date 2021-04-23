import pandas as pd
#import datetime
import requests
import pandas as pd
import time
#import numpy as np

def cal_ma(ticker):
    url = "https://api.upbit.com/v1/candles/minutes/5"
    querystring = {"market":ticker,"count":"100"}
    response = requests.request("GET", url, params=querystring)
    data = response.json()
    df = pd.DataFrame(data)
    df=df['trade_price'].iloc[::-1]

    ma9 = df.rolling(window=9).mean()
    ma26 = df.rolling(window=26).mean()

    test1=ma9.iloc[-2]-ma26.iloc[-2]
    test2=ma9.iloc[-1]-ma26.iloc[-1]

    call='no'

    if test1>0 and test2<0:
        call='dead'

    if test1<0 and test2>0:
        call='golden'
    return call
