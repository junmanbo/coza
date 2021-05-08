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
    info[symbol]['amount'] = 0 # 코인 매수/매도 갯수
    info[symbol]['position'] = '' # 현재 거래 포지션 (long / short)
    info[symbol]['slow_osc'] = 0 # Stochastic Slow Oscilator 값
    info[symbol]['price'] = 0 # 코인 거래한 가격

# Stochastic Slow Oscilator 값 계산
def calStochastic(df, n=9, m=3, t=3):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    df = df.assign(fast_k=fast_k, fast_d=slow_k, slow_k=slow_k, slow_d=slow_d, slow_osc=slow_osc)
    return df['slow_osc'][-1]

# 코인별 Stochastic OSC 값 info에 저장
def save_info():
    bot.sendMessage(chat_id = chat_id, text="코인별 Stochastic OSC 값 수집중...")
    for symbol in symbols:
        # 일봉 데이터 수집
        ohlcv = binance.fetch_ohlcv(symbol, '1d')
        df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)

        # Save Stochastic Oscilator information
        info[symbol]['slow_osc'] = calStochastic(df)
        time.sleep(0.5)
    bot.sendMessage(chat_id = chat_id, text="코인별 Stochastic OSC 값을 저장했습니다.\n매수/매도 조건을 확인하겠습니다.")

# 호가 단위 맞추기
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
    money = round((total_balance * 3 / 20 - 5), 0)
    return money

total_balance = round(binance.fetch_balance()['USDT']['total'], 2) # 현재 전체 잔고 (used + free)
money = round(adjust_money(total_balance), 0) # 코인별 투자금액
bot.sendMessage(chat_id = chat_id, text=f"Stochastic 전략 시작합니다. 화이팅!\n1코인당 투자 금액: {money}")
save_info() # 코인별 Stochastic OSC 값 저장

for symbol in symbols:
    if info[symbol]['slow_osc'] > 0: # 상승장
        price_ask = ccxt.binance().fetch_ticker(symbol)['ask'] # 매도 1호가(현재가)
        price = price_unit(price_ask) # 호가 단위 맞추기
        amount = money / price # 매수할 코인 갯수
        binance.create_market_buy_order(symbol=symbol, amount=amount) # 시장가 매수

        info[symbol]['position'] = 'long' # 포지션 'long' 으로 변경
        info[symbol]['price'] = price # 매수 가격 저장
        info[symbol]['amount'] = amount # 코인 갯수 저장
        bot.sendMessage(chat_id = chat_id, text=f"{symbol} Buying: {price} USD")

    elif info[symbol]['slow_osc'] < 0: # 하락장
        price_bid = ccxt.binance().fetch_ticker(symbol)['bid'] # 매수 1호가(현재가)
        price = price_unit(price_bid) # 호가 단위 맞추기
        amount = money / price # 매도할 코인 갯수
        binance.create_market_sell_order(symbol=symbol, amount=amount) # 시장가 매도

        info[symbol]['position'] = 'short' # 포지션 'short' 으로 변경
        info[symbol]['price'] = price # 매도 가격 저장
        info[symbol]['amount'] = amount # 코인 갯수 저장
        bot.sendMessage(chat_id = chat_id, text=f"{symbol} Selling: {price} USD")
    time.sleep(1)
    print(f"코인: {symbol}\nStochastic OSC: {info[symbol]['slow_osc']}\n포지션 상태: {info[symbol]['position']}\n")

while True:
    try:
        now = datetime.datetime.now()
        if now.hour % 8 == 0 and now.minute == 0 and 0 <= now.second <= 10:
            save_info() # Stochastic OSC 값 갱신
            for symbol in symbols:
                # Position Long to Short
                if info[symbol]['position'] == 'long' and info[symbol]['slow_osc'] < 0: # 상승장에서 하락장으로 바뀐경우
                    binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=info[symbol]['amount'], params={"reduceOnly": True}) # 포지션 종료
                    price_bid = ccxt.binance().fetch_ticker(symbol)['bid'] # 매수 1호가(현재가)
                    profit = round((price_bid - info[symbol]['price']) / info[symbol]['price'] * 100, 2) # 수익률 계산
                    total_balance = round(binance.fetch_balance()['USDT']['total'], 2) # 현재 전체 잔고 (used + free)
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 수익률: {profit}\n전체 잔고: {total_balance}")

                    money = round(adjust_money(total_balance), 0) # 코인별 투자금액
                    price = price_unit(price_bid) # 호가 단위 맞추기
                    amount = money / price # 매도할 코인 갯수
                    binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=amount) # 시장가 매도 (숏 포지션으로 변경)
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 가격: {price} 투자금액: {money}\n포지션 롱에서 숏으로 변경")

                    info[symbol]['price'] = price # 매도가 저장
                    info[symbol]['position'] = 'short' # 포지션 숏으로 변경 저장
                    info[symbol]['amount'] = amount # 매도한 코인 갯수 저장

                # Position Short to Long
                elif info[symbol]['position'] == 'short' and info[symbol]['slow_osc'] > 0: # 하락장에서 상승장으로 바뀐경우
                    binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=info[symbol]['amount'], params={"reduceOnly": True}) # 포지션 종료
                    price_ask = ccxt.binance().fetch_ticker(symbol)['ask'] # 매도 1호가(현재가)
                    profit = round((info[symbol]['price'] - price_ask) / price_ask * 100, 2) # 수익률 계산
                    total_balance = round(binance.fetch_balance()['USDT']['total'], 2) # 현재 전체 잔고 (used + free)
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 수익률: {profit}\nTotal Balance: {total_balance}")

                    money = round(adjust_money(total_balance), 0) # 코인별 투자금액
                    price = price_unit(price_ask) # 호가 단위 맞추기
                    amount = money / price # 매도할 코인 갯수
                    binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=amount) # 시장가 매수 (롱 포지션으로 변경)
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 가격: {price} 투자금액: {money}\n포지션 숏에서 롱으로 변경")

                    info[symbol]['price'] = price # 매수가 저장
                    info[symbol]['position'] = 'long' # 포지션 롱으로 변경 저장
                    info[symbol]['amount'] = amount # 매수한 코인 갯수 저장
                time.sleep(1)
                print(f"시간: {now} 코인: {symbol}\nStochastic OSC: {info[symbol]['slow_osc']}\n포지션 상태: {info[symbol]['position']}\n")

    except Exception as e:
        bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
