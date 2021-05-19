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
tickers = ('ADA/USDT', 'DOT/USDT', 'LINK/USDT', 'SOL/USDT')

symbols = list(tickers)
# 코인별 저장 정보값 초기화
info = {}
for symbol in symbols:
    info[symbol] = {}
    info[symbol]['amount'] = 0 # 코인 매수/매도 갯수
    info[symbol]['position'] = 'wait' # 현재 거래 포지션 (long / short / wait)
    info[symbol]['price'] = 0 # 코인 거래한 가격
    info[symbol]['slow_osc'] = 0 # Stochastic Slow Oscilator 값

# Stochastic Slow Oscilator 값 계산
def calStochastic(df, n=9, m=5, t=3):
    ndays_high = df.high.rolling(window=n, min_periods=1).max()
    ndays_low = df.low.rolling(window=n, min_periods=1).min()
    fast_k = ((df.close - ndays_low) / (ndays_high - ndays_low)) * 100
    slow_k = fast_k.ewm(span=m).mean()
    slow_d = slow_k.ewm(span=t).mean()
    df['slow_osc'] = slow_k - slow_d
    return df['slow_osc'][-1]

# 코인별 Stochastic OSC 값 info에 저장
def save_info():
    bot.sendMessage(chat_id = chat_id, text="코인별 Stochastic 수집중...")
    for symbol in symbols:
        # 일봉 데이터 수집
        ohlcv = binance.fetch_ohlcv(symbol, '1d')
        df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)

        # Save Stochastic Oscilator information
        info[symbol]['slow_osc'] = calStochastic(df)
        print(f"코인: {symbol}")
        print(f"Stochastic OSC: {info[symbol]['slow_osc']}\n")
        time.sleep(0.5)
    bot.sendMessage(chat_id = chat_id, text="코인별 Stochastic값을 저장했습니다.\n매수/매도 조건을 확인하겠습니다.")

bot.sendMessage(chat_id = chat_id, text=f"Stochastic 전략 시작합니다. 화이팅!")
save_info()

while True:
    try:
        now = datetime.datetime.now()
        time.sleep(30)
        if now.minute == 0:
            save_info()
            money = binance.fetch_balance()['USDT']['free'] / 4
            for symbol in symbols:
                current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                amount = money / current_price # 거래할 코인 갯수
                # 코인 미보유 시 거래 (롱)
                if info[symbol]['position'] == 'wait' and info[symbol]['slow_osc'] > 0:
                    binance.create_market_buy_order(symbol=symbol, amount=amount) # 시장가 매수
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'long' # 포지션 'long' 으로 변경
                    info[symbol]['amount'] = amount # 코인 갯수 저장
                    bot.sendMessage(chat_id = chat_id, text=f"{symbol} 롱 포지션\n매수가: {current_price}\n투자금액: {money:.2f}")
                    print(f"{symbol} 롱 포지션\n매수가: {current_price}\n투자금액: {money:.2f}")
                # 코인 미보유 시 거래 (숏)
                elif info[symbol]['position'] == 'wait' and info[symbol]['slow_osc'] < 0:
                    binance.create_market_sell_order(symbol=symbol, amount=amount) # 시장가 매도
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'short' # 포지션 'short' 으로 변경
                    info[symbol]['amount'] = amount # 코인 갯수 저장
                    bot.sendMessage(chat_id = chat_id, text=f"{symbol} 숏 포지션\n매도가: {current_price}\n투자금액: {money:.2f}")
                    print(f"{symbol} 숏 포지션\n매도가: {current_price}\n투자금액: {money:.2f}")
                # 코인 보유시 거래 (롱 -> 숏)
                elif info[symbol]['position'] == 'long' and info[symbol]['slow_osc'] < 0:
                    # 현재 포지션 청산
                    binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=info[symbol]['amount'], params={"reduceOnly": True})
                    profit = (current_price - info[symbol]['price']) / info[symbol]['price'] * 100  # 수익률 계산
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} (롱)\n매수가: {info[symbol]['price']} -> 매도가: {current_price}\n수익률: {profit:.2f}%")
                    print(f"코인: {symbol} (롱)\n매수가: {info[symbol]['price']} -> 매도가: {current_price}\n수익률: {profit:.2f}%")
                    time.sleep(1)
                    # 포지션 변경
                    binance.create_market_sell_order(symbol=symbol, amount=amount) # 시장가 매도
                    info[symbol]['price'] = current_price
                    info[symbol]['amount'] = amount # 코인 갯수 저장
                    bot.sendMessage(chat_id = chat_id, text=f"{symbol} 숏 포지션\n매도가: {current_price}\n투자금액: {money:.2f}")
                    print(f"{symbol} 숏 포지션\n매도가: {current_price}\n투자금액: {money}")
                # 코인 보유시 거래 (숏 -> 롱)
                elif info[symbol]['position'] == 'short' and info[symbol]['slow_osc'] > 0:
                    # 현재 포지션 청산
                    binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=info[symbol]['amount'], params={"reduceOnly": True})
                    profit = (info[symbol]['price'] - current_price) / current_price * 100  # 수익률 계산
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {symbol} (숏)\n매도가: {info[symbol]['price']} -> 매수가: {current_price}\n수익률: {profit:.2f}%")
                    print(f"코인: {symbol} (숏)\n매도가: {info[symbol]['price']} -> 매수가: {current_price}\n수익률: {profit:.2f}%")
                    time.sleep(1)
                    # 포지션 변경
                    binance.create_market_buy_order(symbol=symbol, amount=amount) # 시장가 매수
                    info[symbol]['price'] = current_price
                    info[symbol]['amount'] = amount # 코인 갯수 저장
                    bot.sendMessage(chat_id = chat_id, text=f"{symbol} 롱 포지션\n매수가: {current_price}\n투자금액: {money:.2f}")
                    print(f"{symbol} 롱 포지션\n매수가: {current_price}\n투자금액: {money:.2f}")

                time.sleep(0.5)
                print(f"시간: {now} 코인: {symbol}")
                print(f"Stochastic OSC: {info[symbol]['slow_osc']}")
                print(f"포지션 상태: {info[symbol]['position']}\n")

    except Exception as e:
        bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
