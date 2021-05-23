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

tickers = binance.load_markets().keys()

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
    info[symbol]['macd_osc'] = 0 # MACD Oscilator 값
    info[symbol]['ma'] = 0 # 지수이동평균 값

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
def calStochastic_hour(df, n=9, m=3, t=3):
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

def calMA(df, fast=14):
    df['ma'] = df['close'].ewm(span=fast).mean()
    return df['ma'][-1]

def calMACD(df, m_NumFast=14, m_NumSlow=30, m_NumSignal=10):
    EMAFast = df.close.ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
    EMASlow = df.close.ewm( span = m_NumSlow, min_periods = m_NumSlow - 1 ).mean()
    MACD = EMAFast - EMASlow
    MACDSignal = MACD.ewm( span = m_NumSignal, min_periods = m_NumSignal - 1 ).mean()
    df['macd_osc'] = MACD - MACDSignal
    return df['macd_osc'][-1]

# 코인별 Stochastic OSC 값 info에 저장
def save_info():
    for symbol in symbols:
        # 일봉 데이터 수집
        ohlcv_d = binance.fetch_ohlcv(symbol, '1d')
        df_d = pd.DataFrame(ohlcv_d, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df_d['datetime'] = pd.to_datetime(df_d['datetime'], unit='ms')
        df_d.set_index('datetime', inplace=True)

        ohlcv_h = binance.fetch_ohlcv(symbol, '4h')
        df_h = pd.DataFrame(ohlcv_h, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df_h['datetime'] = pd.to_datetime(df_h['datetime'], unit='ms')
        df_h.set_index('datetime', inplace=True)

        # Save Stochastic Oscilator information
        info[symbol]['slow_osc_d'] = calStochastic_day(df_d)[0]
        info[symbol]['slow_osc_slope_d'] = calStochastic_day(df_d)[1]
        info[symbol]['slow_osc_h'] = calStochastic_hour(df_h)[0]
        info[symbol]['slow_osc_slope_h'] = calStochastic_hour(df_h)[1]
        info[symbol]['macd_osc'] = calMACD(df_d)
        info[symbol]['ma'] = calMA(df_d)
        info[symbol]['open_d'] = df_d['open'][-1]
        info[symbol]['high_h'] = df_h['high'][-1]
        info[symbol]['low_h'] = df_h['low'][-1]

        print(f"코인: {symbol}\n\
            Stochastic OSC (Day): {info[symbol]['slow_osc_d']}\n\
            Stochastic OSC Slope (Day): {info[symbol]['slow_osc_slope_d']}\n\
            Stochastic OSC (Hour): {info[symbol]['slow_osc_h']}\n\
            Stochastic OSC Slope (Hour): {info[symbol]['slow_osc_slope_h']}\n\
            MACD: {info[symbol]['macd_osc']}\n\
            EMA: {info[symbol]['ma']}\n\
            OPEN: {info[symbol]['open_d']}\n")
        time.sleep(0.1)

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
def adjust_money(free_balance, total_hold):
    if total_hold < 5:
        available_hold = 5 - total_hold
        money = round((free_balance * 4 / available_hold - 10), 0)
        return money

total_hold = 0
bot.sendMessage(chat_id = chat_id, text=f"Stochastic (단타) 전략 시작합니다. 화이팅!")
save_info()
free_balance = binance.fetch_balance()['USDT']['free']
money = adjust_money(free_balance, total_hold)
print("Invest money per coin", money)
#for symbol in symbols:
#    current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
#    print(symbol, "Current Price", current_price)
