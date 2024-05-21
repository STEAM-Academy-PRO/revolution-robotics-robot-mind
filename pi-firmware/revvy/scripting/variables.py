from revvy.bluetooth.data_types import ScriptVariables


class Variable(object):
    def __init__(self) -> None:
        self.__script = None
        self.__name = None
        self.__value = None
        self.__is_set = False

    def __get_string_description(self) -> str:
        return 'Variable(script={},name="{}",value={},is_set={})'.format(
            self.__script, self.__name, self.__value, self.__is_set
        )

    def __repr__(self) -> str:
        return self.__get_string_description()

    def __str__(self) -> str:
        return self.__get_string_description()

    def bind(self, script: str, name: str):
        """Bind a variable to a script and give it a name."""
        self.__script = script
        self.__name = name
        self.__value = None

    @property
    def script(self):
        return self.__script

    @property
    def name(self):
        return self.__name

    @property
    def value(self):
        return self.__value

    def set_value(self, v) -> None:
        self.__value = v
        self.__is_set = True

    # Value has been set by ReportVariableChanged
    def value_is_set(self) -> bool:
        return self.__is_set

    # Is a valid assinged slot value. Slot might also be not assigned to
    # any value
    def is_valid(self) -> bool:
        return self.__name is not None

    def reset_value(self) -> None:
        self.__value = None
        self.__is_set = False


class VariableSlot(object):
    def __init__(self, max_num: int):
        self._variables: list[Variable] = [Variable()] * max_num

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"VariableSlot({str(self._variables)})"

    def values(self) -> ScriptVariables:
        return ScriptVariables([var.value for var in self._variables])

    def reset(self) -> None:
        self._variables = [Variable()] * len(self._variables)

    def slot(self, index: int) -> Variable:
        return self._variables[index]
