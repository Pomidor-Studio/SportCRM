def pluralize(singular, plural1, plural2, count):
    if count % 10 == 1 and count % 100 != 11:
        return singular
    elif 2 <= count % 10 <= 4 and (count % 100 < 12 or count % 100 > 14):
        return plural1
    elif count % 10 == 0 or (5 <= count % 10 <= 9) or (11 <= count % 100 <= 14):
        return plural2

    return singular
