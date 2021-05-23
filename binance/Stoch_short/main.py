import sys
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
        info[symbol]['high_h'] = df_h['high'][-2]
        info[symbol]['low_h'] = df_h['low'][-2]

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
    if total_hold < total_investment:
        available_hold = total_investment - total_hold
        money = round((free_balance * 4 / available_hold - 10), 0)
        return money

start_balance = binance.fetch_balance()['USDT']['total'] # 하루 시작 금액
end_balance = binance.fetch_balance()['USDT']['total'] # 하루 종료 금액

total_hold = 0 # 투자한 코인 갯수
total_investment = 5 # 투자할 코인 갯수
bull_profit = 1.017 # 롱 포지션 수익률
bear_profit = 0.983 # 숏 포지션 수익률

# 거래에서 제외하고 싶은 코인
#  except_coin = ['BAKE/USDT', 'ICP/USDT', '1000SHIB/USDT', 'DGB/USDT', 'BTCST/USDT']
#  for coin in except_coin:
#      symbols.remove(coin)

bot.sendMessage(chat_id = chat_id, text=f"Stochastic (단타) 전략 시작합니다. 시작 금액: {start_balance:.2f}")
print("Stochastic (단타) 전략 시작합니다. 화이팅!")

while True:
    now = datetime.datetime.now()
    time.sleep(1)
    if (now.hour + 3) % 4 == 0 and now.minute == 0 and 0 <= now.second <= 9: # 4시간 마다 (1, 5, 9, 13, 17, 21) 체크
        save_info() # 분석 정보 저장
        for symbol in symbols:
            try:
                current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                # 익절한 코인 체크
                if info[symbol]['position'] == 'long' and info[symbol]['high_h'] > info[symbol]['price'] * bull_profit:
                    total_hold -= 1
                    info[symbol]['position'] = 'wait'
                    profit = (bull_profit - 1) * 100
                    bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} (롱)\n매수가: {info[symbol]['price']} -> 매도가: {info[symbol]['price']*bull_profit}\n수익률: {profit}%")
                    print(f"코인: {symbol} (롱) 포지션\n매수가: {info[symbol]['price']} -> 매도가: {info[symbol]['price']*bull_profit}\n수익률: {profit}")

                elif info[symbol]['position'] == 'short' and info[symbol]['low_h'] < info[symbol]['price'] * bear_profit:
                    total_hold -= 1
                    info[symbol]['position'] = 'wait'
                    profit = (1 - bear_profit) * 100
                    bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} (숏)\n매도가: {info[symbol]['price']} -> 매수가: {info[symbol]['price']*bear_profit}\n수익률: {profit}%")
                    print(f"코인: {symbol} (숏) 포지션\n매도가: {info[symbol]['price']} -> 매도가: {info[symbol]['price']*bear_profit}\n수익률: {profit}")

                # 롱 포지션 청산
                elif info[symbol]['position'] == 'long':
                    if info[symbol]['slow_osc_h'] < 0 or info[symbol]['slow_osc_slope_h'] < 0:
                        total_hold -= 1
                        info[symbol]['position'] = 'wait'
                        binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=info[symbol]['amount'], params={"reduceOnly": True})
                        profit = (current_price - info[symbol]['price']) / info[symbol]['price'] * 100 # 수익률 계산
                        bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} (롱)\n매수가: {info[symbol]['price']} -> 매도가: {current_price}\n수익률: {profit:.2f}%")
                        print(f"코인: {symbol} (롱) 포지션 청산\n매수가: {info[symbol]['price']} -> 매도가: {current_price}\n수익률: {profit:.2f}")

                # 숏 포지션 청산
                elif info[symbol]['position'] == 'short':
                    if info[symbol]['slow_osc_h'] > 0 or info[symbol]['slow_osc_slope_h'] > 0:
                        total_hold -= 1
                        info[symbol]['position'] = 'wait'
                        binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=info[symbol]['amount'], params={"reduceOnly": True})
                        profit = (info[symbol]['price'] - current_price) / current_price * 100 # 수익률 계산
                        bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} (숏)\n매도가: {info[symbol]['price']} -> 매수가: {current_price}\n수익률: {profit:.2f}%")
                        print(f"코인: {symbol} (숏) 포지션 청산\n매도가: {info[symbol]['price']} -> 매수가: {current_price}\n수익률: {profit:.2f}")
                time.sleep(0.1)
            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
        if now.hour == 9:
            end_balance = binance.fetch_balance()['USDT']['total'] # 하루 종료 금액
            profit = (end_balance - start_balance) / start_balance * 100
            bot.sendMessage(chat_id = chat_id, text=f"Stochastic (단타) 전략 종료합니다.\n시작 금액: {start_balance:.2f} -> 종료 금액: {end_balance:.2f}\n수익률: {profit:.2f}%")
            sys.exit(f"{now} 9시에 정산을 마쳤습니다. 종료 후 재시작하겠습니다.")

    elif (now.hour + 3) % 4 == 0 and now.minute == 1 and 0 <= now.second <= 9: # 4시간 마다 (1, 5, 9, 13, 17, 21) 체크
        save_info() # 분석 정보 저장
        free_balance = binance.fetch_balance()['USDT']['free']
        money = adjust_money(free_balance, total_hold)
        for symbol in symbols:
            try:
                current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                # 조건 만족시 롱 포지션
                if total_hold < total_investment and info[symbol]['position'] == 'wait' and \
                        info[symbol]['slow_osc_d'] > 0 and info[symbol]['slow_osc_slope_d'] > 0 and \
                        info[symbol]['macd_osc'] > 0 and info[symbol]['open_d'] > info[symbol]['ma'] and \
                        info[symbol]['slow_osc_h'] > 0 and info[symbol]['slow_osc_slope_h'] > 0:
                    amount = money / current_price # 거래할 코인 갯수
                    binance.create_market_buy_order(symbol=symbol, amount=amount) # 시장가 매수
                    take_profit_params = {'stopPrice': current_price * bull_profit}
                    binance.create_order(symbol, 'take_profit_market', 'sell', amount, None, take_profit_params)
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'long' # 포지션 'long' 으로 변경
                    info[symbol]['amount'] = amount # 코인 갯수 저장
                    total_hold += 1
                    bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} 롱 포지션\n매수가: {current_price}\n투자금액: {money:.2f}\n총 보유 코인: {total_hold}")
                    print(f"{symbol} 롱 포지션\n매수가: {current_price}\n투자금액: {money:.2f}\n총 보유 코인: {total_hold}")

                # Stochastic + MACD 둘 다 조건 만족시 숏 포지션
                elif total_hold < total_investment and info[symbol]['position'] == 'wait' and \
                        info[symbol]['slow_osc_d'] < 0 and info[symbol]['slow_osc_slope_d'] < 0 and \
                        info[symbol]['macd_osc'] < 0 and info[symbol]['open_d'] < info[symbol]['ma'] and \
                        info[symbol]['slow_osc_h'] < 0 and info[symbol]['slow_osc_slope_h'] < 0:
                    amount = money / current_price # 거래할 코인 갯수
                    binance.create_market_sell_order(symbol=symbol, amount=amount) # 시장가 매도
                    take_profit_params = {'stopPrice': current_price * bear_profit}
                    binance.create_order(symbol, 'take_profit_market', 'buy', amount, None, take_profit_params)
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'short' # 포지션 'short' 으로 변경
                    info[symbol]['amount'] = amount # 코인 갯수 저장
                    total_hold += 1
                    bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} 숏 포지션\n매도가: {current_price}\n투자금액: {money:.2f}\n총 보유 코인: {total_hold}")
                    print(f"{symbol} 숏 포지션\n매도가: {current_price}\n투자금액: {money:.2f}\n총 보유 코인: {total_hold}")
                time.sleep(0.1)
            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
