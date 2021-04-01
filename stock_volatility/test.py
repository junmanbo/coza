from pykrx import stock

#tickers = stock.get_market_ticker_list("20210401") # 특정 시점의 상장된 주식 조회
#print(tickers)

#tickers = stock.get_market_ticker_list("20210401", market="KOSDAQ") # 특정 시장에서 특정 시점의 상장된 주식 조회
#print(tickers)

# 주식 종목 이름으로 반환
#for ticker in stock.get_market_ticker_list(market="KOSDAQ"):
#    share = stock.get_market_ticker_name(ticker)
#    print(share)

df = stock.get_market_ohlcv_by_date("20200720", "20200810", "005930")
print(df.head(3))

