def get_times():
    return ["на день", "на 3 дня", "на неделю", "навсегда"]


def get_prices():
    return [69, 99, 149, 499]


def get_add_time(price: int):
    if price in [69]:
        return 86400
    elif price in [99]:
        return 259200
    elif price in [149]:
        return 604800
    elif price in [499]:
        return 10000000
    else:
        return 0
