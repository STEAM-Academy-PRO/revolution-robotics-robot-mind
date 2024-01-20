"""
Reverse lookup constant names:

If you have something like:

class Something:
    ASDF: 1,
    BBBB: 2,
    CCCC: 3

... this util will resolve 1,2,3 to ASDF, BBBB, CCCC respectively.


"""

def get_constant_name(num, parent_class):
    """ returns the resolved constant variable name """
    return next((name for name, value in vars(parent_class).items()
                if not name.startswith('_') and value == num), None)
