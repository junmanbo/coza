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
    info[symbol]['amount'] = 0 # 코인 매수/매도 갯수
    info[symbol]['position'] = 'wait' # 현재 거래 포지션 (long / short / wait)
    info[symbol]['price'] = 0 # 코인 거래한 가격
    info[symbol]['slow_osc_d'] = 0 # Stochastic Slow Oscilator 값 (Day)
    info[symbol]['slow_osc_slope_d'] = 0 # Stochastic Slow Oscilator 기울기 값 (Day)
    info[symbol]['slow_osc_h'] = 0 # Stochastic Slow Oscilator 값 (Hour)
    info[symbol]['slow_osc_slope_h'] = 0 # Stochastic Slow Oscilator 기울기 값 (Hour)
    info[symbol]['macd_osc'] = 0 # MACD Oscilator 값
    info[symbol]['ma'] = 0 # 지수이동평균 값

with open('info_short.txt', 'w') as f:
    f.write(json.dumps(info)) # use `json.loads` to do the reverse
