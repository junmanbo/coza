#!/usr/bin/env python

import ccxt
import datetime
import time
import telegram
import json
import logging
from myPackage import indicators as indi

# 로깅 설정
logging.basicConfig(filename='./Log/binance_short.log', format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

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

data = {}
# 코인별 정보값 info 딕셔너리에 저장
def save_info(symbol):
    # 일봉 데이터 수집
    df = indi.getOHLCV(binance, symbol, '1d')
    stoch_osc_d = indi.calStochastic(df, 12, 5, 5)[0]
    stoch_slope_d = indi.calStochastic(df, 12, 5, 5)[1]
    macd_osc = indi.calMACD(df, 12, 26, 9)
    high = df['high'][-1]
    low = df['low'][-1]

    # 4시봉 데이터 수집
    df = indi.getOHLCV(binance, symbol, '4h')
    stoch_slope_4h = indi.calStochastic(df, 12, 5, 5)[1]

    return stoch_osc_d, stoch_slope_d, stoch_slope_4h, macd_osc, high, low


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
start_balance = binance.fetch_balance()['USDT']['total']

# 보유하고 있는 코인 갯수
current_hold = 0
for symbol in symbols:
    if info[symbol]['position'] != 'wait':
        current_hold += 1

total_hold = 3 # 투자할 코인 총 갯수
bull_profit = 1.05 # 롱 포지션 수익률
bear_profit = 0.95 # 숏 포지션 수익률

logging.info(f"{strategy}\n현재보유: {current_hold}개\n투자할 코인: {total_hold-current_hold}개\n기대 수익률: {(bull_profit-1)*100:.2f}%")

while True:
    now = datetime.datetime.now()
    time.sleep(1)
    # 익절한 코인 및 손절할 코인 체크
    if now.hour == 8 and now.minute == 57 and 0 <= now.second <= 9:
        for symbol in symbols:
            try:
                values = save_info(symbol) # 지표값 갱신
                logging.info(f'코인: {symbol}\n지표: {values}')
                current_price = binance.fetch_ticker(symbol)['close'] # 현재가 조회
                # 익절한 Coin 체크
                if info[symbol]['position'] == 'long' and values[4] > info[symbol]['price'] * bull_profit:
                    profit = (bull_profit - 1) * 100
                    invest_money = info[symbol]['price'] * info[symbol]['amount']
                    indi.saveHistory(strategy, symbol, info[symbol]['position'], invest_money, profit) # 엑셀 파일에 저장
                    info[symbol]['position'] = 'wait'
                    current_hold -= 1
                    logging.info(f"{symbol} (롱)\n수익률: {profit:.2f}%\n성공")

                elif info[symbol]['position'] == 'short' and values[5] < info[symbol]['price'] * bear_profit:
                    profit = (1 - bear_profit) * 100
                    invest_money = info[symbol]['price'] * info[symbol]['amount']
                    indi.saveHistory(strategy, symbol, info[symbol]['position'], invest_money, profit) # 엑셀 파일에 저장
                    info[symbol]['position'] = 'wait'
                    current_hold -= 1
                    logging.info(f"{symbol} (숏)\n수익률: {profit:.2f}%\n성공")

                # 롱 포지션 청산
                elif info[symbol]['position'] == 'long':
                    binance.create_order(symbol=symbol, type="MARKET", side="sell", amount=info[symbol]['amount'], params={"reduceOnly": True})
                    binance.cancel_all_orders(symbol)
                    profit = (current_price - info[symbol]['price']) / info[symbol]['price'] * 100 # 수익률 계산
                    invest_money = info[symbol]['price'] * info[symbol]['amount']
                    indi.saveHistory(strategy, symbol, info[symbol]['position'], invest_money, profit)
                    info[symbol]['position'] = 'wait'
                    current_hold -= 1
                    logging.info(f"{symbol} (롱)\n수익률: {profit:.2f}%\n실패")

                # 숏 포지션 청산
                elif info[symbol]['position'] == 'short':
                    binance.create_order(symbol=symbol, type="MARKET", side="buy", amount=info[symbol]['amount'], params={"reduceOnly": True}) # 포지션 청산
                    binance.cancel_all_orders(symbol)
                    profit = (info[symbol]['price'] - current_price) / current_price * 100 # 수익률 계산
                    invest_money = info[symbol]['price'] * info[symbol]['amount']
                    indi.saveHistory(strategy, symbol, info[symbol]['position'], invest_money, profit)
                    info[symbol]['position'] = 'wait'
                    current_hold -= 1
                    logging.info(f"{symbol} (숏)\n수익률: {profit:.2f}%\n실패")

                # 조건 만족시 Long Position
                elif info[symbol]['position'] == 'wait' and current_hold < total_hold and \
                        values[0] > 0 and values[1] > 0 and values[2] > 0 and values[3] > 0:
                    free_balance = binance.fetch_balance()['USDT']['free'] - 100
                    invest_money = free_balance * 4 / (total_hold - current_hold)
                    amount = invest_money / current_price # 거래할 Coin 갯수
                    binance.create_limit_buy_order(symbol, amount, current_price)
                    take_profit_params = {'stopPrice': current_price * bull_profit} # 이익실현 옵션
                    binance.create_order(symbol, 'take_profit_market', 'sell', amount, None, take_profit_params) # 이익실현 예약 주문
                    info[symbol]['price'] = current_price # 현재가 저장
                    info[symbol]['position'] = 'long' # Position 'long' 으로 변경
                    info[symbol]['amount'] = amount # Coin 갯수 저장
                    current_hold += 1
                    logging.info(f"{symbol} (롱)\n투자금액: ${invest_money:.2f}\n현재보유: {current_hold}개\n거래")

                # 조건 만족시 Short Position
                elif info[symbol]['position'] == 'wait' and current_hold < total_hold and \
                        values[0] < 0 and values[1] < 0 and values[2] < 0 and values[3] < 0:
                    free_balance = binance.fetch_balance()['USDT']['free'] - 100
                    invest_money = free_balance * 4 / (total_hold - current_hold)
                    amount = invest_money / current_price # 거래할 Coin 갯수
                    binance.create_limit_sell_order(symbol, amount, current_price)
                    take_profit_params = {'stopPrice': current_price * bear_profit} # 이익실현 옵션
                    binance.create_order(symbol, 'take_profit_market', 'buy', amount, None, take_profit_params) # 이익실현 예약 주문
                    info[symbol]['price'] = current_price
                    info[symbol]['position'] = 'short' # Position 'short' 으로 변경
                    info[symbol]['amount'] = amount # Coin 갯수 저장
                    current_hold += 1
                    logging.info(f"{symbol} (숏)\n투자금액: ${invest_money:.2f}\n현재보유: {current_hold}개\n거래")
            except Exception as e:
                bot.sendMessage(chat_id = chat_id, text=f"에러발생 {e}")
                logging.error(e)
            time.sleep(0.1)
        # 파일에 수집한 정보 및 거래 정보 파일에 저장
        with open('./Data/binance_short.txt', 'w') as f:
            f.write(json.dumps(info))
        end_balance = binance.fetch_balance()['USDT']['total']
        bot.sendMessage(chat_id = chat_id, text=f"정산\n어제자산: ${start_balance} -> 현재자산: ${end_balance}\n수익금: ${end_balance - start_balance}")
        start_balance = end_balance
