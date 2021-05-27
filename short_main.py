#!/usr/bin/env python

import ccxt
import datetime
import time
import telegram
import json
import logging
from myPackage import indicators as indi

# 로깅 설정
logging.basicConfig(filename='./Log/binance_short.log', format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.WARNING)

# telegram 설정
with open('./Api/mybot.txt') as f:
    lines = f.readlines()
    my_token = lines[0].strip()
    chat_id = lines[1].strip()
bot = telegram.Bot(token = my_token)

# 거래소 설정
with open('./Api/binance.txt') as f:
    lines = f.readlines()
    api_key = lines[0].strip()
    secret = lines[1].strip()

# 기본 옵션: 선물
binance = ccxt.binance({
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    }
})

# 코인 정보 저장 파일 불러오기
with open('./Data/binance_short.txt', 'r') as f:
    data = f.read()
    info = json.loads(data)

# 코인별 정보값 info 딕셔너리에 저장
def save_info(symbol):
    # 일봉 데이터 수집
    df = indi.getOHLCV(binance, symbol, '1d')
    info[symbol]['stoch_osc_d'] = indi.calStochastic(df, 12, 5, 5)[0]
    info[symbol]['stoch_slope_d'] = indi.calStochastic(df, 12, 5, 5)[1]
    info[symbol]['macd_osc'] = indi.calMACD(df, 12, 26, 9)
    info[symbol]['ema'] = indi.calEMA(df, 14)
    info[symbol]['rsi'] = indi.calRSI(df, 14)
    info[symbol]['close'] = df['close'][-1]

    # 4시봉 데이터 수집
    df = indi.getOHLCV(binance, symbol, '4h')
    info[symbol]['stoch_slope_4h'] = indi.calStochastic(df, 12, 5, 5)[1]

    # 1시봉 데이터 수집
    df = indi.getOHLCV(binance, symbol, '1h')
    info[symbol]['stoch_slope_1h'] = indi.calStochastic(df, 12, 5, 5)[1]
    info[symbol]['high'] = df['high'][-1]
    info[symbol]['low'] = df['low'][-1]

strategy = 'Short-term'
# Coin 목록 불러오기
#  tickers = binance.load_markets().keys() # 목록 전체 조회
tickers = (
        'BCH/USDT', 'XRP/USDT', 'EOS/USDT', 'LTC/USDT', 'TRX/USDT',
        'ETC/USDT', 'LINK/USDT', 'XLM/USDT', 'ICP/USDT', 'BAKE/USDT',
        'ADA/USDT', 'XMR/USDT', 'DASH/USDT', 'ZEC/USDT', 'XTZ/USDT',
        'BNB/USDT', 'ATOM/USDT', 'ONT/USDT', 'BAT/USDT', 'VET/USDT',
        'NEO/USDT', 'QTUM/USDT', 'THETA/USDT', 'ALGO/USDT', 'ZIL/USDT',
        'ZRX/USDT', 'OMG/USDT', 'WAVES/USDT', 'MKR/USDT', 'SNX/USDT',
        'DOT/USDT', 'YFI/USDT', 'RUNE/USDT', 'SUSHI/USDT', 'EGLD/USDT',
        'SOL/USDT', 'ICX/USDT', 'UNI/USDT', 'AVAX/USDT', 'FTM/USDT',
        'HNT/USDT', 'ENJ/USDT', 'KSM/USDT', 'NEAR/USDT', 'AAVE/USDT',
        'FIL/USDT', 'MATIC/USDT', 'ZEN/USDT', 'GRT/USDT', 'CHZ/USDT',
        'ANKR/USDT', 'LUNA/USDT', 'RVN/USDT', 'XEM/USDT', 'MANA/USDT',
        'HBAR/USDT', 'HOT/USDT', 'BTT/USDT', 'SC/USDT', 'DGB/USDT',
        )
symbols = list(tickers)

# 보유하고 있는 코인 갯수
current_hold = 0
for symbol in symbols:
    if info[symbol]['position'] != 'wait':
        current_hold += 1

total_hold = 3 # 투자할 코인 총 갯수
bull_profit = 1.012 # 롱 포지션 수익률
bear_profit = 0.988 # 숏 포지션 수익률

bot.sendMessage(chat_id = chat_id, text=f"{strategy}\n현재보유: {current_hold}개\n투자할 코인: {total_hold-current_hold}개\n기대 수익률: {(bull_profit-1)*100:.2f}%")

