#!/usr/bin/env python

import ccxt

# 거래소 설정
with open('./Api/binance.txt') as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret = lines[1].strip()

# 기본 옵션: 선물
binance = ccxt.binance({
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    }
})

symbol = 'BTC/USDT'
bid_ask = binance.fetch_bids_asks(symbols=symbol)
ask = bid_ask[symbol]['ask']

print(bid_ask, ask)

