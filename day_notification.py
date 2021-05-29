#!/usr/bin/env python

import ccxt
import telegram
import json

# telegram 설정
with open('./Api/mybot.txt') as f:
    lines = f.readlines()
    my_token = lines[0].strip()
    chat_id = lines[1].strip()
bot = telegram.Bot(token = my_token)

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

# 코인 정보 저장 파일 불러오기
with open('./Data/balance.txt', 'r') as f:
    data = f.read()
    start_balance = json.loads(data)

end_balance = binance.fetch_balance()['USDT']['total']

bot.sendMessage(chat_id = chat_id, text=f"하루 정산\n어제: ${start_balance:.2f} -> 오늘: ${end_balance:.2f}\n차액: ${end_balance - start_balance:.2f}")

# 파일에 수집한 정보 및 거래 정보 파일에 저장
with open('./Data/balance.txt', 'w') as f:
    f.write(json.dumps(end_balance))
