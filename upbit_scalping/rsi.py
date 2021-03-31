import requests
import pandas as pd
#import time

def cal_rsi(ticker):
    url = "https://api.upbit.com/v1/candles/minutes/5"
    querystring = {"market":ticker,"count":"100"}
    response = requests.request("GET", url, params=querystring)
    data = response.json()
    df = pd.DataFrame(data)
    df=df.reindex(index=df.index[::-1]).reset_index()
    df['close']=df["trade_price"]

    def get_rsi(ohlc: pd.DataFrame, period: int = 14):
        ohlc["close"] = ohlc["close"]
        delta = ohlc["close"].diff()

        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0

        _gain = up.ewm(com=(period - 1), min_periods=period).mean()
        _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()

        RS = _gain / _loss
        return pd.Series(100 - (100 / (1 + RS)), name="RSI")

    rsi = get_rsi(df, 14).iloc[-1]
    last_rsi = get_rsi(df, 14).iloc[-2]

    if rsi - last_rsi > 10:
        result = True
    else:
        result = False
    return result
