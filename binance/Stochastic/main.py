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

binance = ccxt.binance({
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    }
})

print('Loading markets from', binance.id)
binance.load_markets()
print('Loaded markets from', binance.id)

# 코인 목록
symbols = ['BTC/USDT', 'ETH/USDT', 'BCH/USDT', 'XRP/USDT', 'EOS/USDT', 'LTC/USDT', 'TRX/USDT', 'ETC/USDT', 'LINK/USDT', 'XLM/USDT', 'ADA/USDT', 'XMR/USDT', 'DASH/USDT', 'ZEC/USDT', 'XTZ/USDT', 'BNB/USDT', 'ATOM/USDT', 'ONT/USDT', 'IOTA/USDT', 'BAT/USDT']

# 코인별 저장 정보값 초기화
info = {}
for symbol in symbols:
    info[symbol] = {}
    info[symbol]['amount'] = 0
    info[symbol]['position'] = ''
    info[symbol]['slow_osc'] = 0
    info[symbol]['price'] = 0

def calStochastic(df, n=9, m=3, t=3):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    df = df.assign(fast_k=fast_k, fast_d=slow_k, slow_k=slow_k, slow_d=slow_d, slow_osc=slow_osc)
    return df['slow_osc'][-1]

def save_info():
    bot.sendMessage(chat_id = chat_id, text="Collecting the Coin's Stochastic Oscilator value...")
    for symbol in symbols:
        # 일봉 데이터 수집
        ohlcv = binance.fetch_ohlcv(symbol, '1d')
        df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)

        # Save Stochastic Oscilator information
        info[symbol]['slow_osc'] = calStochastic(df)
        time.sleep(1)
    bot.sendMessage(chat_id = chat_id, text="Saving the Coin's Stochastic Oscilator value!\nLet's Start checking condition.")

def price_unit(price):
    if price < 0.01:
        price = round(price, 6)
    elif 0.01 <= price < 0.1:
        price = round(price, 5)
    elif 0.1 <= price < 1:
        price = round(price, 4)
    elif 10 <= price < 100:
        price = round(price, 3)
    elif 100 <= price < 1000:
        price = round(price, 2)
    elif price >= 10000:
        price = round(price, 1)
    return price

# 투자금액 조정
def adjust_money(total_balance):
    money = total_balance * 3 / 20 - 5
    return money

total_balance = round(binance.fetch_balance()['USDT']['total'], 2)
money = adjust_money(total_balance)
bot.sendMessage(chat_id = chat_id, text=f"Stochastic 전략 시작합니다. 화이팅!\n1코인당 투자 금액: {money}")
save_info()

for symbol in symbols:
    if info[symbol]['slow_osc'] > 0:
        price_ask = ccxt.binance().fetch_ticker(symbol)['ask'] # 매도 1호가(현재가)
        price = price_unit(price_ask)
        amount = money / price # 매수할 코인 개수
        binance.create_market_buy_order(symbol=symbol, amount=amount)

        info[symbol]['position'] = 'long'
        info[symbol]['price'] = price
        info[symbol]['amount'] = amount
        bot.sendMessage(chat_id = chat_id, text=f"{symbol} Buying: {price} USD")

    elif info[symbol]['slow_osc'] < 0:
        price_bid = ccxt.binance().fetch_ticker(symbol)['bid'] # 매수 1호가(현재가)
        price = price_unit(price_bid)
        amount = money / price
        binance.create_market_sell_order(symbol=symbol, amount=amount)

        info[symbol]['position'] = 'short'
        info[symbol]['price'] = price
        info[symbol]['amount'] = amount
        bot.sendMessage(chat_id = chat_id, text=f"{symbol} Selling: {price} USD")
    time.sleep(1)

while True:
    try:
        for symbol in symbols:
            now = datetime.datetime.now()
            time.sleep(0.5)

            print(f"현재시간: {now} 코인: {symbol}")
            print(f"Stochastic OSC: {info[symbol]['slow_osc']}\n포지션 상태: {info[symbol]['position']}\n")

            if now.hour % 4 == 0 and 0 <= now.minute <= 1:
                save_info()

                # Position Long to Short
                if info[symbol]['position'] == 'long' and info[symbol]['slow_osc'] < 0:
                    binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=info[symbol]['amount'], params={"reduceOnly": True})
                    price_bid = ccxt.binance().fetch_ticker(symbol)['bid'] # 매수 1호가(현재가)
                    profit = round((price_bid - info[symbol]['price']) / info[symbol]['price'] * 100, 2)
                    total_balance = round(binance.fetch_balance()['USDT']['total'], 2)
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 수익률: {profit}\nTotal Balance: {total_balance}")

                    money = adjust_money(total_balance)
                    price = price_unit(price_bid)
                    amount = money / price # 매수할 코인 개수
                    binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=amount)
                    info[symbol]['price'] = price
                    info[symbol]['position'] = 'short'
                    info[symbol]['amount'] = amount
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} Change Position Long to Short")

                # Position Short to Long
                elif info[symbol]['position'] == 'short' and info[symbol]['slow_osc'] > 0:
                    binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=info[symbol]['amount'], params={"reduceOnly": True})
                    price_ask = ccxt.binance().fetch_ticker(symbol)['ask']
                    profit = round((price_ask - info[symbol]['price']) / info[symbol]['price'] * 100, 2)
                    total_balance = round(binance.fetch_balance()['USDT']['total'], 2)
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 수익률: {profit}\nTotal Balance: {total_balance}")

                    money = adjust_money(total_balance)
                    price = price_unit(price_ask)
                    amount = money / price # 매수할 코인 개수
                    binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=amount)
                    info[symbol]['price'] = price
                    info[symbol]['position'] = 'short'
                    info[symbol]['amount'] = amount
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} Change Position Short to Long")

    except Exception as e:
        bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
