#!/home/xnote/venvs/trading/bin/python
import ccxt
import json

binance = ccxt.binance({
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    }
})

tickers = binance.load_markets().keys()

symbols = list(tickers)
# 코인별 저장 정보값 초기화
info = {}
for symbol in symbols:
    info[symbol] = {}
    info[symbol]['quantity'] = 0 # 코인 매수/매도 갯수
    info[symbol]['position'] = 'wait' # 현재 거래 포지션 (long / short / wait)
    info[symbol]['price'] = 0 # 코인 거래한 가격

with open('./Data/binance_swing.txt', 'w') as f:
    f.write(json.dumps(info)) # use `json.loads` to do the reverse
