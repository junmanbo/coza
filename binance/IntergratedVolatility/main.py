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
symbols = ['BTC/USDT', 'ETH/USDT', 'BCH/USDT', 'XRP/USDT', 'EOS/USDT', 'LTC/USDT', 'TRX/USDT', 'ETC/USDT', 'LINK/USDT', 'XLM/USDT', 'ADA/USDT', 'XMR/USDT', 'DASH/USDT', 'ZEC/USDT', 'XTZ/USDT', 'BNB/USDT', 'ATOM/USDT', 'ONT/USDT', 'IOTA/USDT', 'BAT/USDT', 'VET/USDT', 'NEO/USDT', 'QTUM/USDT', 'THETA/USDT', 'ALGO/USDT', 'ZIL/USDT', 'ZRX/USDT', 'COMP/USDT', 'OMG/USDT', 'DOGE/USDT', 'WAVES/USDT', 'MKR/USDT', 'SNX/USDT', 'DOT/USDT', 'YFI/USDT', 'RUNE/USDT', 'SUSHI/USDT', 'EGLD/USDT', 'SOL/USDT', 'ICX/USDT', 'UNI/USDT', 'AVAX/USDT', 'FTM/USDT', 'HNT/USDT', 'ENJ/USDT', 'KSM/USDT', 'NEAR/USDT', 'AAVE/USDT', 'FIL/USDT', 'RSR/USDT', 'MATIC/USDT', 'ZEN/USDT', 'GRT/USDT', '1INCH/USDT', 'CHZ/USDT', 'ANKR/USDT', 'LUNA/USDT', 'RVN/USDT', 'XEM/USDT', 'MANA/USDT', 'HBAR/USDT', 'ONE/USDT', 'HOT/USDT', 'BTT/USDT', 'SC/USDT', 'DGB/USDT']

# 코인별 저장 정보값 초기화
info = {}
for symbol in symbols:
    info[symbol] = {}
    info[symbol]['amount'] = 0
    info[symbol]['position'] = 'wait'
    info[symbol]['target_bull'] = 0
    info[symbol]['target_bear'] = 0
    info[symbol]['macd_osc'] = 0
    info[symbol]['slow_osc'] = 0
    info[symbol]['slow_k'] = 0

def calMACD(df, m_NumFast=14, m_NumSlow=30, m_NumSignal=10):
    df['EMAFast'] = df['close'].ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
    df['EMASlow'] = df['close'].ewm( span = m_NumSlow, min_periods = m_NumSlow - 1 ).mean()
    df['MACD'] = df['EMAFast'] - df['EMASlow']
    df['MACD_Signal'] = df['MACD'].ewm( span = m_NumSignal, min_periods = m_NumSignal - 1 ).mean()
    df['MACD_OSC'] = df['MACD'] - df['MACD_Signal']
    return df['MACD_OSC'][-1]

def calStochastic(df, n=14, m=7, t=7):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    df = df.assign(fast_k=fast_k, fast_d=slow_k, slow_k=slow_k, slow_d=slow_d, slow_osc=slow_osc)
    return df['slow_osc'][-1], df['slow_k'][-1]

def cal_target(df):
    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    yesterday_range = yesterday['high'] - yesterday['low']
    noise = 1 - abs(yesterday['open'] - yesterday['close']) / (yesterday['high'] - yesterday['low'])
    target_bull = today['open'] + (yesterday_range * noise)
    target_bear = today['open'] - (yesterday_range * noise)
    return target_bull, target_bear

def save_info():
    bot.sendMessage(chat_id = chat_id, text=f"오늘 코인 목표가를 계산중입니다...")
    for symbol in symbols:
        # 일봉 데이터 수집
        ohlcv = binance.fetch_ohlcv(symbol, '1d')
        df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)

        info[symbol]['macd_osc'] = calMACD(df)
        info[symbol]['slow_osc'] = calStochastic(df)[0]
        info[symbol]['slow_k'] = calStochastic(df)[1]
        info[symbol]['target_bull'] = cal_target(df)[0]
        info[symbol]['target_bear'] = cal_target(df)[1]
        time.sleep(1)
    bot.sendMessage(chat_id = chat_id, text=f"오늘 코인 목표가 계산이 끝났습니다.")

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
        money = 300
    elif 600 < total_balance <= 700:
        money = 350
    elif 700 < total_balance <= 800:
        money = 400
    elif 800 < total_balance <= 900:
        money = 450
    elif 900 < total_balance <= 1000:
        money = 500
    elif 1000 < total_balance <= 1100:
        money = 550
    elif 1100 < total_balance <= 1200:
        money = 600
    elif 1200 < total_balance <= 1300:
        money = 650
    elif 1300 < total_balance <= 1400:
        money = 700
    elif 1400 < total_balance <= 1500:
        money = 750
    elif total_balance > 1500:
        money = 800
    return money

