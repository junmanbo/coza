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
tickers = ('BTC/USDT', 'ETH/USDT', 'BCH/USDT', 'XRP/USDT', 'EOS/USDT', 'LTC/USDT', 'TRX/USDT', 'ETC/USDT', 'LINK/USDT', 'XLM/USDT', 'ADA/USDT', 'XMR/USDT', 'DASH/USDT', 'ZEC/USDT', 'XTZ/USDT', 'BNB/USDT', 'ATOM/USDT', 'ONT/USDT', 'IOTA/USDT', 'BAT/USDT', 'VET/USDT', 'NEO/USDT', 'QTUM/USDT', 'IOST/USDT', 'THETA/USDT', 'ALGO/USDT', 'ZIL/USDT', 'KNC/USDT', 'ZRX/USDT', 'COMP/USDT', 'OMG/USDT', 'DOGE/USDT', 'SXP/USDT', 'KAVA/USDT', 'BAND/USDT', 'RLC/USDT', 'WAVES/USDT', 'MKR/USDT', 'SNX/USDT', 'DOT/USDT', 'YFI/USDT', 'BAL/USDT', 'CRV/USDT', 'TRB/USDT', 'YFII/USDT', 'RUNE/USDT', 'SUSHI/USDT', 'SRM/USDT', 'BZRX/USDT', 'EGLD/USDT', 'SOL/USDT', 'ICX/USDT', 'STORJ/USDT', 'UNI/USDT', 'AVAX/USDT', 'FTM/USDT', 'HNT/USDT', 'ENJ/USDT', 'NEAR/USDT', 'AAVE/USDT', 'FIL/USDT', 'CHZ/USDT', 'SAND/USDT', 'ANKR/USDT', 'LUNA/USDT', 'XEM/USDT', 'CHR/USDT', 'MANA/USDT', 'HBAR/USDT', 'BTT/USDT')

symbols = list(tickers)

# 매수 목표가 구하기
def cal_target_bull(symbol):
    ohlcv = binance.fetch_ohlcv(symbol, '1d')
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)

    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    yesterday_range = yesterday['high'] - yesterday['low']
    noise = 1 - abs(yesterday['open'] - yesterday['close']) / (yesterday['high'] - yesterday['low'])
    target = today['open'] + (yesterday_range * noise)
    return target

# 공매도 목표가 구하기
def cal_target_bear(symbol):
    ohlcv = binance.fetch_ohlcv(symbol, '1d')
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)

    yesterday = df.iloc[-2]
    today = df.iloc[-1]
    yesterday_range = yesterday['high'] - yesterday['low']
    noise = 1 - abs(yesterday['open'] - yesterday['close']) / (yesterday['high'] - yesterday['low'])
    target = today['open'] - (yesterday_range * noise)
    return target

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

# 코인별 저장 정보값 초기화
temp = {}
for symbol in symbols:
    temp[symbol] = {}
    temp[symbol]['amount'] = 0
    temp[symbol]['start_price'] = 0
    temp[symbol]['position'] = ''
    temp[symbol]['hold'] = False
    temp[symbol]['target_bull'] = cal_target_bull(symbol)
    temp[symbol]['target_bear'] = cal_target_bear(symbol)
    temp[symbol]['profit_bull'] = temp[symbol]['target_bull'] * 1.03
    temp[symbol]['loss_bull'] = temp[symbol]['target_bull'] * 0.98
    temp[symbol]['profit_bear'] = temp[symbol]['target_bear'] * 0.97
    temp[symbol]['loss_bear'] = temp[symbol]['target_bear'] * 1.02
    temp[symbol]['order1'] = {}
    temp[symbol]['order2'] = {}

count_trading = 0
count_success = 0
total_hold = 0
start_balance = round(binance.fetch_balance()['USDT']['total'], 2)
bot.sendMessage(chat_id = chat_id, text="변동성 돌파 전략 자동매매 시작합니다. 화이팅!")

