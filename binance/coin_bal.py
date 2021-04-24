import ccxt
from pprint import pprint
import pandas as pd

with open("binance.txt") as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret = lines[1].strip()

binance = ccxt.binance({
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    }
})


symbols = ['BTC/USDT', 'ETH/USDT', 'BCH/USDT', 'XRP/USDT', 'EOS/USDT', 'LTC/USDT', 'TRX/USDT', 'ETC/USDT', 'LINK/USDT', 'XLM/USDT', 'ADA/USDT', 'XMR/USDT', 'DASH/USDT', 'ZEC/USDT', 'XTZ/USDT', 'BNB/USDT', 'ATOM/USDT', 'ONT/USDT', 'IOTA/USDT', 'BAT/USDT', 'VET/USDT', 'NEO/USDT', 'QTUM/USDT', 'IOST/USDT', 'THETA/USDT', 'ALGO/USDT', 'ZIL/USDT', 'KNC/USDT', 'ZRX/USDT', 'COMP/USDT', 'OMG/USDT', 'DOGE/USDT', 'SXP/USDT', 'KAVA/USDT', 'BAND/USDT', 'RLC/USDT', 'WAVES/USDT', 'MKR/USDT', 'SNX/USDT', 'DOT/USDT', 'DEFI/USDT', 'YFI/USDT', 'BAL/USDT', 'CRV/USDT', 'TRB/USDT', 'YFII/USDT', 'RUNE/USDT', 'SUSHI/USDT', 'SRM/USDT', 'BZRX/USDT', 'EGLD/USDT', 'SOL/USDT', 'ICX/USDT', 'STORJ/USDT', 'BLZ/USDT', 'UNI/USDT', 'AVAX/USDT', 'FTM/USDT', 'HNT/USDT', 'ENJ/USDT', 'FLM/USDT', 'TOMO/USDT', 'REN/USDT', 'KSM/USDT', 'NEAR/USDT', 'AAVE/USDT', 'FIL/USDT', 'RSR/USDT', 'LRC/USDT', 'MATIC/USDT', 'OCEAN/USDT', 'CVC/USDT', 'BEL/USDT', 'CTK/USDT', 'AXS/USDT', 'ALPHA/USDT', 'ZEN/USDT', 'SKL/USDT', 'GRT/USDT', '1INCH/USDT', 'BTC/BUSD', 'AKRO/USDT', 'CHZ/USDT', 'SAND/USDT', 'ANKR/USDT', 'LUNA/USDT', 'BTS/USDT', 'LIT/USDT', 'UNFI/USDT', 'DODO/USDT', 'REEF/USDT', 'RVN/USDT', 'SFP/USDT', 'XEM/USDT', 'BTCSTUSDT', 'COTI/USDT', 'CHR/USDT', 'MANA/USDT', 'ALICE/USDT', 'HBAR/USDT', 'ONE/USDT', 'LINA/USDT', 'STMX/USDT', 'DENT/USDT', 'CELR/USDT', 'HOT/USDT', 'MTL/USDT', 'OGN/USDT', 'BTT/USDT', 'NKN/USDT', 'SC/USDT', 'DGB/USDT']

print(symbols)
#  def table(values):
#      first = values[0]
#      keys = list(first.keys()) if isinstance(first, dict) else range(0, len(first))
#      widths = [max([len(str(v[k])) for v in values]) for k in keys]
#      string = ' | '.join(['{:<' + str(w) + '}' for w in widths])
#      return "\n".join([string.format(*[str(v[k]) for k in keys]) for v in values])
#
#  symbol = "TRX/USDT"
#  ohlcv = binance.fetch_ohlcv(symbol, '1d')
#  df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
#  df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
#  df.set_index('datetime', inplace=True)
#  balance = binance.fetch_balance()['USDT']['free']
#  price = ccxt.binance().fetch_ticker("TRX/USDT")['ask'] # 매도 1호가(현재가)
#  amount = binance.fetch_balance()['USDT']['used']
#  print(balance, amount, price)
#  print('----------------------------------------------------------------------')
#
#  print('Fetching your balance:')
#  response = binance.fetch_balance()
#  pprint(response['total'])  # make sure you have enough futures margin...
#  # pprint(response['info'])  # more details
#
#  print('----------------------------------------------------------------------')
#
#  print('Getting your positions:')
#  response = binance.fapiPrivateV2_get_positionrisk()
#  print(table(response))
#
#  print('----------------------------------------------------------------------')
#
#  print('Getting your current position mode (One-way or Hedge Mode):')
#  response = binance.fapiPrivate_get_positionside_dual()
#  if response['dualSidePosition']:
#      print('You are in Hedge Mode')
#  else:
#      print('You are in One-way Mode')
#
#  print('----------------------------------------------------------------------')
#
