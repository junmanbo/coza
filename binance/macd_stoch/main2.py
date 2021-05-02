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
tickers = ('BTC/USDT', 'ETH/USDT', 'BCH/USDT', 'XRP/USDT', 'EOS/USDT', 'LTC/USDT', 'TRX/USDT', 'ETC/USDT', 'LINK/USDT', 'XLM/USDT', 'ADA/USDT', 'XMR/USDT', 'DASH/USDT', 'ZEC/USDT', 'XTZ/USDT', 'BNB/USDT', 'ATOM/USDT', 'ONT/USDT', 'IOTA/USDT', 'BAT/USDT', 'IOST/USDT', 'THETA/USDT', 'ALGO/USDT', 'ZIL/USDT', 'KNC/USDT', 'ZRX/USDT', 'COMP/USDT', 'OMG/USDT', 'DOGE/USDT', 'SXP/USDT', 'KAVA/USDT', 'BAND/USDT', 'RLC/USDT', 'WAVES/USDT', 'MKR/USDT', 'SNX/USDT', 'DOT/USDT', 'YFI/USDT', 'BAL/USDT', 'CRV/USDT', 'TRB/USDT', 'YFII/USDT', 'RUNE/USDT', 'SUSHI/USDT', 'SRM/USDT', 'BZRX/USDT', 'EGLD/USDT', 'SOL/USDT', 'ICX/USDT', 'STORJ/USDT', 'UNI/USDT', 'AVAX/USDT', 'FTM/USDT', 'HNT/USDT', 'ENJ/USDT', 'NEAR/USDT', 'AAVE/USDT')

symbols = list(tickers)

def calMACD(df, m_NumFast=12, m_NumSlow=26, m_NumSignal=9):
    df['EMAFast'] = df['close'].ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
    df['EMASlow'] = df['close'].ewm( span = m_NumSlow, min_periods = m_NumSlow - 1 ).mean()
    df['MACD'] = df['EMAFast'] - df['EMASlow']
    df['MACD_Signal'] = df['MACD'].ewm( span = m_NumSignal, min_periods = m_NumSignal - 1 ).mean()
    df['MACD_OSC'] = df['MACD'] - df['MACD_Signal']
    bullish = df['MACD_OSC'][-1] - df['MACD_OSC'][-2]
    return bullish

def calStochastic(df, n=14, m=5, t=5):
    df = pd.DataFrame(df)
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_signal = slow_k - slow_d
    df = df.assign(fast_k=fast_k, fast_d=slow_k, slow_k=slow_k, slow_d=slow_d, slow_signal=slow_signal)
    return df

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

amount = 0
count_trading = 0
count_success = 0
count_loose = 0
order = {}
order1 = {}
order2 = {}
hold1 = False
hold2 = False
n = 2
start_balance = binance.fetch_balance()['USDT']['total']

bot.sendMessage(chat_id = chat_id, text="macd+stochastic 전략 자동매매 시작합니다. 화이팅!")

while True:
    try:
        for symbol in symbols:
            now = datetime.datetime.now()
            time.sleep(n)
            price1 = ccxt.binance().fetch_ticker(symbol)['ask'] # 매도 1호가(현재가)
            price2 = ccxt.binance().fetch_ticker(symbol)['bid'] # 매수 1호가(현재가)

            ohlcv = binance.fetch_ohlcv(symbol, '1d')
            df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
            df.set_index('datetime', inplace=True)

            macd = calMACD(df)
            stochastic = calStochastic(df)

            print(f"현재시간: {now} 코인: {symbol}\nStochastic K: {stochastic['slow_k'][-1]} MACD신호: {macd}\n")

            if now.hour == 8 and 55 <= now.minute <= 59:
                total_balance = binance.fetch_balance()['USDT']['total']
                bot.sendMessage(chat_id = chat_id, text=f"잔고: {total_balance}원\n거래횟수: {count_trading}번\n성공횟수: {count_success}\n실패횟수: {count_loose}번")
                count_trading = 0
                count_loose = 0
                count_success = 0
                time.sleep(300)

            # 조건을 만족하면 지정가 매수
            elif hold1 == False and hold2 == False and 30 < stochastic['slow_k'][-1] <= 70 and stochastic['slow_signal'][-1] > stochastic['slow_signal'][-2] and macd > 0 and stochastic['slow_k'][-1] - 3 <= stochastic['slow_d'][-1] <= stochastic['slow_k'][-1] + 3:
                price1 = price_unit(price1) # 목표가 (호가 단위)
                amount = 1500 / price1 # 매수할 코인 개수
                order = binance.create_limit_buy_order(symbol=symbol, amount=amount, price=price1) # 지정가 매수
                count_trading += 1
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 예약매수\n매수가: {price1} 거래횟수: {count_trading}번")
                symbols.clear()
                symbols = [symbol]
                n = 300
                hold1 = True # 코인 보유

            # 조건을 만족하면 지정가 공매도
            elif hold2 == False and hold2== False and 30 < stochastic['slow_k'][-1] <= 70 and stochastic['slow_signal'][-1] < stochastic['slow_signal'][-2] and macd < 0 and stochastic['slow_k'][-1] - 3 <= stochastic['slow_d'][-1] <= stochastic['slow_k'][-1] + 3:
                price2 = price_unit(price2) # 목표가 (호가 단위)
                amount = 1500 / price2 # 매도할 코인 개수
                order = binance.create_limit_sell_order(symbol=symbol, amount=amount, price=price2) # 지정가 매도
                count_trading += 1
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 예약매도\n매도가: {price2} 거래횟수: {count_trading}번")
                symbols.clear()
                symbols = [symbol]
                n = 300
                hold2 = True # 코인 보유

            # 매도 타이밍 -> 매도 후 리스트 복구
            elif hold1 == True and stochastic['slow_signal'][-1] < stochastic['slow_signal'][-2] and macd < 0:
                order = binance.create_limit_sell_order(symbol=symbol, amount=amount, price=price2)
                time.sleep(120)
                total_balance = binance.fetch_balance()['USDT']['total']
                if total_balance - start_balance > 0:
                    count_success += 1
                    bot.sendMessage(chat_id = chat_id, text=f"성공! 코인: {symbol} 성공횟수: {count_success}번\n잔고: {total_balance}")
                else:
                    count_loose += 1
                    bot.sendMessage(chat_id = chat_id, text=f"실패! 코인: {symbol} 실패횟수: {count_success}번\n잔고: {total_balance}")
                start_balance = total_balance
                hold1 = False # 코인 미보유
                symbols.clear()
                symbols = list(tickers)

            # 매수 타이밍 -> 매수 후 리스트 복구
            elif hold2 == True and stochastic['slow_signal'][-1] > stochastic['slow_signal'][-2] and macd > 0:
                order = binance.create_limit_buy_order(symbol=symbol, amount=amount, price=price1)
                time.sleep(120)
                total_balance = binance.fetch_balance()['USDT']['total']
                if total_balance - start_balance > 0:
                    count_success += 1
                    bot.sendMessage(chat_id = chat_id, text=f"성공! 코인: {symbol} 성공횟수: {count_success}번\n잔고: {total_balance}")
                else:
                    count_loose += 1
                    bot.sendMessage(chat_id = chat_id, text=f"실패! 코인: {symbol} 실패횟수: {count_success}번\n잔고: {total_balance}")
                start_balance = total_balance
                hold2 = False # 코인 미보유
                symbols.clear()
                symbols = list(tickers)
    except Exception as e:
        bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
