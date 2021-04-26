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
tickers = ('BTC/USDT', 'ETH/USDT', 'BCH/USDT', 'XRP/USDT', 'EOS/USDT', 'LTC/USDT', 'TRX/USDT', 'ETC/USDT', 'LINK/USDT', 'XLM/USDT', 'ADA/USDT', 'XMR/USDT', 'DASH/USDT', 'ZEC/USDT', 'XTZ/USDT', 'BNB/USDT', 'ATOM/USDT', 'ONT/USDT', 'IOTA/USDT', 'BAT/USDT', 'VET/USDT', 'NEO/USDT', 'QTUM/USDT', 'IOST/USDT', 'THETA/USDT', 'ALGO/USDT', 'ZIL/USDT', 'KNC/USDT', 'ZRX/USDT', 'COMP/USDT', 'OMG/USDT', 'DOGE/USDT', 'SXP/USDT', 'KAVA/USDT', 'BAND/USDT', 'RLC/USDT', 'WAVES/USDT', 'MKR/USDT', 'SNX/USDT', 'DOT/USDT', 'YFI/USDT', 'BAL/USDT', 'CRV/USDT', 'TRB/USDT', 'YFII/USDT', 'RUNE/USDT', 'SUSHI/USDT', 'SRM/USDT', 'BZRX/USDT', 'EGLD/USDT', 'SOL/USDT', 'ICX/USDT', 'STORJ/USDT', 'BLZ/USDT', 'UNI/USDT', 'AVAX/USDT', 'FTM/USDT', 'HNT/USDT', 'ENJ/USDT', 'FLM/USDT', 'TOMO/USDT', 'REN/USDT', 'KSM/USDT', 'NEAR/USDT', 'AAVE/USDT', 'FIL/USDT', 'RSR/USDT', 'LRC/USDT', 'MATIC/USDT', 'OCEAN/USDT', 'CVC/USDT', 'BEL/USDT', 'CTK/USDT', 'AXS/USDT', 'ALPHA/USDT', 'ZEN/USDT', 'SKL/USDT', 'GRT/USDT', '1INCH/USDT', 'BTC/BUSD', 'AKRO/USDT', 'CHZ/USDT', 'SAND/USDT', 'ANKR/USDT', 'LUNA/USDT', 'BTS/USDT', 'LIT/USDT', 'UNFI/USDT', 'DODO/USDT', 'REEF/USDT', 'RVN/USDT', 'SFP/USDT', 'XEM/USDT', 'COTI/USDT', 'CHR/USDT', 'MANA/USDT', 'ALICE/USDT', 'HBAR/USDT', 'ONE/USDT', 'LINA/USDT', 'STMX/USDT', 'DENT/USDT', 'CELR/USDT', 'HOT/USDT', 'MTL/USDT', 'OGN/USDT', 'BTT/USDT', 'NKN/USDT', 'SC/USDT', 'DGB/USDT')

symbols = list(tickers)

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

count_trading = 0
count_success = 0
count_loose = 0
order = {}
order1 = {}
order2 = {}
hold = False

bot.sendMessage(chat_id = chat_id, text="추격매수 전략 자동매매 시작합니다. 화이팅!")
print("추격매수 전략 시작!")

while True:
    try:
        for symbol in symbols:
            now = datetime.datetime.now()
            time.sleep(0.1)
            target = cal_target(symbol) # 목표가
            price = ccxt.binance().fetch_ticker(symbol)['ask'] # 매도 1호가(현재가)
            balance = binance.fetch_balance()['USDT']['free']

            profit = price_unit(target * 1.02) # 익절가
            limit = price_unit(target * 0.98) # 손절가
            print(f"현재시간: {now} 현재잔고: {balance} 코인: {symbol}\n현재가: {price} -> 목표가: {target}\n")

            if now.hour == 8 and now.minute == 59 and 50 <= now.second <= 59:
                total_balance = binance.fetch_balance()['USDT']['total']
                bot.sendMessage(chat_id = chat_id, text=f"추격매수 전략 잔고: {total_balance}원\n거래횟수: {count_trading}번\n성공횟수: {count_success}\n실패횟수: {count_loose}번")
                count_trading = 0
                count_loose = 0
                count_success = 0
                time.sleep(10)

            # 조건을 만족하면 지정가 매도
            elif hold == False and balance >= 250 and target <= price <= (target * 1.001):
                target = price_unit(target) # 목표가 (호가 단위)
                amount = 250 / target # 매도할 코인 개수
                order = binance.create_limit_buy_order(symbol, amount, target) # 지정가 매도
                count_trading += 1
                bot.sendMessage(chat_id = chat_id, text=f"추격매수 전략 코인: {symbol} 예약매수\n매수가: {target} 거래횟수: {count_trading}번")
                stop_loss_params = {'stopPrice': target * 0.98}
                order1 = binance.create_order(symbol, 'stop_market', 'sell', amount, None, stop_loss_params)
                take_profit_params = {'stopPrice': target * 1.02}
                order2 = binance.create_order(symbol, 'take_profit_market', 'sell', amount, None, take_profit_params)
                symbols.clear()
                symbols = [symbol]
                hold = True # 코인 보유

            # 코인 보유 상태인 경우 익절가 체크후 리스트 복구
            elif hold == True and profit < price:
                time.sleep(5)
                count_success += 1
                total_balance = binance.fetch_balance()['USDT']['total']
                bot.sendMessage(chat_id = chat_id, text=f"추격매수 전략 코인: {symbol} 목표가 도달!\n성공횟수: {count_success}번\n잔고: {total_balance}")
                hold = False # 코인 미보유
                resp = binance.cancel_order(order1['id'], symbol) # Stop Loss 주문 취소
                symbols.clear()
                symbols = list(tickers)

            # 코인 보유 상태인 경우 손절가 체크후 리스트 복구
            elif hold == True and limit > price:
                time.sleep(5)
                count_loose += 1
                total_balance = binance.fetch_balance()['USDT']['total']
                bot.sendMessage(chat_id = chat_id, text=f"추격매수 전략 코인: {symbol} 손절매...\n실패횟수: {count_loose}번\n잔고: {total_balance}")
                hold = False # 코인 미보유
                resp = binance.cancel_order(order2['id'], symbol) # Stop Profit 주문 취소
                symbols.clear()
                symbols = list(tickers)
    except Exception as e:
        print("에러발생", e)
