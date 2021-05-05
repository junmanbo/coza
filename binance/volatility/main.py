import ccxt
import pandas as pd
import datetime
import time
import telegram

# telegram setting
with open("mombot.txt") as f:
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
tickers = ('BTC/USDT', 'ETH/USDT', 'BCH/USDT', 'XRP/USDT', 'EOS/USDT', 'LTC/USDT', 'TRX/USDT', 'ETC/USDT', 'LINK/USDT', 'XLM/USDT', 'ADA/USDT', 'XMR/USDT', 'DASH/USDT', 'ZEC/USDT', 'XTZ/USDT', 'BNB/USDT', 'ATOM/USDT', 'ONT/USDT', 'IOTA/USDT', 'BAT/USDT', 'VET/USDT', 'NEO/USDT', 'QTUM/USDT', 'IOST/USDT', 'THETA/USDT', 'ALGO/USDT', 'ZIL/USDT', 'KNC/USDT', 'ZRX/USDT', 'COMP/USDT', 'OMG/USDT', 'DOGE/USDT', 'SXP/USDT', 'KAVA/USDT', 'BAND/USDT', 'RLC/USDT', 'WAVES/USDT', 'MKR/USDT', 'SNX/USDT', 'DOT/USDT')
symbols = list(tickers)

# 목표가 구하기
def cal_target(symbol):
    ohlcv = binance.fetch_ohlcv(symbol, '1d')
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)

    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    yesterday_range = yesterday['high'] - yesterday['low']
    noise = 1 - abs(yesterday['open'] - yesterday['close']) / (yesterday['high'] - yesterday['low'])
    target_bull = today['open'] + (yesterday_range * noise)
    target_bear = today['open'] - (yesterday_range * noise)
    return target_bull, target_bear

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
    money = 0
    if total_balance <= 500:
        money = 0
    elif 500 < total_balance <= 600:
        money = 50
    elif 600 < total_balance <= 700:
        money = 100
    elif 700 < total_balance <= 800:
        money = 150
    elif 800 < total_balance <= 900:
        money = 200
    elif 900 < total_balance <= 1000:
        money = 250
    elif total_balance > 1000:
        money = 300
    return money

# 오늘 목표가 계산
def cal_today_target(symbols):
    symbols.clear()
    symbols = list(tickers)
    for symbol in symbols:
        temp[symbol]['target_bull'] = cal_target(symbol)[0]
        temp[symbol]['target_bear'] = cal_target(symbol)[1]
        time.sleep(1)

# 코인별 저장 정보값 초기화
temp = {}
for symbol in symbols:
    temp[symbol] = {}
    temp[symbol]['position'] = ''
    temp[symbol]['hold'] = False
    temp[symbol]['amount'] = 0
    temp[symbol]['target_bull'] = cal_target(symbol)[0]
    temp[symbol]['target_bear'] = cal_target(symbol)[1]
    time.sleep(1)

count_trading = 0
count_success = 0
total_hold = 0
start_balance = round(binance.fetch_balance()['USDT']['total'], 2)
bot.sendMessage(chat_id = chat_id, text="변동성 돌파 전략 자동매매 시작합니다. 화이팅!")
money = adjust_money(start_balance)

