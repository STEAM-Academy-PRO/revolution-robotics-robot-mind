import math


def floor0(number, round_to=1):
    """Round toward 0"""
    if number < 0:
        return math.ceil(number * round_to) / round_to
    else:
        return math.floor(number * round_to) / round_to