total_hold = 0
start_balance = round(binance.fetch_balance()['USDT']['total'], 2)
money = adjust_money(start_balance)
bot.sendMessage(chat_id = chat_id, text=f"통합 Volatility 전략 자동매매 시작합니다. 화이팅!\n오늘 1코인당 투자 금액: {money}")
save_info()

while True:
    try:
        for symbol in symbols:

            now = datetime.datetime.now()
            time.sleep(1)

            price_ask = ccxt.binance().fetch_ticker(symbol)['ask'] # 매도 1호가(현재가)
            price_bid = ccxt.binance().fetch_ticker(symbol)['bid'] # 매수 1호가(현재가)

            print(f"현재시간: {now} 코인: {symbol}\n현재가: {price_ask}\n지정 매수가: {info[symbol]['target_bull']}\n지정 매도가: {info[symbol]['target_bear']}\nMACD OSC: {info[symbol]['macd_osc']}\nStochastic OSC: {info[symbol]['slow_osc']}\nStochastic Slow K: {info[symbol]['slow_k']}\n포지션 상태: {info[symbol]['position']}\n총 보유 코인: {total_hold}개\n")

            if now.hour == 8 and 50 <= now.minute <= 59:
                # 매수건 청산
                if info[symbol]['position'] == 'long':
                    binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=info[symbol]['amount'], params={"reduceOnly": True})
                    profit = round((price_bid - info[symbol]['target_bull']) / info[symbol]['target_bull'] * 100, 2)
                    if profit > 0:
                        bot.sendMessage(chat_id = chat_id, text=f"Success! 코인: {symbol}\n수익률: {profit}")
                    else:
                        bot.sendMessage(chat_id = chat_id, text=f"Failure! 코인: {symbol}\n수익률: {profit}")
                    info[symbol]['position'] = 'wait'
                # 매도건 청산
                elif info[symbol]['position'] == 'short':
                    binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=info[symbol]['amount'], params={"reduceOnly": True})
                    profit = round((info[symbol]['target_bear']) - price_ask / price_ask * 100, 2)
                    if profit > 0:
                        bot.sendMessage(chat_id = chat_id, text=f"Success! 코인: {symbol}\n수익률: {profit}")
                    else:
                        bot.sendMessage(chat_id = chat_id, text=f"Failure! 코인: {symbol}\n수익률: {profit}")
                    info[symbol]['position'] = 'wait'

            elif now.hour == 9 and 0 <= now.minute <= 1:
                total_balance = round(binance.fetch_balance()['USDT']['total'], 2)
                money = adjust_money(total_balance)
                total_hold = 0
                bot.sendMessage(chat_id = chat_id, text=f"시작잔고: {start_balance} -> 현재잔고: {total_balance}원\n오늘 1코인당 투자금액: {money}")
                start_balance = total_balance
                save_info()

            # 조건을 만족하면 지정가 매수
            elif info[symbol]['position'] == 'wait' and total_hold < 3 and info[symbol]['macd_osc'] > 0 and info[symbol]['slow_osc'] > 0 and info[symbol]['slow_k'] < 75 and (info[symbol]['target_bull'] * 0.999) <= price_ask <= (info[symbol]['target_bull'] * 1.001):
                price_ask = price_unit(price_ask)
                amount = money / price_ask # 매수할 코인 개수
                binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=amount)
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 매수")
                info[symbol]['amount'] = amount
                info[symbol]['position'] = 'long'
                total_hold += 1

            # 조건을 만족하면 지정가 공매도
            elif info[symbol]['position'] == 'wait' and total_hold < 3 and info[symbol]['macd_osc'] < 0 and info[symbol]['slow_osc'] < 0 and info[symbol]['slow_k'] > 35 and (info[symbol]['target_bear'] * 0.999) <= price_bid <= (info[symbol]['target_bear'] * 1.001):
                price_bid = price_unit(price_bid)
                amount = money / price_bid # 매도할 코인 개수
                binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=amount)
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 매도")
                info[symbol]['amount'] = amount
                info[symbol]['position'] = 'short'
                total_hold += 1

            # Total 코인 도달시 장마감까지 기다리기
            elif total_hold == 3:
                while now.hour != 8 and now.minute != 50:
                    time.sleep(1)

    except Exception as e:
        bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
