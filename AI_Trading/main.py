import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import datetime
import time
import telegram
import ccxt

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

tickers = ['LINK/USDT', 'ADA/USDT']

info = {}
for ticker in tickers:
    info[ticker] = {}
    info[ticker]['amount'] = 0 # 코인 매수/매도 갯수
    info[ticker]['position'] = 'wait' # 현재 거래 포지션 (long / short / wait)
    info[ticker]['price'] = 0 # 코인 거래한 가격
    info[ticker]['trade_signal'] = None # 거래 신호 (buy or sell)
    info[ticker]['linReg_confidence'] = 0

def calPrice(ticker):
    ohlcv = binance.fetch_ohlcv(ticker, '1d')
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)

    projection = 1
    df['Prediction'] = df[['close']].shift(-projection)

    X = np.array(df[['close']])
    X = X[:-projection]

    y = df['Prediction'].values
    y = y[:-projection]

    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=.15)
    linReg = LinearRegression()
    linReg.fit(x_train, y_train)

    linReg_confidence = linReg.score(x_test, y_test)
    info[ticker]['linReg_confidence'] = linReg_confidence
    print('Linear Regression Confidence:', linReg_confidence)
    x_projection = np.array(df[['close']])[-projection:]
    linReg_prediction = linReg.predict(x_projection)
    print(linReg_prediction)
    print(df)

    if linReg_prediction > df['close'][-1]:
        print("Buy")
        info[ticker]['trade_signal'] = True
    elif linReg_prediction < df['close'][-1]:
        print("Sell")
        info[ticker]['trade_signal'] = False

def savePrice(ticker):
    while True:
        calPrice(ticker)
        if info[ticker]['linReg_confidence'] > 0.975:
            break

bot.sendMessage(chat_id = chat_id, text=f"AI 전략 시작합니다. 화이팅!")

while True:
    try:
        now = datetime.datetime.now()
        if now.minute % 30 == 0:
            money = round(binance.fetch_balance()['USDT']['free'] / 4, 0)
            for ticker in tickers:
                savePrice(ticker)
                current_price = binance.fetch_ticker(symbol=ticker)['close'] # 현재가 조회
                amount = money / current_price # 거래할 코인 갯수
                if info[ticker]['position'] == 'wait' and info[ticker]['trade_signal'] == True:
                    binance.create_market_buy_order(symbol=ticker, amount=amount) # 시장가 매수
                    info[ticker]['price'] = current_price
                    info[ticker]['position'] == 'long'
                    info[ticker]['amount'] = amount # 코인 갯수 저장
                    print(f"{ticker}를 매수했습니다!\n")
                    bot.sendMessage(chat_id = chat_id, text=f"{ticker} 롱 포지션\n매수가: {current_price}\n투자금액: {money}")

                elif info[ticker]['position'] == 'wait' and info[ticker]['trade_signal'] == False:
                    binance.create_market_sell_order(symbol=ticker, amount=amount) # 시장가 매도
                    info[ticker]['price'] = current_price
                    info[ticker]['position'] == 'short'
                    info[ticker]['amount'] = amount # 코인 갯수 저장
                    print(f"{ticker}를 매도했습니다!\n")
                    bot.sendMessage(chat_id = chat_id, text=f"{ticker} 숏 포지션\n매도가: {current_price}\n투자금액: {money}")

                elif info[ticker]['position'] == 'long' and info[ticker]['trade_signal'] == False:
                    binance.create_order(symbol=ticker, type="MARKET", side="sell", amount=info[ticker]['amount'], params={"reduceOnly": True})
                    profit = (current_price - info[ticker]['price']) / info[ticker]['price'] * 100 # 수익률 계산
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {ticker} (롱)\n매수가: {info[ticker]['price']} -> 매도가: {current_price}\n수익률: {profit:.2f}%")
                    print(f"코인: {ticker} (롱) 포지션 청산\n매수가: {info[ticker]['price']} -> 매도가: {current_price}\n수익률: {profit}")
                    time.sleep(1)
                    binance.create_market_sell_order(symbol=ticker, amount=amount) # 시장가 매도
                    info[ticker]['price'] = current_price
                    info[ticker]['position'] == 'short'
                    info[ticker]['amount'] = amount # 코인 갯수 저장
                    print(f"{ticker}를 매도했습니다!\n")
                    bot.sendMessage(chat_id = chat_id, text=f"{ticker} 숏 포지션\n매도가: {current_price}\n투자금액: {money}")

                elif info[ticker]['position'] == 'short' and info[ticker]['trade_signal'] == True:
                    binance.create_order(symbol=ticker, type="MARKET", side="buy", amount=info[ticker]['amount'], params={"reduceOnly": True})
                    profit = (info[ticker]['price'] - current_price) / current_price * 100 # 수익률 계산
                    bot.sendMessage(chat_id = chat_id, text=f"코인: {ticker} (숏)\n매도가: {info[ticker]['price']} -> 매수가: {current_price}\n수익률: {profit:.2f}%")
                    print(f"코인: {ticker} (숏) 포지션 청산\n매도가: {info[ticker]['price']} -> 매수가: {current_price}\n수익률: {profit}")
                    time.sleep(1)
                    binance.create_market_buy_order(symbol=ticker, amount=amount) # 시장가 매수
                    info[ticker]['price'] = current_price
                    info[ticker]['position'] == 'long'
                    info[ticker]['amount'] = amount # 코인 갯수 저장
                    print(f"{ticker}를 매수했습니다!\n")
                    bot.sendMessage(chat_id = chat_id, text=f"{ticker} 롱 포지션\n매수가: {current_price}\n투자금액: {money}")
        time.sleep(30)
    except Exception as e:
        bot.sendMessage(chat_id = chat_id, text=f"Error!!\n{e}")
