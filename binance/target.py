import ccxt
import pandas as pd
import datetime
import time
import telegram

# telegram setting
with open("heebot.txt") as f:
    lines = f.readlines()
    my_token = lines[0].strip()
    chat_id = lines[1].strip()
bot = telegram.Bot(token = my_token)


# 거래소 설정
# 파일로부터 apiKey, Secret 읽기
with open("binance.txt") as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret = lines[1].strip()

binance = ccxt.binance(config={
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
})

# 메이저 코인 목록
symbols = ["BTC/USDT", "ETH/USDT", "BCH/USDT", "XRP/USDT", "EOS/USDT", "LTC/USDT", "TRX/USDT", "ETC/USDT", "LINK/USDT", "XLM/USDT", "ADA/USDT", "XMR/USDT", "DASH/USDT", "ZEC/USDT", "XTZ/USDT", "BNB/USDT", "ATOM/USDT", "ONT/USDT", "IOTA/USDT", "BAT/USDT", "VET/USDT", "NEO/USDT", "QTUM/USDT", "IOST/USDT", "THETA/USDT"]

def cal_target(symbol):
    # 목표가 구하기
    ohlcv = binance.fetch_ohlcv(symbol, '1d')
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)

    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    yesterday_range = yesterday['high'] - yesterday['low']
    noise = 1 - abs(yesterday['open'] - yesterday['close']) / (yesterday['high'] - yesterday['low'])
    target = today['open'] + (yesterday_range * noise)

    # 5일 이동평균선 구하기
    close = df['close']
    ma = close.rolling(window=5).mean()

    if target > ma[-2]:
        return target
    else:
        return ma[-2]

def price_unit(price):
    if price < 0.01:
        price = round(price, 5)
    elif 0.01 <= price < 0.1:
        price = round(price, 4)
    elif 0.1 <= price < 1:
        price = round(price, 3)
    elif 10 <= price < 100:
        price = round(price, 2)
    elif 100 <= price < 1000:
        price = round(price, 1)
    elif price >= 10000:
        price = round(price)
    return price

count_trading = 0
count_success = 0
count_loose = 0

while True:
    try:
        for symbol in symbols:
            now = datetime.datetime.now()
            time.sleep(0.1)
            target = cal_target(symbol) # 목표가
            price = binance.fetch_ticker(symbol)['bid'] # 매수 1호가(현재가)
            balance = binance.fetch_balance(params={"type": "future"})['USDT']['free']
            coin_balance = binance.fetch_balance(params={"type": "future"})[symbol]['free']

            profit = target * 1.02 # 익절가
            limit = target * 0.98 # 손절가

            if now.hour == 8 and now.minute == 59 and 50 <= now.second <= 59:
                total_balance = binance.fetch_balance(params={"type": "future"})['USDT']['total']
                bot.sendMessage(chat_id = chat_id, text=f"잔고: {total_balance}원\n거래횟수: {count_trading}번\n실패횟수: {count_loose}번")
                count_trading = 0
                count_loose = 0
                time.sleep(10)

            # 조건을 만족하면 지정가 매수
            elif balance >= 300 and target <= price <= (target * 1.001):
                target = price_unit(target) # 목표가 (호가 단위)
                amount = 300 / target # 매수할 코인 개수
                binance.create_limit_buy_order(symbol, amount, price=target, params={'type': 'future'}) # 지정가 매수
                count_trading += 1
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 예약매수\n매수가: {target} 거래횟수: {count_trading}번")
                symbols = [symbol]

            # 익절가에 도달하면 지정가 매도
            elif coin_balance > 0 and profit <= price:
                profit = price_unit(profit) # 익절가
                amount = coin_balance # 매도할 코인 개수
                binance.create_limit_sell_order(symbol, amount, price=profit, params={'type': 'future'}) # 지정가 매도
                count_success += 1
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 예약매수\n매도가: {profit} 성공횟수: {count_success}번")
                symbols = ["BTC/USDT", "ETH/USDT", "BCH/USDT", "XRP/USDT", "EOS/USDT", "LTC/USDT", "TRX/USDT", "ETC/USDT", "LINK/USDT", "XLM/USDT", "ADA/USDT", "XMR/USDT", "DASH/USDT", "ZEC/USDT", "XTZ/USDT", "BNB/USDT", "ATOM/USDT", "ONT/USDT", "IOTA/USDT", "BAT/USDT", "VET/USDT", "NEO/USDT", "QTUM/USDT", "IOST/USDT", "THETA/USDT"]

            # 손절가에 도달하면 지정가 매도
            elif coin_balance > 0 and limit >= price:
                limit = price_unit(limit) # 손절가
                amount = coin_balance # 매도할 코인 개수
                binance.create_limit_sell_order(symbol, amount, price=limit, params={'type': 'future'}) # 지정가 매도
                count_loose += 1
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 예약매도\n매도가: {limit} 실패횟수: {count_loose}번")
                symbols = ["BTC/USDT", "ETH/USDT", "BCH/USDT", "XRP/USDT", "EOS/USDT", "LTC/USDT", "TRX/USDT", "ETC/USDT", "LINK/USDT", "XLM/USDT", "ADA/USDT", "XMR/USDT", "DASH/USDT", "ZEC/USDT", "XTZ/USDT", "BNB/USDT", "ATOM/USDT", "ONT/USDT", "IOTA/USDT", "BAT/USDT", "VET/USDT", "NEO/USDT", "QTUM/USDT", "IOST/USDT", "THETA/USDT"]
    except:
        pass