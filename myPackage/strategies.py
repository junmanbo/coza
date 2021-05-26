import logging
import telegram

def Short():
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

