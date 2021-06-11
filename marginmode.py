# 마진모드 변경 프로그램 (ISOLATED or CROSSED 모드 선택 가능)

# 모듈 가져오기
import ccxt
import time

# 거래소 설정
with open('./Api/binance.txt') as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret = lines[1].strip()

# 기본 옵션: 선물
exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    }
})

markets = exchange.load_markets()

symbols = exchange.load_markets().keys() # 목록 전체 조회
# CROSSED 모드로 변경
for symbol in symbols:
    try:
        print('Changing your', symbol, 'position margin mode to CROSSED:')
        market = exchange.market(symbol)
        response = exchange.fapiPrivate_post_margintype({
        'symbol': market['id'],
        'marginType': 'CROSSED',
        })
        print(response)
    except Exception as e:
        print(e)
    time.sleep(0.5)

# ISOLATED 모드로 변경
# print('Changing your', symbol, 'position margin mode to ISOLATED:')
# response = exchange.fapiPrivate_post_margintype({
#     'symbol': market['id'],
#     'marginType': 'ISOLATED',
# })
# print(response)
