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
    info[symbol]['price'] = 0
    info[symbol]['open_price'] = 0
    info[symbol]['position'] = 'wait'
    info[symbol]['target_bull'] = 0
    info[symbol]['target_bear'] = 0
    info[symbol]['macd_osc'] = 0
    info[symbol]['slow_osc'] = 0
    info[symbol]['ma'] = 0

def calMACD(df, m_NumFast=12, m_NumSlow=26, m_NumSignal=9):
    df['EMAFast'] = df['close'].ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
    df['EMASlow'] = df['close'].ewm( span = m_NumSlow, min_periods = m_NumSlow - 1 ).mean()
    df['MACD'] = df['EMAFast'] - df['EMASlow']
    df['MACD_Signal'] = df['MACD'].ewm( span = m_NumSignal, min_periods = m_NumSignal - 1 ).mean()
    df['MACD_OSC'] = df['MACD'] - df['MACD_Signal']
    return df['MACD_OSC'][-1]

def calStochastic(df, n=9, m=5, t=3):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    df = df.assign(fast_k=fast_k, fast_d=slow_k, slow_k=slow_k, slow_d=slow_d, slow_osc=slow_osc)
    return df['slow_osc'][-1]

def cal_target(df):
    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    yesterday_range = yesterday['high'] - yesterday['low']
    noise = 1 - abs(yesterday['open'] - yesterday['close']) / (yesterday['high'] - yesterday['low'])
    target_bull = today['open'] + (yesterday_range * noise)
    target_bear = today['open'] - (yesterday_range * noise)
    return target_bull, target_bear

def calMA(df, fast=14):
    df['ma'] = df['close'].ewm(span=fast).mean()
    return df['ma'][-1]

def save_info():
    bot.sendMessage(chat_id = chat_id, text=f"오늘 코인 목표가를 계산중입니다...")
    for symbol in symbols:
        # 일봉 데이터 수집
        ohlcv = binance.fetch_ohlcv(symbol, '1d')
        df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)

        info[symbol]['macd_osc'] = calMACD(df)
        info[symbol]['slow_osc'] = calStochastic(df)
        info[symbol]['target_bull'] = cal_target(df)[0]
        info[symbol]['target_bear'] = cal_target(df)[1]
        info[symbol]['ma'] = calMA(df)
        info[symbol]['open_price'] = binance.fetch_ticker(symbol=symbol)['open'] # 현재가 조회
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
def adjust_money(free_balance, total_hold):
    if total_hold < 5:
        available_hold = 5 - total_hold
        money = round((free_balance * 3 / available_hold - 6), -1)
        return money

total_hold = 0
bot.sendMessage(chat_id = chat_id, text=f"Intergrated Volatility 전략 시작합니다. 화이팅!")
save_info()

while True:
    try:
        for symbol in symbols:

            now = datetime.datetime.now()
            time.sleep(0.5)

            current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
            current_price = price_unit(current_price)

            print(f"현재시간: {now} 코인: {symbol}\n현재가: {current_price}")
            print(f"지정 매수가: {info[symbol]['target_bull']}\n지정 매도가: {info[symbol]['target_bear']}")
            print(f"Stochastic OSC: {info[symbol]['slow_osc']}\nEMA: {info[symbol]['ma']}")
            print(f"포지션 상태: {info[symbol]['position']}\n총 보유 코인: {total_hold}개\n")

            if now.hour == 8 and 55 <= now.minute <= 59:
                # 매수건 청산
                if info[symbol]['position'] == 'long':
                    binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=info[symbol]['amount'], params={"reduceOnly": True})
                    profit = round((current_price - info[symbol]['target_bull']) / info[symbol]['target_bull'] * 100, 2)
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} (롱)\n매수가: {info[symbol]['price']} -> 매도가: {current_price}\n수익률: {profit}")
                    info[symbol]['position'] = 'wait'
                # 매도건 청산
                elif info[symbol]['position'] == 'short':
                    binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=info[symbol]['amount'], params={"reduceOnly": True})
                    profit = round((info[symbol]['target_bear']) - current_price / current_price * 100, 2)
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} (숏)\n매도가: {info[symbol]['price']} -> 매수가: {current_price}\n수익률: {profit}")
                    info[symbol]['position'] = 'wait'

            elif now.hour == 9 and 0 <= now.minute <= 1:
                total_hold = 0
                free_balance = round(binance.fetch_balance()['USDT']['free'], 2)
                money = adjust_money(free_balance=free_balance, total_hold=total_hold) # 코인별 투자금액
                bot.sendMessage(chat_id = chat_id, text=f"시작잔고: {start_balance} -> 현재잔고: {total_balance}원\n오늘 1코인당 투자금액: {money}")
                start_balance = total_balance
                save_info()

            # 조건을 만족하면 지정가 매수
            elif info[symbol]['position'] == 'wait' and total_hold < 3 and info[symbol]['slow_osc'] > 0 and info[symbol]['ma'] < info[symbol]['open_price'] and (info[symbol]['target_bull'] * 0.995) <= current_price <= (info[symbol]['target_bull'] * 1.005):
                amount = money / current_price # 매수할 코인 개수
                binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=amount)
                info[symbol]['price'] = current_price
                info[symbol]['position'] = 'long' # 포지션 'long' 으로 변경
                info[symbol]['amount'] = amount # 코인 갯수 저장
                total_hold += 1
                bot.sendMessage(chat_id = chat_id, text=f"{symbol} 롱 포지션\n매수가: {current_price}\n투자금액: {money}\n총 보유 코인: {total_hold}")

            # 조건을 만족하면 지정가 공매도
            elif info[symbol]['position'] == 'wait' and total_hold < 3 and info[symbol]['slow_osc'] < 0 and info[symbol]['ma'] > info[symbol]['open_price'] and (info[symbol]['target_bear'] * 0.995) <= current_price <= (info[symbol]['target_bear'] * 1.005):
                amount = money / current_price # 매도할 코인 개수
                binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=amount)
                info[symbol]['price'] = current_price
                info[symbol]['position'] = 'short' # 포지션 'short' 으로 변경
                info[symbol]['amount'] = amount # 코인 갯수 저장
                total_hold += 1
                bot.sendMessage(chat_id = chat_id, text=f"{symbol} 숏 포지션\n매도가: {current_price}\n투자금액: {money}\n총 보유 코인: {total_hold}")

            # Total 코인 도달시 장마감까지 기다리기
            elif total_hold == 3:
                while now.hour != 8 and now.minute != 55:
                    time.sleep(1)

    except Exception as e:
        bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
