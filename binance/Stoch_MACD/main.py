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
tickers = ('BTC/USDT', 'ETH/USDT', 'BCH/USDT', 'XRP/USDT', 'EOS/USDT', 'LTC/USDT', 'TRX/USDT', 'ETC/USDT', 'LINK/USDT', 'XLM/USDT', 'ADA/USDT', 'XMR/USDT', 'DASH/USDT', 'ZEC/USDT', 'XTZ/USDT', 'BNB/USDT', 'ATOM/USDT', 'ONT/USDT', 'IOTA/USDT', 'BAT/USDT', 'VET/USDT', 'NEO/USDT', 'QTUM/USDT', 'THETA/USDT', 'ALGO/USDT', 'ZIL/USDT', 'ZRX/USDT', 'COMP/USDT', 'OMG/USDT', 'DOGE/USDT', 'WAVES/USDT', 'MKR/USDT', 'SNX/USDT', 'DOT/USDT', 'YFI/USDT', 'RUNE/USDT', 'SUSHI/USDT', 'EGLD/USDT', 'SOL/USDT', 'ICX/USDT', 'UNI/USDT', 'AVAX/USDT', 'FTM/USDT', 'HNT/USDT', 'ENJ/USDT', 'KSM/USDT', 'NEAR/USDT', 'AAVE/USDT', 'FIL/USDT', 'RSR/USDT', 'MATIC/USDT', 'ZEN/USDT', 'GRT/USDT', '1INCH/USDT', 'CHZ/USDT', 'ANKR/USDT', 'LUNA/USDT', 'RVN/USDT', 'XEM/USDT', 'MANA/USDT', 'HBAR/USDT')

symbols = list(tickers)
# 코인별 저장 정보값 초기화
info = {}
for symbol in symbols:
    info[symbol] = {}
    info[symbol]['amount'] = 0 # 코인 매수/매도 갯수
    info[symbol]['position'] = 'wait' # 현재 거래 포지션 (long / short / wait)
    info[symbol]['price'] = 0 # 코인 거래한 가격
    info[symbol]['slow_osc'] = 0 # Stochastic Slow Oscilator 값
    info[symbol]['slow_osc_slope'] = 0 # Stochastic Slow Oscilator 기울기 값
    info[symbol]['slow_k'] = 0 # Stochastic Slow Oscilator 기울기 값
    info[symbol]['macd_osc'] = 0 # Stochastic Slow Oscilator 값
    info[symbol]['ma'] = 0 # 지수이동평균 값

# Stochastic Slow Oscilator 값 계산
def calStochastic(df, n=9, m=5, t=3):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    slow_osc = slow_k - slow_d
    slow_osc_slope = slow_osc - slow_osc.shift(1)
    df['slow_osc'] = slow_osc
    df['slow_osc_slope'] = slow_osc_slope
    df['slow_k'] = slow_k
    return df['slow_osc'][-1], df['slow_osc_slope'][-1], df['slow_k'][-1]

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
    bot.sendMessage(chat_id = chat_id, text="코인별 Stochastic + MACD 수집중...")
    for symbol in symbols:
        # 일봉 데이터 수집
        ohlcv = binance.fetch_ohlcv(symbol, '1d')
        df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)

        # Save Stochastic Oscilator information
        info[symbol]['slow_osc'] = calStochastic(df)[0]
        info[symbol]['slow_osc_slope'] = calStochastic(df)[1]
        info[symbol]['slow_k'] = calStochastic(df)[2]
        info[symbol]['macd_osc'] = calMACD(df)
        print(f"코인: {symbol}")
        print(f"Stochastic OSC: {info[symbol]['slow_osc']}\nStochastic OSC Slope: {info[symbol]['slow_osc_slope']}\nStochastic K: {info[symbol]['slow_k']}\nMACD: {info[symbol]['macd_osc']}\n")
        time.sleep(0.5)
    bot.sendMessage(chat_id = chat_id, text="코인별 Stochastic + MACD 값을 저장했습니다.\n매수/매도 조건을 확인하겠습니다.")

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
        money = round((free_balance * 4 / available_hold - 6), -1)
        return money

