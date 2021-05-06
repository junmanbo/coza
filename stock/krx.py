from pykrx import stock

tickers = stock.get_market_ticker_list("20210504", market="KOSPI")

#  for ticker in tickers:
#      name = stock.get_market_ticker_name(ticker)
#      print(ticker, name)

df = stock.get_market_ohlcv_by_date("20201104", "20210404", "22640", "m")
print(df)
