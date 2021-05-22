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
tickers = ('ADA/USDT', 'DOT/USDT', 'LINK/USDT', 'SOL/USDT')

symbols = list(tickers)

# 코인별 저장 정보값 초기화
info = {}
for symbol in symbols:
    info[symbol] = {}
    info[symbol]['amount'] = 0 # 코인 매수/매도 갯수
    info[symbol]['position'] = 'wait' # 현재 거래 포지션 (long / short / wait)
    info[symbol]['price'] = 0 # 코인 거래한 가격
    info[symbol]['slow_osc_d'] = 0 # Stochastic Slow Oscilator 값 (Day)
    info[symbol]['slow_osc_slope_d'] = 0 # Stochastic Slow Oscilator 기울기 값 (Day)
    info[symbol]['slow_osc_h'] = 0 # Stochastic Slow Oscilator 값 (Hour)
    info[symbol]['slow_osc_slope_h'] = 0 # Stochastic Slow Oscilator 기울기 값 (Hour)

# Stochastic Slow Oscilator 값 계산
def calStochastic_day(df, n=12, m=5, t=5):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    slow_osc_slope = slow_osc - slow_osc.shift(1)
    df['slow_osc_d'] = slow_osc
    df['slow_osc_slope_d'] = slow_osc_slope
    return df['slow_osc_d'][-1], df['slow_osc_slope_d'][-1]

# Stochastic Slow Oscilator 값 계산
def calStochastic_hour(df, n=20, m=12, t=12):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    slow_osc_slope = slow_osc - slow_osc.shift(1)
    df['slow_osc_h'] = slow_osc
    df['slow_osc_slope_h'] = slow_osc_slope
    return df['slow_osc_h'][-1], df['slow_osc_slope_h'][-1]

# 코인별 Stochastic OSC 값 info에 저장
def save_info():
    for symbol in symbols:
        # 일봉 데이터 수집
        ohlcv_d = binance.fetch_ohlcv(symbol, '1d')
        df_d = pd.DataFrame(ohlcv_d, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df_d['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df_d.set_index('datetime', inplace=True)

        ohlcv_h = binance.fetch_ohlcv(symbol, '1h')
        df_h = pd.DataFrame(ohlcv_h, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df_h['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df_h.set_index('datetime', inplace=True)

        # Save Stochastic Oscilator information
        info[symbol]['slow_osc_d'] = calStochastic_day(df_d)[0]
        info[symbol]['slow_osc_slope_d'] = calStochastic_day(df_d)[1]
        info[symbol]['slow_osc_h'] = calStochastic_hour(df_h)[0]
        info[symbol]['slow_osc_slope_h'] = calStochastic_hour(df_h)[1]

        print(f"코인: {symbol}\n\
            Stochastic OSC (Day): {info[symbol]['slow_osc_d']}\n\
            Stochastic OSC Slope (Day): {info[symbol]['slow_osc_slope_d']}\n\
            Stochastic OSC (Hour): {info[symbol]['slow_osc_h']}\n\
            Stochastic OSC Slope (Hour): {info[symbol]['slow_osc_slope_h']}\n")
        time.sleep(0.1)

bot.sendMessage(chat_id = chat_id, text=f"Stochastic (스윙) 전략 시작합니다. 화이팅!")
save_info()

while True:
    try:
        now = datetime.datetime.now()
        time.sleep(10)
        if now.minute == 0:
            save_info()
            money = binance.fetch_balance()['USDT']['free'] / 4
            for symbol in symbols:
                current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                amount = money / current_price # 거래할 코인 갯수
                # 코인 미보유 시 거래 (롱)
                if info[symbol]['position'] == 'wait' and \
                        info[symbol]['slow_osc_d'] > 0 and info[symbol]['slow_osc_slope_d'] > 0 and \
                        info[symbol]['slow_osc_h'] > 0 and info[symbol]['slow_osc_slope_h'] > 0:
                    binance.create_market_buy_order(symbol=symbol, amount=amount) # 시장가 매수
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'long' # 포지션 'long' 으로 변경
                    info[symbol]['amount'] = amount # 코인 갯수 저장
                    bot.sendMessage(chat_id = chat_id, text=f"(스윙){symbol} 롱 포지션\n매수가: {current_price}\n투자금액: {money:.2f}")
                    print(f"{symbol} 롱 포지션\n매수가: {current_price}\n투자금액: {money:.2f}")
                # 코인 미보유 시 거래 (숏)
                elif info[symbol]['position'] == 'wait' and \
                        info[symbol]['slow_osc_d'] < 0 and info[symbol]['slow_osc_slope_d'] < 0 and \
                        info[symbol]['slow_osc_h'] < 0 and info[symbol]['slow_osc_slope_h'] < 0:
                    binance.create_market_sell_order(symbol=symbol, amount=amount) # 시장가 매도
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'short' # 포지션 'short' 으로 변경
                    info[symbol]['amount'] = amount # 코인 갯수 저장
                    bot.sendMessage(chat_id = chat_id, text=f"(스윙){symbol} 숏 포지션\n매도가: {current_price}\n투자금액: {money:.2f}")
                    print(f"{symbol} 숏 포지션\n매도가: {current_price}\n투자금액: {money:.2f}")
                # 반환점 가까워지면 청산
                elif info[symbol]['position'] == 'long':
                    if info[symbol]['slow_osc_h'] < 0 or info[symbol]['slow_osc_slope_h'] < 0:
                        # 현재 포지션 청산
                        binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=info[symbol]['amount'], params={"reduceOnly": True})
                        profit = (current_price - info[symbol]['price']) / info[symbol]['price'] * 100  # 수익률 계산
                        bot.sendMessage(chat_id = chat_id, text=f"(스윙){symbol} (롱)\n\
                            매수가: {info[symbol]['price']} -> 매도가: {current_price}\n수익률: {profit:.2f}%")
                        print(f"코인: {symbol} (롱)\n매수가: {info[symbol]['price']} -> 매도가: {current_price}\n수익률: {profit:.2f}%")
                        info[symbol]['position'] = 'wait'

                elif info[symbol]['position'] == 'short':
                    if info[symbol]['slow_osc_h'] > 0 or info[symbol]['slow_osc_slope_h'] > 0:
                        # 현재 포지션 청산
                        binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=info[symbol]['amount'], params={"reduceOnly": True})
                        profit = (info[symbol]['price'] - current_price) / current_price * 100  # 수익률 계산
                        bot.sendMessage(chat_id = chat_id, text=f"(스윙){symbol} (숏)\n\
                            매도가: {info[symbol]['price']} -> 매수가: {current_price}\n수익률: {profit:.2f}%")
                        print(f"코인: {symbol} (숏)\n매도가: {info[symbol]['price']} -> 매수가: {current_price}\n수익률: {profit:.2f}%")
                        info[symbol]['position'] = 'wait'

                time.sleep(1)
                print(f"시간: {now} 코인: {symbol}\n\
                    Stochastic OSC (Day): {info[symbol]['slow_osc_d']}\nStochastic OSC Slope (Day): {info[symbol]['slow_osc_slope_d']}\n\
                    Stochastic OSC (Hour): {info[symbol]['slow_osc_h']}\nStochastic OSC Slope (Hour): {info[symbol]['slow_osc_slope_h']}\n\
                    포지션 상태: {info[symbol]['position']}\n")
            time.sleep(60)

    except Exception as e:
        bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
