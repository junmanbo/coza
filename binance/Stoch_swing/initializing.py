import json

# 코인 목록
tickers = ('BTC/USDT', 'ETH/USDT')

symbols = list(tickers)

# 코인별 저장 정보값 초기화
info = {}
for symbol in symbols:
    info[symbol] = {}
    info[symbol]['amount'] = 0 # 코인 매수/매도 갯수
    info[symbol]['position'] = 'wait' # 현재 거래 포지션 (long / short / wait)
    info[symbol]['price'] = 0 # 코인 거래한 가격
    info[symbol]['slow_osc'] = 0 # Stochastic Slow Oscilator 값 (Day)
    info[symbol]['slow_osc_slope'] = 0 # Stochastic Slow Oscilator 기울기 값 (Day)

with open('info_swing.txt', 'w') as f:
    f.write(json.dumps(info)) # use `json.loads` to do the reverse
