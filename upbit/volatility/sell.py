import pyupbit

ticker = "KRW-HUNT"

f = open("upbit.txt")
lines = f.readlines()
access = lines[0].strip()
secret = lines[1].strip()
f.close()
upbit = pyupbit.Upbit(access, secret)

my_balance = upbit.get_balance("KRW")  # 원화 잔고
print(my_balance)

#  coin_balance = upbit.get_balance(ticker)  # 코인 잔고
#  print(coin_balance)
#
#  sell_order = upbit.sell_market_order(ticker, coin_balance)
#  print(sell_order)
