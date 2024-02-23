import math

def floor0(number, round_to=1):
    """Simple floor function that works reversed for minus values, having 0 between -1 and 1"""
    if number < 0:
        return math.ceil(number * round_to) / round_to
    else:
        return math.floor(number * round_to) / round_to