while True:
    try:
        for symbol in symbols:
            now = datetime.datetime.now()
            time.sleep(2)
            price_ask = ccxt.binance().fetch_ticker(symbol)['ask'] # 매도 1호가(현재가)
            price_bid = ccxt.binance().fetch_ticker(symbol)['bid'] # 매수 1호가(현재가)

            print(f"현재시간: {now} 코인: {symbol}\n현재가: {price_ask}\n매수 목표가: {temp['target_bull']}\n공매도 목표가: {temp['target_bear']}\n")

            if now.hour == 9 and 10 <= now.minute <= 19:
                total_balance = binance.fetch_balance()['USDT']['total']
                bot.sendMessage(chat_id = chat_id, text=f"변동성 돌파전략\n시작잔고: {start_balance} -> 현재잔고: {total_balance}원\n거래횟수: {count_trading}번\n성공횟수: {count_success}")
                # 오늘 목표가 계산
                for symbol in symbols:
                    temp[symbol]['target_bull'] = cal_target_bull(symbol)
                    temp[symbol]['target_bear'] = cal_target_bear(symbol)
                    temp[symbol]['profit_bull'] = temp[symbol]['target_bull'] * 1.03
                    temp[symbol]['loss_bull'] = temp[symbol]['target_bull'] * 0.98
                    temp[symbol]['profit_bear'] = temp[symbol]['target_bear'] * 0.97
                    temp[symbol]['loss_bear'] = temp[symbol]['target_bear'] * 1.02
                count_trading = 0
                count_success = 0
                start_balance = total_balance
                time.sleep(600)

            # 조건을 만족하면 지정가 매수 (매수건)
            elif temp[symbol]['hold'] == False and total_hold < 4 and (temp[symbol]['target_bull'] * 0.999) <= price_ask <= (temp[symbol]['target_bull'] * 1.001):
                target = price_unit(price_ask) # 목표가 (호가 단위)
                amount = 500 / target # 매수할 코인 개수
                binance.create_limit_buy_order(symbol=symbol, amount=amount, price=target) # 지정가 매수
                count_trading += 1
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 매수\n매수가: {target} 거래횟수: {count_trading}번")
                time.sleep(10)
                stop_loss_params = {'stopPrice': temp[symbol]['loss_bull']}
                temp[symbol]['order1'] = binance.create_order(symbol, 'stop_market', 'sell', amount, None, stop_loss_params)
                take_profit_params = {'stopPrice': temp[symbol]['profit_bull']}
                temp[symbol]['order2'] = binance.create_order(symbol, 'take_profit_market', 'sell', amount, None, take_profit_params)
                temp[symbol]['amount'] = amount
                temp[symbol]['start_price'] = price_ask
                temp[symbol]['hold'] = True
                temp[symbol]['position'] = 'long'
                total_hold += 1

            # 조건을 만족하면 지정가 매도 (공매도건)
            elif temp[symbol]['hold'] == False and total_hold < 4 and (temp[symbol]['target_bear'] * 0.999) <= price_bid <= (temp[symbol]['target_bear'] * 1.001):
                target = price_unit(price_bid) # 목표가 (호가 단위)
                amount = 500 / target # 매도할 코인 개수
                binance.create_limit_sell_order(symbol=symbol, amount=amount, price=target) # 지정가 매도
                count_trading += 1
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 매도\n매도가: {target} 거래횟수: {count_trading}번")
                time.sleep(10)
                stop_loss_params = {'stopPrice': temp[symbol]['loss_bear']}
                temp[symbol]['order1'] = binance.create_order(symbol, 'stop_market', 'buy', amount, None, stop_loss_params)
                take_profit_params = {'stopPrice': temp[symbol]['profit_bear']}
                temp[symbol]['order2'] = binance.create_order(symbol, 'take_profit_market', 'buy', amount, None, take_profit_params)
                temp[symbol]['amount'] = amount
                temp[symbol]['start_price'] = price_bid
                temp[symbol]['hold'] = True
                temp[symbol]['position'] = 'short'
                total_hold += 1

            # (매수건) 코인 보유 익절 목표 도달시 주문 취소
            elif temp[symbol]['hold'] == True and temp[symbol]['position'] == 'long' and price_bid > temp[symbol]['profit_bull']:
                time.sleep(60)
                binance.cancel_order(temp[symbol]['order1']['id'], symbol) # Stop Loss 주문 취소
                total_balance = binance.fetch_balance()['USDT']['total']
                profit = round((price_bid - temp[symbol]['start_price']) / temp[symbol]['start_price'] * 100, 2)
                count_success += 1
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 목표가 도달!\n성공횟수: {count_success}번\n수익률: {profit} 잔고: {total_balance}")
                total_hold -= 1
                temp[symbol]['hold'] = False

            # (매수건) 코인 보유 손절가 도달시 주문 취소
            elif temp[symbol]['hold'] == True and temp[symbol]['position'] == 'long' and price_bid < temp[symbol]['loss_bull']:
                time.sleep(60)
                binance.cancel_order(temp[symbol]['order2']['id'], symbol) # Stop Profit 주문 취소
                total_balance = binance.fetch_balance()['USDT']['total']
                profit = round((price_bid - temp[symbol]['start_price']) / temp[symbol]['start_price'] * 100, 2)
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 손절매!\n실패횟수: {count_trading - count_success}번\n수익률: {profit} 잔고: {total_balance}")
                total_hold -= 1
                temp[symbol]['hold'] = False

            # (매도건) 코인 보유 익절 목표 도달시 주문 취소
            elif temp[symbol]['hold'] == True and temp[symbol]['position'] == 'short' and price_ask < temp[symbol]['profit_bear']:
                time.sleep(60)
                binance.cancel_order(temp[symbol]['order1']['id'], symbol) # Stop Loss 주문 취소
                total_balance = binance.fetch_balance()['USDT']['total']
                profit = round((temp[symbol]['start_price'] - price_ask) / price_ask * 100, 2)
                count_success += 1
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 목표가 도달!\n성공횟수: {count_success}번\n수익률: {profit} 잔고: {total_balance}")
                total_hold -= 1
                temp[symbol]['hold'] = False

            # (매도건) 코인 보유 손절가 도달시 주문 취소
            elif temp[symbol]['hold'] == True and temp[symbol]['position'] == 'short' and price_ask > temp[symbol]['loss_bear']:
                time.sleep(60)
                binance.cancel_order(temp[symbol]['order2']['id'], symbol) # Stop Profit 주문 취소
                total_balance = binance.fetch_balance()['USDT']['total']
                profit = round((temp[symbol]['start_price'] - price_ask) / price_ask * 100, 2)
                bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} 손절매!\n실패횟수: {count_trading - count_success}번\n수익률: {profit} 잔고: {total_balance}")
                total_hold -= 1
                temp[symbol]['hold'] = False

    except Exception as e:
        bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")