while True:
    try:
        for symbol in symbols:
            now = datetime.datetime.now()
            time.sleep(2)

            price_ask = ccxt.binance().fetch_ticker(symbol)['ask'] # 매도 1호가(현재가)
            price_bid = ccxt.binance().fetch_ticker(symbol)['bid'] # 매수 1호가(현재가)

            print(f"현재시간: {now} 코인: {symbol}\n현재가: {price_ask}\n매수 목표가: {temp[symbol]['target_bull']}\n공매도 목표가: {temp[symbol]['target_bear']}\n고가: {high} 저가: {low}\n")

            if now.hour == 8 and 55 <= now.minute <= 59:
                # 매수건 청산
                if temp[symbol]['hold'] == True and temp[symbol]['position'] == 'long':
                    for symbol in symbols:
                        binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=temp[symbol]['amount'], params={"reduceOnly": True})
                        profit = round((price_bid - temp[symbol]['target_bull']) / temp[symbol]['target_bull'] * 100, 2)
                        if profit > 0:
                            count_success += 1
                            bot.sendMessage(chat_id = chat_id, text=f"Success! 코인: {symbol} 성공횟수: {count_success}번\n수익률: {profit}")
                        else:
                            bot.sendMessage(chat_id = chat_id, text=f"Failure! 코인: {symbol}\n수익률: {profit}")
                        temp[symbol]['hold'] = False
                # 매도건 청산
                elif temp[symbol]['hold'] == True and temp[symbol]['position'] == 'short':
                    for symbol in symbols:
                        binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=temp[symbol]['amount'], params={"reduceOnly": True})
                        profit = round((temp[symbol]['target_bear']) - price_ask / price_ask * 100, 2)
                        if profit > 0:
                            count_success += 1
                            bot.sendMessage(chat_id = chat_id, text=f"성공! 코인: {symbol} 성공횟수: {count_success}번\n수익률: {profit}")
                        else:
                            bot.sendMessage(chat_id = chat_id, text=f"Failure! 코인: {symbol}\n수익률: {profit}")
                        temp[symbol]['hold'] = False
                time.sleep(100)

            elif now.hour == 9 and 1 <= now.minute <= 5:
                total_balance = binance.fetch_balance()['USDT']['total']
                bot.sendMessage(chat_id = chat_id, text=f"변동성 돌파전략\n시작잔고: {start_balance} -> 현재잔고: {total_balance}원\n거래횟수: {count_trading}번\n성공횟수: {count_success}")
                bot.sendMessage(chat_id = chat_id, text=f"오늘 코인 목표가를 계산중입니다...")
                cal_today_target(symbols)
                bot.sendMessage(chat_id = chat_id, text=f"오늘 코인 목표가 계산이 끝났습니다.")
                count_trading = 0
                count_success = 0
                start_balance = total_balance
                money = adjust_money(total_balance)
                bot.sendMessage(chat_id = chat_id, text="오늘도 변동성 돌파 전략 화이팅!")
                time.sleep(300)

            # 조건을 만족하면 지정가 매수 (매수건)
            elif temp[symbol]['hold'] == False and total_hold < 3 and (temp[symbol]['target_bull'] * 0.9999) <= price_ask <= (temp[symbol]['target_bull'] * 1.0001):
                target = price_unit(price_ask) # 목표가 (호가 단위)
                amount = money / target # 매수할 코인 개수
                binance.create_limit_buy_order(symbol=symbol, amount=amount, price=target) # 지정가 매수
                count_trading += 1
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 매수\n매수가: {target * amount}")
                temp[symbol]['hold'] = True
                temp[symbol]['position'] = 'long'
                temp[symbol]['amount'] = amount
                total_hold += 1

            # 조건을 만족하면 지정가 매도 (공매도건)
            elif temp[symbol]['hold'] == False and total_hold < 3 and (temp[symbol]['target_bear'] * 0.9999) <= price_bid <= (temp[symbol]['target_bear'] * 1.0001):
                target = price_unit(price_bid) # 목표가 (호가 단위)
                amount = money / target # 매도할 코인 개수
                binance.create_limit_sell_order(symbol=symbol, amount=amount, price=target) # 지정가 매도
                count_trading += 1
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 매도\n매도가: {target * amount}")
                temp[symbol]['hold'] = True
                temp[symbol]['position'] = 'short'
                temp[symbol]['amount'] = amount
                total_hold += 1

            elif total_hold == 3 and n == 2:
                while True:
                    if now.hour == 8 and now.minute == 54:
                        break
                    time.sleep(1)

    except Exception as e:
        bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
