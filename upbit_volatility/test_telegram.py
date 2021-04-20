import telegram

my_token = '1623206706:AAHii0cbgXD287hBsNTjSjeTjnOW9R7-zvQ'
bot = telegram.Bot(token = my_token)
chat_id = '1459236537'
ticker = "KRW-TRX"
bot.sendMessage(chat_id = chat_id, text=f"저는 봇입니다.\n{ticker}를 갖고 있습니다.")
