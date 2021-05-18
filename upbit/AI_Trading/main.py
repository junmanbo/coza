import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import pyupbit
import datetime
import time
import telegram

# telegram setting
my_token = '1725701346:AAFoCMr7xeQwjaqvBsOPoIS99PyRFwVFK_E'
bot = telegram.Bot(token = my_token)
chat_id = '1459236537'

def calPrice(df):
# Create a variable for predicting 'n' days out into the future
    projection = 1
# Create a new column called projection
    df['Prediction'] = df[['close']].shift(-projection)

# Create the independent data set (X)
    X = np.array(df[['close']])
# Remove the last 14 rows
    X = X[:-projection]

# Create the dependent data set (y)
    y = df['Prediction'].values
    y = y[:-projection]

# Split the data into 85% training and 15% testing data sets
    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=.15)

# Create and train the model
    linReg = LinearRegression()
# Train the model
    linReg.fit(x_train, y_train)

# Test the model using score
    linReg_confidence = linReg.score(x_test, y_test)
    print('Linear Regression Confidence:', linReg_confidence)

# Create a variable called x_projection and set it equal to the last 14 rows of data from the original data set
    x_projection = np.array(df[['close']])[-projection:]

# Print the linear regression models predictions for the next 14 days
    linReg_prediction = linReg.predict(x_projection)
    print(linReg_prediction)

# Show the data set
    print(df)

    if linReg_prediction > df['close'][-1]:
        print("Buy")
        trade = True
    elif linReg_prediction < df['close'][-1]:
        print("Sell")
        trade = False

    return linReg_confidence

# 원화 마켓 주문 가격 단위
def price_unit(price):
    if price < 10:
        price = round(price, 2)
    elif 10 <= price < 100:
        price = round(price, 1)
    elif 100 <= price < 1000:
        price = round(price)
    elif 1000 <= price < 100000:
        price = round(price, -1)
    elif 100000 <= price < 1000000:
        price = round(price, -2)
    elif price >= 1000000:
        price = round(price, -3)
    return price

# 객체 생성
f = open("upbit.txt")
lines = f.readlines()
access = lines[0].strip()
secret = lines[1].strip()
f.close()
upbit = pyupbit.Upbit(access, secret)

ticker = "KRW-BTC"
trade = False
hold = False
start_price = 0
end_price = 0
profit = 0

while True:
    try:
        now = datetime.datetime.now()
        if now.minute % 15 == 0:
            df = pyupbit.get_ohlcv(ticker=ticker, interval="minute15", count=200)

            while True:
                if calPrice(df=df) > 0.98:
                    break

            if hold == False and trade == True:
                upbit.buy_market_order(ticker=ticker, price=50000)
                start_price = pyupbit.get_current_price(ticker)  # 코인 현재가
                hold = True
                print(f"{ticker}를 매수했습니다!\n")
                bot.sendMessage(chat_id = chat_id, text=f"코인: {ticker} 매수했습니다.")

            elif hold == True and trade == False:
                coin_balance = upbit.get_balance(ticker)  # 코인 잔고
                upbit.sell_market_order(ticker=ticker, volume=coin_balance)
                end_price = pyupbit.get_current_price(ticker)  # 코인 현재가
                profit = (end_price - start_price) / start_price * 100
                hold = False
                print(f"{ticker}를 매도했습니다!\n수익률: {profit}\n\n")
                bot.sendMessage(chat_id = chat_id, text=f"코인: {ticker} 매도했습니다.\n수익률: {profit}")
            time.sleep(60)
    except Exception as e:
        bot.sendMessage(chat_id = chat_id, text=f"Error!!\n{e}")
