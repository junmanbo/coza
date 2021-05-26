import ccxt
import json
import os

# 경로 설정
home = os.getcwd()
path_data = home + '/Data/'
print(home)

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
    info[symbol]['stoch_osc_d'] = 0 # Stochastic Slow Oscilator 값 (Day)
    info[symbol]['stoch_slope_d'] = 0 # Stochastic Slow Oscilator 기울기 값 (Day)
    info[symbol]['stoch_slope_4h'] = 0 # Stochastic Slow Oscilator 기울기 값 (4Hour)
    info[symbol]['stoch_slope_1h'] = 0 # Stochastic Slow Oscilator 기울기 값 (1Hour)
    info[symbol]['macd_osc'] = 0 # MACD Oscilator 값
    info[symbol]['ma'] = 0 # 지수이동평균 값
    info[symbol]['RSI'] = 0 # RSI 지수 값

with open(path_data+'binance_short.txt', 'w') as f:
    f.write(json.dumps(info)) # use `json.loads` to do the reverse