total_hold = 0
bot.sendMessage(chat_id = chat_id, text=f"Stochastic + MACD 전략 시작합니다. 화이팅!")
save_info()

while True:
    try:
        now = datetime.datetime.now()
        if (now.hour - 3) % 6 == 0 and now.minute == 0:
            symbols.clear()
            symbols = list(tickers)
            print(f"코인 전체 리스트로 초기화\nList: {symbols}")
            save_info()

            for symbol in symbols:
                current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                free_balance = round(binance.fetch_balance()['USDT']['free'], 2)
                money = adjust_money(free_balance=free_balance, total_hold=total_hold) # 코인별 투자금액

                # 롱 포지션 청산
                if info[symbol]['position'] == 'long':
                    total_hold -= 1
                    info[symbol]['position'] = 'wait'
                    binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=info[symbol]['amount'], params={"reduceOnly": True})
                    profit = round((current_price - info[symbol]['price']) / info[symbol]['price'] * 100, 2) # 수익률 계산
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} (롱)\n매수가: {info[symbol]['price']} -> 매도가: {current_price}\n수익률: {profit}%")
                    print(f"코인: {symbol} (롱) 포지션 청산\n매수가: {info[symbol]['price']} -> 매도가: {current_price}\n수익률: {profit}")

                # 숏 포지션 청산
                elif info[symbol]['position'] == 'short':
                    total_hold -= 1
                    info[symbol]['position'] = 'wait'
                    binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=info[symbol]['amount'], params={"reduceOnly": True})
                    profit = round((info[symbol]['price'] - current_price) / current_price * 100, 2) # 수익률 계산
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} (숏)\n매도가: {info[symbol]['price']} -> 매수가: {current_price}\n수익률: {profit}%")
                    print(f"코인: {symbol} (숏) 포지션 청산\n매도가: {info[symbol]['price']} -> 매수가: {current_price}\n수익률: {profit}")

                # Stochastic + MACD 둘 다 조건 만족시 롱 포지션
                elif total_hold < 5 and info[symbol]['position'] == 'wait' and info[symbol]['slow_osc'] > 0 and info[symbol]['macd_osc'] > 0 and info[symbol]['slow_osc_slope'] > 0 and info[symbol]['slow_k'] < 80:
                    amount = money / current_price # 거래할 코인 갯수
                    binance.create_market_buy_order(symbol=symbol, amount=amount) # 시장가 매수
                    take_profit_params = {'stopPrice': current_price * 1.015}
                    binance.create_order(symbol, 'take_profit_market', 'sell', amount, None, take_profit_params)
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'long' # 포지션 'long' 으로 변경
                    info[symbol]['amount'] = amount # 코인 갯수 저장
                    total_hold += 1
                    bot.sendMessage(chat_id = chat_id, text=f"{symbol} 롱 포지션\n매수가: {current_price}\n투자금액: {money}\n총 보유 코인: {total_hold}")
                    print(f"{symbol} 롱 포지션\n매수가: {current_price}\n투자금액: {money}\n총 보유 코인: {total_hold}")

                # Stochastic + MACD 둘 다 조건 만족시 숏 포지션
                elif total_hold < 5 and info[symbol]['position'] == 'wait' and info[symbol]['slow_osc'] < 0 and info[symbol]['macd_osc'] < 0 and info[symbol]['slow_osc_slope'] < 0 and info[symbol]['slow_k'] > 30:
                    amount = money / current_price # 거래할 코인 갯수
                    binance.create_market_sell_order(symbol=symbol, amount=amount) # 시장가 매도
                    take_profit_params = {'stopPrice': current_price * 0.985}
                    binance.create_order(symbol, 'take_profit_market', 'buy', amount, None, take_profit_params)
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'short' # 포지션 'short' 으로 변경
                    info[symbol]['amount'] = amount # 코인 갯수 저장
                    total_hold += 1
                    bot.sendMessage(chat_id = chat_id, text=f"{symbol} 숏 포지션\n매도가: {current_price}\n투자금액: {money}\n총 보유 코인: {total_hold}")
                    print(f"{symbol} 숏 포지션\n매도가: {current_price}\n투자금액: {money}\n총 보유 코인: {total_hold}")

                time.sleep(0.5)
                print(f"시간: {now} 코인: {symbol}")
                print(f"Stochastic OSC: {info[symbol]['slow_osc']}\nStochastic OSC Slope: {info[symbol]['slow_osc_slope']}\nMACD: {info[symbol]['macd_osc']}\n")
                print(f"포지션 상태: {info[symbol]['position']}\n")
            time.sleep(60)

        # 1시간 마다 stochastic 값 체크하여 손절
        elif now.hour == 0 and now.minute == 0:
            save_info()
            for symbol in symbols:
                current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                free_balance = round(binance.fetch_balance()['USDT']['free'], 2)
                money = adjust_money(free_balance=free_balance, total_hold=total_hold) # 코인별 투자금액

                # 롱 포지션 청산
                if info[symbol]['position'] == 'long':
                    if info[symbol]['slow_osc_slope'] < 0 or info[symbol]['slow_osc'] < 0:
                        total_hold -= 1
                        info[symbol]['position'] = 'wait'
                        binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=info[symbol]['amount'], params={"reduceOnly": True})
                        profit = round((current_price - info[symbol]['price']) / info[symbol]['price'] * 100, 2) # 수익률 계산
                        bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} (롱)\n매수가: {info[symbol]['price']} -> 매도가: {current_price}\n수익률: {profit}%")
                        print(f"코인: {symbol} (롱) 포지션 청산\n매수가: {info[symbol]['price']} -> 매도가: {current_price}\n수익률: {profit}")

                # 숏 포지션 청산
                elif info[symbol]['position'] == 'short':
                    if info[symbol]['slow_osc_slope'] > 0 or info[symbol]['slow_osc'] > 0:
                        total_hold -= 1
                        info[symbol]['position'] = 'wait'
                        binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=info[symbol]['amount'], params={"reduceOnly": True})
                        profit = round((info[symbol]['price'] - current_price) / current_price * 100, 2) # 수익률 계산
                        bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} (숏)\n매도가: {info[symbol]['price']} -> 매수가: {current_price}\n수익률: {profit}%")
                        print(f"코인: {symbol} (숏) 포지션 청산\n매도가: {info[symbol]['price']} -> 매수가: {current_price}\n수익률: {profit}")
            time.sleep(60)

        elif len(symbols) == 0:
            if now.minute == 2:
                time.sleep(3480)

        # 실시간 가격 체크
        else:
            for symbol in symbols:
                current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                profit = 1.5
                if info[symbol]['position'] == 'wait':
                    symbols.remove(symbol)
                    print(f"코인: {symbol} 보유X -> 코인 리스트에서 삭제\nList: {symbols}")

                elif info[symbol]['position'] == 'long' and info[symbol]['price'] * 1.015 < current_price:
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} (롱)\n매수가: {info[symbol]['price']} -> 매도가: {current_price}\n수익률: {profit}%")
                    print(f"코인: {symbol} (롱)\n매수가: {info[symbol]['price']} -> 매도가: {current_price}\n수익률: {profit}")
                    total_hold -= 1
                    info[symbol]['position'] = 'wait'

                elif info[symbol]['position'] == 'short' and info[symbol]['price'] * 0.985 > current_price:
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} (숏)\n매도가: {info[symbol]['price']} -> 매수가: {current_price}\n수익률: {profit}%")
                    print(f"코인: {symbol} (숏)\n매도가: {info[symbol]['price']} -> 매수가: {current_price}\n수익률: {profit}")
                    total_hold -= 1
                    info[symbol]['position'] = 'wait'

                time.sleep(1)
                print(f"시간: {now} 코인: {symbol}")
                print(f"Stochastic OSC: {info[symbol]['slow_osc']}\nStochastic OSC Slope: {info[symbol]['slow_osc_slope']}\nMACD: {info[symbol]['macd_osc']}\n")
                print(f"현재가: {current_price}\n포지션 상태: {info[symbol]['position']}\n")

    except Exception as e:
        bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