while True:
    now = datetime.datetime.now()
    time.sleep(1)
    # 익절한 코인 및 손절할 코인 체크
    if now.minute == 55 and 0 <= now.second <= 9:
        for symbol in symbols:
            try:
                free_balance = binance.fetch_balance()['USDT']['free'] - 300
                invest_money = free_balance * 4 / (total_hold - current_hold)
                current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                save_info(symbol)
                # 익절한 Coin 체크
                if info[symbol]['position'] == 'long' and info[symbol]['high'] > info[symbol]['price'] * bull_profit:
                    profit = (bull_profit - 1) * 100
                    bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} (롱)\n수익률: {profit:.2f}%\n성공")
                    invest_money = info[symbol]['price'] * info[symbol]['amount']
                    indi.saveHistory(strategy=strategy, symbol=symbol, position=info[symbol]['position'], invest_money=invest_money, profit_rate=profit)
                    info[symbol]['position'] = 'wait'
                    current_hold -= 1

                elif info[symbol]['position'] == 'short' and info[symbol]['low'] < info[symbol]['price'] * bear_profit:
                    profit = (1 - bear_profit) * 100
                    bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} (숏)\n수익률: {profit:.2f}%\n성공")
                    invest_money = info[symbol]['price'] * info[symbol]['amount']
                    indi.saveHistory(strategy=strategy, symbol=symbol, position=info[symbol]['position'], invest_money=invest_money, profit_rate=profit)
                    info[symbol]['position'] = 'wait'
                    current_hold -= 1

                # 롱 포지션 청산
                elif info[symbol]['position'] == 'long' and info[symbol]['stoch_slope_4h'] < 0:
                    binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=info[symbol]['amount'], params={"reduceOnly": True})
                    current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                    profit = (current_price - info[symbol]['price']) / info[symbol]['price'] * 100 # 수익률 계산
                    bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} (롱)\n수익률: {profit:.2f}%\n실패")
                    invest_money = info[symbol]['price'] * info[symbol]['amount']
                    indi.saveHistory(strategy=strategy, symbol=symbol, position=info[symbol]['position'], invest_money=invest_money, profit_rate=profit)
                    info[symbol]['position'] = 'wait'
                    current_hold -= 1

                # 숏 포지션 청산
                elif info[symbol]['position'] == 'short' and info[symbol]['stoch_slope_4h'] > 0:
                    binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=info[symbol]['amount'], params={"reduceOnly": True}) # 포지션 청산
                    current_price = binance.fetch_ticker(symbol=symbol)['close'] # 현재가 조회
                    profit = (info[symbol]['price'] - current_price) / current_price * 100 # 수익률 계산
                    bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} (숏)\n수익률: {profit:.2f}%\n실패")
                    invest_money = info[symbol]['price'] * info[symbol]['amount']
                    indi.saveHistory(strategy=strategy, symbol=symbol, position=info[symbol]['position'], invest_money=invest_money, profit_rate=profit)
                    info[symbol]['position'] = 'wait'
                    current_hold -= 1

                # 조건 만족시 Long Position
                elif info[symbol]['position'] == 'wait' and info[symbol]['rsi'] < 70 and current_hold < total_hold and \
                        info[symbol]['stoch_osc_d'] > 0 and info[symbol]['stoch_slope_d'] > 0 and \
                        info[symbol]['macd_osc'] > 0 and info[symbol]['close'] > info[symbol]['ema'] and \
                        info[symbol]['stoch_slope_4h'] > 0 and info[symbol]['stoch_slope_1h'] > 0:
                    amount = invest_money / current_price # 거래할 Coin 갯수
                    binance.create_market_buy_order(symbol, amount)
                    take_profit_params = {'stopPrice': current_price * bull_profit} # 이익실현 옵션
                    binance.create_order(symbol, 'take_profit_market', 'sell', amount, None, take_profit_params) # 이익실현 예약 주문
                    info[symbol]['price'] = current_price # 현재가 저장
                    info[symbol]['position'] = 'long' # Position 'long' 으로 변경
                    info[symbol]['amount'] = amount # Coin 갯수 저장
                    current_hold += 1
                    bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} (롱)\n투자금액: ${invest_money:.2f}\n현재보유: {current_hold}개\n거래")

                # 조건 만족시 Short Position
                elif info[symbol]['position'] == 'wait' and info[symbol]['rsi'] > 30 and current_hold < total_hold and \
                        info[symbol]['stoch_osc_d'] < 0 and info[symbol]['stoch_slope_d'] < 0 and \
                        info[symbol]['macd_osc'] < 0 and info[symbol]['close'] < info[symbol]['ema'] and \
                        info[symbol]['stoch_slope_4h'] < 0 and info[symbol]['stoch_slope_1h'] < 0:
                    amount = invest_money / current_price # 거래할 Coin 갯수
                    binance.create_market_sell_order(symbol, amount)
                    take_profit_params = {'stopPrice': current_price * bear_profit} # 이익실현 옵션
                    binance.create_order(symbol, 'take_profit_market', 'buy', amount, None, take_profit_params) # 이익실현 예약 주문
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'short' # Position 'short' 으로 변경
                    info[symbol]['amount'] = amount # Coin 갯수 저장
                    current_hold += 1
                    bot.sendMessage(chat_id = chat_id, text=f"(단타){symbol} (숏)\n투자금액: ${invest_money:.2f}\n현재보유: {current_hold}개\n거래")
            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
            time.sleep(0.1)
        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/binance_short.txt', 'w') as f:
            f.write(json.dumps(info))
