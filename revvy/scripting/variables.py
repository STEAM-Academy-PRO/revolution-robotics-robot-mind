class Variable(object):
    def __init__(self):
        self.__script = None
        self.__name = None
        self.__value = 0.0

    def __get_string_description(self):
        return 'var:script:"{}",name:"{}",val:"{}"'.format(
            self.__script,
            self.__name,
            self.__value)

    def __repr__(self):
        return self.__get_string_description()

    def __str__(self):
        return self.__get_string_description()

    def init(self, script, name, value):
        self.__script = script
        self.__name = name
        self.__value = value

    def get_script(self):
        return self.__script

    def get_name(self):
        return self.__name

    def get_value(self):
        return self.__value

    def set_value(self, v):
        self.__value = v

    def is_valid(self):
        return self.__name is not None


class ScriptvarsStorage(object):
    def __init__(self):
        self.__v = {}

    def __iter__(self):
        return iter(sorted(self.__v.items()))

    def __next__(self):
        return next(self)

    def __get_string_description(self):
        return 'var_storage(' + str(self.__v) + ')'

    def __repr__(self):
        return self.__get_string_description()

    def __str__(self):
        return self.__get_string_description()

    def get_by_slot(self, slot):
        return self.__v.setdefault(slot, Variable())

    def reset(self):
        self.__v = {}
