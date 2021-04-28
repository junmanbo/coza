import pyupbit
import telegram

tickers = pyupbit.get_tickers("KRW") # 코인 전체 불러오기
symbols = []

# API key 불러오기
f = open("upbit.txt")
lines = f.readlines()
access = lines[0].strip()
secret = lines[1].strip()
f.close()
upbit = pyupbit.Upbit(access, secret)

# Telegram bot 토큰 불러오기
f = open("upbit.txt")
lines = f.readlines()
my_token = lines[0].strip()
chat_id = lines[1].strip()
f.close()
bot = telegram.Bot(token = my_token)

# 보유하고 있는 코인으로 리스트 재구성
def reorg_symbols():
    for ticker in tickers:
        coin_balance = upbit.get_balance(ticker)  # 코인 잔고
        if coin_balance > 0:
            symbols.append(ticker)
    bot.sendMessage(chat_id = chat_id, text=f"보유하고 있는 코인 목록을 재구성했습니다.\n코인 목록: {symbols}")

reorg_symbols()
for symbol in symbols:
    price = pyupbit.get_current_price(symbol)  # 코인 현재가
    avg_buy_price = upbit.get_balance(symbol)['avg_buy_price']
    goal = price * 1.05
    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 평균매수단가: {avg_buy_price}\n현재가: {price} 다음 목표가: {goal}")
