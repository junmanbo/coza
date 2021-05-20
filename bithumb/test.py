from pybithumb import Bithumb
tickers = ['BTC', 'ETH', 'LTC', 'ETC', 'XRP', 'BCH', 'QTUM', 'BTG', 'EOS', 'ICX', 'TRX', 'ELF', 'OMG', 'KNC', 'GLM', 'ZIL', 'WAXP', 'POWR', 'LRC', 'STEEM', 'STRAX', 'AE', 'ZRX', 'REP', 'XEM', 'SNT', 'ADA', 'CTXC', 'BAT', 'WTC', 'THETA', 'LOOM', 'WAVES', 'TRUE', 'LINK', 'RNT', 'ENJ', 'VET', 'MTL', 'IOST', 'TMTG', 'QKC', 'HDAC', 'AMO', 'BSV', 'DAC', 'ORBS', 'TFUEL', 'VALOR', 'CON', 'ANKR', 'MIX', 'LAMB', 'CRO', 'FX', 'CHR', 'MBL', 'MXC', 'DVP', 'FCT', 'FNB', 'TRV', 'PCM', 'DAD', 'AOA', 'XSR', 'WOM', 'SOC', 'EM', 'QBZ', 'BOA', 'FLETA', 'SXP', 'COS', 'APIX', 'EL', 'BASIC', 'HIVE', 'XPR', 'FIT']
print(len(tickers))
df = Bithumb.get_candlestick("BTC", chart_intervals="1h")
print(df)
