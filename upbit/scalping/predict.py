import numpy as np
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime
import calendar, requests
import pandas as pd
import pyupbit

symbol = 'KRW-TRX'
now = datetime.now()
print(now, symbol, "Current Price:", pyupbit.get_current_price(symbol))


unixtime = calendar.timegm(now.utctimetuple())

since = unixtime - 60 * 60 * 10000

param = {"period": 60, "from": since, "to": unixtime}

url = "https://api.upbit.com/v1/candles/minutes/15"
querystring = {"market":symbol,"count":"500"}
response = requests.request("GET", url, params=querystring)
data = response.json()
#df = pd.DataFrame(data)
#df=df.reindex(index=df.index[::-1]).reset_index()

#urlcheck = "https://www.bitmex.com/api/udf/history?symbol=" + symbol + "&resolution={period}&from={from}&to={to}"
#url = urlcheck.format(**param)
#res = requests.get(url)
#data = res.json()

#
df = pd.DataFrame({
    "timestamp": data["t"],
    "open": data["o"],
    "high": data["h"],
    "low": data["l"],
    "close": data["c"],
    "volume": data["v"],
}, columns=["timestamp", "open", "high", "low", "close", "volume"])

df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")

df = df.set_index("datetime")

df['target'] = df['close'].shift(-1)

df = df.reset_index()

X = df.drop(['target', 'timestamp', 'datetime'], axis=1).reset_index(drop=True)

Y = df['target'].reset_index(drop=True)

h = 1

b = []
for h in range(0, h):
    b.append(h)

u = len(df) - h - 1

for i in range(0, 1):
    trainstart = 0
    trainend = u + i
    teststart = u + i
    testend = teststart + 1

    X_train = X[trainstart:trainend]
    y_train = Y[trainstart:trainend]
    X_test = X[teststart:testend]
    y_test = Y[teststart:testend]

    k = i
    rs = 0

    n_samples = trainend + 1
    n_splits = 10
    n_folds = n_splits + 1
    indices = np.arange(n_samples)
    test_size = (n_samples // n_folds)
    test_starts = range(test_size + n_samples % n_folds, n_samples, test_size)

    tscv = [(np.arange(0, j + test_size - 2, 1), np.arange(j + test_size - 2, j + test_size - 1, 1)) for j in
            range(test_size + n_samples % n_folds, n_samples, test_size)]

    parameters_rf = {'n_estimators': (1,5,10), 'max_depth': (1, 5, 10, 15)}

    grid_search_rf = GridSearchCV(estimator=RandomForestRegressor(random_state=rs), param_grid=parameters_rf, cv=tscv,
                                  scoring='neg_mean_squared_error')
    grid_search_rf.fit(X_train, y_train)
    rf_para = str(grid_search_rf.best_params_)

    max_depth_rf = float(rf_para.split("{'max_depth': ", 1)[1].split(",", 1)[0])
    n_estimators_rf = int(rf_para.split("n_estimators': ", 1)[1].split("}", 1)[0])

    RF = RandomForestRegressor(n_estimators=n_estimators_rf, max_depth=max_depth_rf, random_state=rs)
    RF.fit(X_train, y_train)

    print('1 Hour Forecasted Price ', RF.predict(X_test))
