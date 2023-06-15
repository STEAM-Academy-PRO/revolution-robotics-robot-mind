class Variable(object):
    def __init__(self):
        self.__script = None
        self.__name = None
        self.__value = None
        self.__is_set = False

    def __get_string_description(self):
        return 'Variable(script={},name="{}",value={},is_set={})'.format(
            self.__script,
            self.__name,
            self.__value,
            self.__is_set)

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
        self.__is_set = True

    # Value has been set by ReportVariableChanged
    def value_is_set(self):
        return self.__is_set

    # Is a valid assinged slot value. Slot might also be not assigned to
    # any value
    def is_valid(self):
        return self.__name is not None

    def reset_value(self):
      self.__value = None
      self.__is_set = None


class VariableSlot(object):
    def __init__(self, max_num):
        self.__v = [Variable()] * max_num

    def __get_string_description(self):
        return 'VariableSlot(' + str(self.__v) + ')'

    def __repr__(self):
        return self.__get_string_description()

    def __str__(self):
        return self.__get_string_description()

    def get_variable(self, slot_idx):
        return self.__v[slot_idx]

    def reset(self):
        self.__v = [Variable()] * len(self.__v)
