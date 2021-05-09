import ccxt
import pandas as pd
import time

binance = ccxt.binance()

# 코인 목록
symbols = ['BTC/USDT', 'ETH/USDT', 'BCH/USDT', 'XRP/USDT', 'EOS/USDT', 'LTC/USDT', 'TRX/USDT', 'ETC/USDT', 'LINK/USDT', 'XLM/USDT', 'ADA/USDT', 'XMR/USDT', 'DASH/USDT', 'ZEC/USDT', 'XTZ/USDT', 'BNB/USDT', 'ATOM/USDT', 'ONT/USDT', 'IOTA/USDT', 'BAT/USDT']

for symbol in symbols:

    current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
    print(f"{symbol} : {current_price}")
