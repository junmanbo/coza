import pandas as pd
#import datetime
import requests
import pandas as pd
import time

while True:
    url = "https://api.upbit.com/v1/candles/minutes/5"
    querystring = {"market":"KRW-BTC","count":"100"}
    response = requests.request("GET", url, params=querystring)
    data = response.json()
    df = pd.DataFrame(data)
    df=df.iloc[::-1]
    high_prices = df['high_price']
    close_prices = df['trade_price']
    low_prices = df['low_price']
    dates = df.index
    nine_period_high =  df['high_price'].rolling(window=9).max()
    nine_period_low = df['low_price'].rolling(window=9).min()
    df['tenkan_sen'] = (nine_period_high + nine_period_low) /2
    period26_high = high_prices.rolling(window=26).max()
    period26_low = low_prices.rolling(window=26).min()
    df['kijun_sen'] = (period26_high + period26_low) / 2
    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
    period52_high = high_prices.rolling(window=52).max()
    period52_low = low_prices.rolling(window=52).min()
    df['senkou_span_b'] = ((period52_high + period52_low) / 2).shift(26)
    df['chikou_span'] = close_prices.shift(-26)

    print('전환선: ',df['tenkan_sen'].iloc[-1])
    print('기준선: ',df['kijun_sen'].iloc[-1])
    print('후행스팬: ',df['chikou_span'].iloc[-27])
    print('선행스팬1: ',df['senkou_span_a'].iloc[-1])
    print('선행스팬2: ',df['senkou_span_b'].iloc[-1])
    print('')
    time.sleep(1)
