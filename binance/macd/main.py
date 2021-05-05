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
tickers = ('BTC/USDT', 'ETH/USDT', 'BCH/USDT', 'XRP/USDT', 'EOS/USDT', 'LTC/USDT', 'TRX/USDT', 'ETC/USDT', 'LINK/USDT', 'XLM/USDT', 'ADA/USDT', 'XMR/USDT', 'DASH/USDT', 'ZEC/USDT', 'XTZ/USDT', 'BNB/USDT', 'ATOM/USDT', 'ONT/USDT', 'IOTA/USDT', 'BAT/USDT', 'VET/USDT', 'NEO/USDT', 'QTUM/USDT', 'IOST/USDT', 'THETA/USDT', 'ALGO/USDT', 'ZIL/USDT', 'KNC/USDT', 'ZRX/USDT', 'COMP/USDT', 'OMG/USDT', 'DOGE/USDT', 'SXP/USDT', 'KAVA/USDT', 'BAND/USDT', 'RLC/USDT', 'WAVES/USDT', 'MKR/USDT', 'SNX/USDT', 'DOT/USDT', 'YFI/USDT', 'BAL/USDT', 'CRV/USDT', 'TRB/USDT', 'YFII/USDT', 'RUNE/USDT', 'SUSHI/USDT', 'SRM/USDT', 'BZRX/USDT', 'EGLD/USDT', 'SOL/USDT', 'ICX/USDT', 'STORJ/USDT', 'BLZ/USDT', 'UNI/USDT', 'AVAX/USDT', 'FTM/USDT', 'HNT/USDT', 'ENJ/USDT', 'FLM/USDT', 'TOMO/USDT', 'REN/USDT', 'KSM/USDT', 'NEAR/USDT', 'AAVE/USDT', 'FIL/USDT', 'RSR/USDT', 'LRC/USDT', 'MATIC/USDT', 'OCEAN/USDT', 'CVC/USDT', 'BEL/USDT', 'CTK/USDT', 'AXS/USDT', 'ALPHA/USDT', 'ZEN/USDT', 'SKL/USDT', 'GRT/USDT', '1INCH/USDT', 'BTC/BUSD', 'AKRO/USDT', 'CHZ/USDT', 'SAND/USDT', 'ANKR/USDT', 'LUNA/USDT', 'BTS/USDT', 'LIT/USDT', 'UNFI/USDT', 'DODO/USDT', 'REEF/USDT', 'RVN/USDT', 'SFP/USDT', 'XEM/USDT', 'COTI/USDT', 'CHR/USDT', 'MANA/USDT', 'ALICE/USDT', 'HBAR/USDT', 'ONE/USDT', 'LINA/USDT', 'STMX/USDT', 'DENT/USDT', 'CELR/USDT', 'HOT/USDT', 'MTL/USDT', 'OGN/USDT', 'BTT/USDT', 'NKN/USDT', 'SC/USDT', 'DGB/USDT')
symbols = list(tickers)

# 코인별 저장 정보값 초기화
temp = {}
for symbol in symbols:
    temp[symbol] = {}
    temp[symbol]['amount'] = 0
    temp[symbol]['start_price'] = 0
    temp[symbol]['position'] = ''
    temp[symbol]['hold'] = False

def calMACD(df, m_NumFast=5, m_NumSlow=10, m_NumSignal=3):
    df['EMAFast'] = df['close'].ewm( span = m_NumFast, min_periods = m_NumFast - 1 ).mean()
    df['EMASlow'] = df['close'].ewm( span = m_NumSlow, min_periods = m_NumSlow - 1 ).mean()
    df['MACD'] = df['EMAFast'] - df['EMASlow']
    df['MACD_Signal'] = df['MACD'].ewm( span = m_NumSignal, min_periods = m_NumSignal - 1 ).mean()
    df['MACD_OSC'] = df['MACD'] - df['MACD_Signal']
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

# 투자금액 조정
def adjust_money(total_balance):
    money = 0
    if total_balance <= 500:
        money = 0
    elif 500 < total_balance <= 600:
        money = 100
    elif 600 < total_balance <= 700:
        money = 150
    elif 700 < total_balance <= 800:
        money = 200
    elif 800 < total_balance <= 900:
        money = 250
    elif 900 < total_balance <= 1000:
        money = 300
    elif total_balance > 1000:
        money = 350
    return money

count_trading = 0
count_success = 0
total_hold = 0
start_balance = round(binance.fetch_balance()['USDT']['total'], 2)
bot.sendMessage(chat_id = chat_id, text="MACD 전략 자동매매 시작합니다. 화이팅!")
n = 2
money = adjust_money(start_balance)

