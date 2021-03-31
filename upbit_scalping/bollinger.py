#import datetime
import requests
import pandas as pd
#import time
import numpy

def bb(ticker):
    url = "https://api.upbit.com/v1/candles/minutes/5"
    querystring = {"market":ticker,"count":"100"}
    response = requests.request("GET", url, params=querystring)
    data = response.json()
    df = pd.DataFrame(data)
    df=df['trade_price'].iloc[::-1]

    unit=2
    band1=unit*numpy.std(df[len(df)-20:len(df)])
    bb_center=numpy.mean(df[len(df)-20:len(df)])
    band_high=bb_center+band1
    band_low=bb_center-band1
    band_width = (band_high - band_low) / bb_center
    return band_width
