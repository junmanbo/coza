from pykrx import stock
import pandas as pd
import numpy as np
import datetime
import time


#      name = stock.get_market_ticker_name(ticker)
#      print(ticker, name)


tickers = stock.get_market_ticker_list("20210504", market="KOSPI")
for ticker in tickers:
    df = stock.get_market_ohlcv_by_date("20201104", "20210404", ticker, "m")
    name = stock.get_market_ticker_name(ticker)
    profit = (df['종가'][-1] - df['종가'][0]) / df['종가'][0] * 100
    print(f"종목: {name}\n6개월간 수익률: {profit}\n")
    with open("Profit6M.txt", 'a') as f:
        f.write(f"종목: {name}\n6개월간 수익률: {profit}\n\n")
    time.sleep(1)
