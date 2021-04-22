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
