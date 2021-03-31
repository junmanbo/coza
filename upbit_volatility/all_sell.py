import pyupbit

#tickers = pyupbit.get_tickers("KRW") # 코인 전체 불러오기
tickers = ["KRW-BTC", "KRW-ETH", "KRW-ADA", "KRW-XRP", "KRW-LTC", "KRW-LINK", "KRW-BCH", "KRW-XLM", "KRW-VET", "KRW-DOGE", "KRW-TRX", "KRW-ATOM", "KRW-THETA", "KRW-DOT", "KRW-CRO", "KRW-EOS", "KRW-BSV", "KRW-BTT", "KRW-XTZ", "KRW-XEM", "KRW-NEO", "KRW-CHZ", "KRW-HBAR", "KRW-TFUEL", "KRW-ENJ", "KRW-NPXS", "KRW-ZIL", "KRW-BAT", "KRW-MANA", "KRW-ETC", "KRW-WAVES", "KRW-ICX", "KRW-ONT", "KRW-ANKR", "KRW-QTUM"]

# 객체 생성
f = open("upbit.txt")
lines = f.readlines()
access = lines[0].strip()
secret = lines[1].strip()
f.close()
upbit = pyupbit.Upbit(access, secret)

for ticker in tickers:
    coin_balance = upbit.get_balance(ticker)  # 코인 잔고
    if coin_balance > 0:
        upbit.sell_market_order(ticker, coin_balance)
        print(f"{ticker} 를 팔았습니다.")

print("다 팔았습니다.")
