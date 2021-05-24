#!/usr/bin/env python

import ccxt
import pandas as pd
import datetime
import time
import telegram
import json
import logging

logging.basicConfig(filename='/home/cocojun/logs/stoch_short.log', format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

# telegram setting
with open("/home/cocojun/coza/binance/mybot.txt") as f:
    lines = f.readlines()
    my_token = lines[0].strip()
    chat_id = lines[1].strip()
bot = telegram.Bot(token = my_token)


# 거래소 설정
# 파일로부터 apiKey, Secret 읽기
with open("/home/cocojun/coza/binance/binance.txt") as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret = lines[1].strip()

# Coin정보 저장 파일 불러오기
with open('/home/cocojun/coza/binance/Stoch_short/info.txt', 'r') as f:
    data = f.read()
    info = json.loads(data)

binance = ccxt.binance({
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    }
})

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

# Coin별 Stochastic OSC 값 info에 저장
def save_info():
    logging.info('Collecting information of Cryptocurrencies')
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

        logging.info(f"Coin: {symbol}\n\
            Stochastic OSC (Day): {info[symbol]['slow_osc_d']}\n\
            Stochastic OSC Slope (Day): {info[symbol]['slow_osc_slope_d']}\n\
            Stochastic OSC (Hour): {info[symbol]['slow_osc_h']}\n\
            Stochastic OSC Slope (Hour): {info[symbol]['slow_osc_slope_h']}\n\
            MACD: {info[symbol]['macd_osc']}\n\
            EMA: {info[symbol]['ma']}\n\
            OPEN: {info[symbol]['open_d']}\n")
        time.sleep(0.1)
    logging.info('Finished collecting')

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

# InvestmentAmount 조정
def adjust_money(free_balance, total_hold):
    if total_hold < total_investment:
        available_hold = total_investment - total_hold
        money = round((free_balance * 4 / available_hold - 10), 0)
        return money

# Coin 목록 불러오기
tickers = binance.load_markets().keys()
symbols = list(tickers)

time.sleep(1)
start_balance = binance.fetch_balance()['USDT']['total']

total_hold = 0
for symbol in symbols:
    if info[symbol]['position'] != 'wait':
        total_hold += 1 # 투자한 Coin 갯수

total_investment = 5 # 투자할 Coin 갯수
bull_profit = 1.017 # Long Position Profit
bear_profit = 0.983 # Short Position Profit

# 거래에서 제외하고 싶은 Coin
except_coin = ['BTC/USDT', 'ETH/USDT']
for coin in except_coin:
    symbols.remove(coin)

check = True # 익절 / 청산 체크 확인
time.sleep(1)
save_info() # 분석 정보 저장

bot.sendMessage(chat_id = chat_id, text=f"Stochastic (Short-term) 전략 시작합니다. 시작 금액: {start_balance:.2f}")
logging.info(f"Start Strategy of Stochastic (Short-term). Strat Balance: {start_balance:.2f}\n\
        The number of current Holding Coin: {total_hold}\nThe number of Investing Coin: {total_investment-total_hold}\n\
        Target profit per a trading: {(bull_profit-1)*100:.2f}%")

