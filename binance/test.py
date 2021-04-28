import ccxt
import pandas as pd


#  # 거래소 설정
#  # 파일로부터 apiKey, Secret 읽기
#  with open("binance.txt") as f:
#      lines = f.readlines()
#      api_key = lines[0].strip()
#      secret = lines[1].strip()
#
binance = ccxt.binance({
    #  'apiKey': api_key,
    #  'secret': secret,
    #  'enableRateLimit': True,
    #  'options': {
    #      'defaultType': 'future',
    #  }
})
#
#  print('Loading markets from', binance.id)
#  binance.load_markets()
#  print('Loaded markets from', binance.id)

# 코인 목록
tickers = ('BTC/USDT', 'ETH/USDT', 'BCH/USDT', 'XRP/USDT', 'EOS/USDT', 'LTC/USDT', 'TRX/USDT', 'ETC/USDT', 'LINK/USDT', 'XLM/USDT', 'ADA/USDT', 'XMR/USDT', 'DASH/USDT', 'ZEC/USDT', 'XTZ/USDT', 'BNB/USDT', 'ATOM/USDT', 'ONT/USDT', 'IOTA/USDT', 'BAT/USDT', 'VET/USDT', 'NEO/USDT', 'QTUM/USDT', 'IOST/USDT', 'THETA/USDT', 'ALGO/USDT', 'ZIL/USDT', 'KNC/USDT', 'ZRX/USDT', 'COMP/USDT', 'OMG/USDT', 'DOGE/USDT', 'SXP/USDT', 'KAVA/USDT', 'BAND/USDT', 'RLC/USDT', 'WAVES/USDT', 'MKR/USDT', 'SNX/USDT', 'DOT/USDT', 'YFI/USDT', 'BAL/USDT', 'CRV/USDT', 'TRB/USDT', 'YFII/USDT', 'RUNE/USDT', 'SUSHI/USDT', 'SRM/USDT', 'BZRX/USDT', 'EGLD/USDT', 'SOL/USDT', 'ICX/USDT', 'STORJ/USDT', 'BLZ/USDT', 'UNI/USDT', 'AVAX/USDT', 'FTM/USDT', 'HNT/USDT', 'ENJ/USDT', 'FLM/USDT', 'TOMO/USDT', 'REN/USDT', 'KSM/USDT', 'NEAR/USDT', 'AAVE/USDT', 'FIL/USDT', 'RSR/USDT', 'LRC/USDT', 'MATIC/USDT', 'OCEAN/USDT', 'CVC/USDT', 'BEL/USDT', 'CTK/USDT', 'AXS/USDT', 'ALPHA/USDT', 'ZEN/USDT', 'SKL/USDT', 'GRT/USDT', '1INCH/USDT', 'BTC/BUSD', 'AKRO/USDT', 'CHZ/USDT', 'SAND/USDT', 'ANKR/USDT', 'LUNA/USDT', 'BTS/USDT', 'LIT/USDT', 'UNFI/USDT', 'DODO/USDT', 'REEF/USDT', 'RVN/USDT', 'SFP/USDT', 'XEM/USDT', 'COTI/USDT', 'CHR/USDT', 'MANA/USDT', 'ALICE/USDT', 'HBAR/USDT', 'ONE/USDT', 'LINA/USDT', 'STMX/USDT', 'DENT/USDT', 'CELR/USDT', 'HOT/USDT', 'MTL/USDT', 'OGN/USDT', 'BTT/USDT', 'NKN/USDT', 'SC/USDT', 'DGB/USDT')

symbols = list(tickers)

#  for symbol in symbols:
symbol = 'ETH/USDT'
ohlcv = binance.fetch_ohlcv(symbol, '1m')
df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
df.set_index('datetime', inplace=True)
close = df['close']
print(close)
total = 0
for i in range(-1, -60, -1):
    total += close[i]
    print(total)

avg = total / 59
print("\n")
print(avg)
