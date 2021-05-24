import json
import os.path

#  with open('file.txt', 'w') as f:
#      f.write(json.dumps(info)) # use `json.loads` to do the reverse

with open('/home/cocojun/coza/binance/Stoch_short/info.txt', 'r') as f:
    data = f.read()
    info = json.loads(data)
#
print(info, type(info))
print(info["BTC/USDT"]['position'])

print(os.path.abspath("binance"))
home_path = '/home/cocojun'
