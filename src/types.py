import enum


class Markets(enum.StrEnum):
    SHARES = 'eq'
    CURRENCY = 'fx'
    FUTURES = 'fo'


class Endpoints(enum.StrEnum):
    TRADESTATS = 'tradestats'
    ORDERSTATS = 'orderstats'
    ORDERBOOKSTATS = 'obstats'
    HI2 = 'hi2'