while True:
    now = datetime.datetime.now()
    time.sleep(1)
    if (now.hour + 3) % 4 == 0 and now.minute == 0 and 0 <= now.second <= 9: # 4시간 마다 (1, 5, 9, 13, 17, 21) 체크
        save_info() # 분석 정보 저장
        logging.info('Checking Stop Profit or Stop Loss')
        for symbol in symbols:
            try:
                current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                # 익절한 Coin 체크
                if info[symbol]['position'] == 'long' and info[symbol]['high_h'] > info[symbol]['price'] * bull_profit:
                    total_hold -= 1
                    info[symbol]['position'] = 'wait'
                    profit = (bull_profit - 1) * 100
                    bot.sendMessage(chat_id = chat_id, text=f"(Short-term){symbol} (Long)\n\
                            Buying: {info[symbol]['price']} -> Selling: {info[symbol]['price']*bull_profit}\nProfit: {profit:.2f}%")
                    logging.info(f"Coin: {symbol} (Long) Position\nBuying: {info[symbol]['price']} -> Selling: {info[symbol]['price']*bull_profit}\nProfit: {profit:.2f}")

                elif info[symbol]['position'] == 'short' and info[symbol]['low_h'] < info[symbol]['price'] * bear_profit:
                    total_hold -= 1
                    info[symbol]['position'] = 'wait'
                    profit = (1 - bear_profit) * 100
                    bot.sendMessage(chat_id = chat_id, text=f"(Short-term){symbol} (Short)\n\
                            Selling: {info[symbol]['price']} -> Buying: {info[symbol]['price']*bear_profit}\nProfit: {profit:.2f}%")
                    logging.info(f"Coin: {symbol} (Short) Position\nSelling: {info[symbol]['price']} -> Buying: {info[symbol]['price']*bear_profit}\nProfit: {profit:.2f}")

                # Long Position 청산
                elif info[symbol]['position'] == 'long':
                    if info[symbol]['slow_osc_h'] < 0 or info[symbol]['slow_osc_slope_h'] < 0:
                        total_hold -= 1
                        info[symbol]['position'] = 'wait'
                        binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=info[symbol]['amount'], params={"reduceOnly": True})
                        profit = (current_price - info[symbol]['price']) / info[symbol]['price'] * 100 # Profit 계산
                        bot.sendMessage(chat_id = chat_id, text=f"(Short-term){symbol} (Long)\n\
                                Buying: {info[symbol]['price']} -> Selling: {current_price}\nProfit: {profit:.2f}%")
                        logging.info(f"Coin: {symbol} (Long) Position Loss\nBuying: {info[symbol]['price']} -> Selling: {current_price}\nProfit: {profit:.2f}")

                # Short Position 청산
                elif info[symbol]['position'] == 'short':
                    if info[symbol]['slow_osc_h'] > 0 or info[symbol]['slow_osc_slope_h'] > 0:
                        total_hold -= 1
                        info[symbol]['position'] = 'wait'
                        binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=info[symbol]['amount'], params={"reduceOnly": True})
                        profit = (info[symbol]['price'] - current_price) / current_price * 100 # Profit 계산
                        bot.sendMessage(chat_id = chat_id, text=f"(Short-term){symbol} (Short)\n\
                                Selling: {info[symbol]['price']} -> Buying: {current_price}\nProfit: {profit:.2f}%")
                        logging.info(f"Coin: {symbol} (Short) Position Loss\nSelling: {info[symbol]['price']} -> Buying: {current_price}\nProfit: {profit:.2f}")
                time.sleep(0.1)
            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"Occured error {e}")
                logging.error(f"Occured error {e}")
        check = True
        with open('/home/cocojun/coza/binance/Stoch_short/info.txt', 'w') as f:
            f.write(json.dumps(info)) # use `json.loads` to do the reverse

    elif check == True: # 익절 / 청산 체크 끝나면 거래 진행
        free_balance = binance.fetch_balance()['USDT']['free']
        money = adjust_money(free_balance, total_hold)
        logging.info('Finished Checking and Start Trading.')
        for symbol in symbols:
            try:
                current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                # 조건 만족시 Long Position
                if total_hold < total_investment and info[symbol]['position'] == 'wait' and \
                        info[symbol]['slow_osc_d'] > 0 and info[symbol]['slow_osc_slope_d'] > 0 and \
                        info[symbol]['macd_osc'] > 0 and info[symbol]['open_d'] > info[symbol]['ma'] and \
                        info[symbol]['slow_osc_h'] > 0 and info[symbol]['slow_osc_slope_h'] > 0:
                    amount = money / current_price # 거래할 Coin 갯수
                    binance.create_market_buy_order(symbol=symbol, amount=amount) # 시장가 매수
                    take_profit_params = {'stopPrice': current_price * bull_profit}
                    binance.create_order(symbol, 'take_profit_market', 'sell', amount, None, take_profit_params)
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'long' # Position 'long' 으로 변경
                    info[symbol]['amount'] = amount # Coin 갯수 저장
                    total_hold += 1
                    bot.sendMessage(chat_id = chat_id, text=f"(Short-term){symbol} Long Position\n\
                            Buying: {current_price}\nInvestment Amount: {money:.2f}\nTotal holding: {total_hold}")
                    logging.info(f"{symbol} Long Position\nBuying: {current_price}\nInvestment Amount: {money:.2f}\nTotal holding: {total_hold}")

                # Stochastic + MACD 둘 다 조건 만족시 Short Position
                elif total_hold < total_investment and info[symbol]['position'] == 'wait' and \
                        info[symbol]['slow_osc_d'] < 0 and info[symbol]['slow_osc_slope_d'] < 0 and \
                        info[symbol]['macd_osc'] < 0 and info[symbol]['open_d'] < info[symbol]['ma'] and \
                        info[symbol]['slow_osc_h'] < 0 and info[symbol]['slow_osc_slope_h'] < 0:
                    amount = money / current_price # 거래할 Coin 갯수
                    binance.create_market_sell_order(symbol=symbol, amount=amount) # 시장가 매도
                    take_profit_params = {'stopPrice': current_price * bear_profit}
                    binance.create_order(symbol, 'take_profit_market', 'buy', amount, None, take_profit_params)
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'short' # Position 'short' 으로 변경
                    info[symbol]['amount'] = amount # Coin 갯수 저장
                    total_hold += 1
                    bot.sendMessage(chat_id = chat_id, text=f"(Short-term){symbol} Short Position\n\
                            Selling: {current_price}\nInvestment Amount: {money:.2f}\nTotal holding: {total_hold}")
                    logging.info(f"{symbol} Short Position\nSelling: {current_price}\nInvestment Amount: {money:.2f}\nTotal holding: {total_hold}")
                time.sleep(0.1)
            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"Occured error {e}")
                logging.info(f"Occured error {e}")
        check = False
        with open('/home/cocojun/coza/binance/Stoch_short/info.txt', 'w') as f:
            f.write(json.dumps(info)) # use `json.loads` to do the reverse
        logging.info(f"Finished Trading")
