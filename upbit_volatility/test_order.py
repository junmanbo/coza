import pyupbit

def search_order(ticker):
    ret = upbit.get_order(ticker)[0].get('state')
    print(ret)

# 객체 생성
f = open("upbit.txt")
lines = f.readlines()
access = lines[0].strip()
secret = lines[1].strip()
f.close()
upbit = pyupbit.Upbit(access, secret)

try:
    search_order("KRW-NPXS")
except:
    state = 'done'
    print(state)
    pass
