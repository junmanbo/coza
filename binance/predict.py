# Description: Predict the price of ETH

# Import the dependencies
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import ccxt

# Load the data
binance = ccxt.binance()
ticker = "BTC/USDT"
ohlcv = binance.fetch_ohlcv(ticker, '1m')

# Get and Show the data
# Store the data
df = pd.DataFrame(ohlcv, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
df['Date'] = pd.to_datetime(df['Date'], unit='ms')
df.set_index('Date', inplace=True)

# Create a variable for predicting 'n' days out into the future
projection = 1
# Create a new column called projection
df['Prediction'] = df[['Close']].shift(-projection)

# Create the independent data set (X)
X = np.array(df[['Close']])
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
x_projection = np.array(df[['Close']])[-projection:]

# Print the linear regression models predictions for the next 14 days
linReg_prediction = linReg.predict(x_projection)
print(linReg_prediction)

# Show the data set
print(df)
