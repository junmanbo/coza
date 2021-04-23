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

def table(values):
    first = values[0]
    keys = list(first.keys()) if isinstance(first, dict) else range(0, len(first))
    widths = [max([len(str(v[k])) for v in values]) for k in keys]
    string = ' | '.join(['{:<' + str(w) + '}' for w in widths])
    return "\n".join([string.format(*[str(v[k]) for k in keys]) for v in values])

symbol = "TRX/USDT"
ohlcv = binance.fetch_ohlcv(symbol, '1d')
df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
df.set_index('datetime', inplace=True)
balance = binance.fetch_balance()['USDT']['free']
price = ccxt.binance().fetch_ticker("TRX/USDT")['ask'] # 매도 1호가(현재가)
amount = binance.fetch_balance()['USDT']['used']
print(balance, amount, price)
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