while True:
    try:
        for symbol in symbols:

            now = datetime.datetime.now()
            time.sleep(n)

            price_ask = ccxt.binance().fetch_ticker(symbol)['ask'] # 매도 1호가(현재가)
            price_bid = ccxt.binance().fetch_ticker(symbol)['bid'] # 매수 1호가(현재가)

            # 일봉 데이터 수집
            ohlcv = binance.fetch_ohlcv(symbol, '1d')
            df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
            df.set_index('datetime', inplace=True)

            #  macd = calMACD(df)
            macd = calMACD(df)

            print(f"현재시간: {now} 코인: {symbol}\nMACD: {macd['MACD'][-1]} MACD OSC: {macd['MACD_OSC'][-1]}\n")

            if now.hour == 8 and 55 <= now.minute <= 59:
                total_balance = round(binance.fetch_balance()['USDT']['total'], 2)
                bot.sendMessage(chat_id = chat_id, text=f"시작잔고: {start_balance} -> 현재잔고: {total_balance}원\n거래횟수: {count_trading}번\n성공횟수: {count_success}")
                start_balance = total_balance
                count_trading = 0
                count_success = 0
                money = adjust_money(total_balance)
                time.sleep(300)


            # 조건을 만족하면 지정가 매수
            elif temp[symbol]['hold'] == False and total_hold < 3 and macd['MACD'][-1] < 0 and macd['MACD_OSC'][-1] >= 0:
                price_ask = price_unit(price_ask)
                amount = money / price_ask # 매수할 코인 개수
                temp[symbol]['amount'] = amount
                temp[symbol]['start_price'] = price_ask
                binance.create_limit_buy_order(symbol=symbol, amount=amount, price=price_ask) # 지정가 매수
                count_trading += 1
                total_hold += 1
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 매수\n매수가: {price_ask * amount} 거래횟수: {count_trading}번")
                temp[symbol]['hold'] = True
                temp[symbol]['position'] = 'long'

            # 조건을 만족하면 지정가 공매도
            elif temp[symbol]['hold'] == False and total_hold < 3 and macd['MACD'][-1] > 0 and macd['MACD_OSC'][-1] <= 0:
                price_bid = price_unit(price_bid)
                amount = money / price_bid # 매도할 코인 개수
                temp[symbol]['amount'] = amount
                temp[symbol]['start_price'] = price_bid
                binance.create_limit_sell_order(symbol=symbol, amount=amount, price=price_bid) # 지정가 매도
                count_trading += 1
                total_hold += 1
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 매도\n매도가: {price_bid * amount} 거래횟수: {count_trading}번")
                temp[symbol]['hold'] = True
                temp[symbol]['position'] = 'short'

            # 매도 타이밍 조건 만족시 매도 (매수건)
            elif temp[symbol]['hold'] == True and temp[symbol]['position'] == 'long' and macd['MACD_OSC'][-1] <= 0:
                binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=temp[symbol]['amount'], params={"reduceOnly": True})
                total_balance = round(binance.fetch_balance()['USDT']['total'], 2)
                profit = round((price_bid - temp[symbol]['start_price']) / temp[symbol]['start_price'] * 100, 2)
                if profit > 0:
                    count_success += 1
                    bot.sendMessage(chat_id = chat_id, text=f"성공! 코인: {symbol} 성공횟수: {count_success}번\n수익률: {profit} 잔고: {total_balance}")
                else:
                    bot.sendMessage(chat_id = chat_id, text=f"실패! 코인: {symbol}\n수익률: {profit} 잔고: {total_balance}")
                temp[symbol]['hold'] = False
                total_hold -= 1

            # 매수 타이밍 조건 만족시 매수 (공매도건)
            elif temp[symbol]['hold'] == True and temp[symbol]['position'] == 'short' and macd['MACD_OSC'][-1] >= 0:
                binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=temp[symbol]['amount'], params={"reduceOnly": True})
                total_balance = round(binance.fetch_balance()['USDT']['total'], 2)
                profit = round((temp[symbol]['start_price'] - price_ask) / price_ask * 100, 2)
                if profit > 0:
                    count_success += 1
                    bot.sendMessage(chat_id = chat_id, text=f"성공! 코인: {symbol} 성공횟수: {count_success}번\n수익률: {profit} 잔고: {total_balance}")
                else:
                    bot.sendMessage(chat_id = chat_id, text=f"실패! 코인: {symbol}\n수익률: {profit} 잔고: {total_balance}")
                temp[symbol]['hold'] = False
                total_hold -= 1

            elif total_hold == 3 and n == 2:
                symbols.clear()
                for symbol in tickers:
                    if temp[symbol]['hold'] == True:
                        symbols.append(symbol)
                n = 20

            elif total_hold < 3 and n == 20:
                symbols.clear()
                symbols = list(tickers)
                n = 2

    except Exception as e:
        bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
