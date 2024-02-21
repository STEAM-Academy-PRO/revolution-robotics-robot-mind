"""
    Util
"""


def create_unique_file(base_filename):
    """Creates a new fie that's not existing yet with a number iterator if needed"""
    try:
        return open(base_filename, "x")
    except FileExistsError:

        i = 1
        while True:
            try:
                return open(base_filename + str(i), "x")
            except FileExistsError:
                i += 1
