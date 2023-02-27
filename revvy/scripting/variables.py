class Variable(object):
    def __init__(self, name, value: float):
        self._name = name
        self._value = value
        self._on_variable_changed = True
        self._script_id = None

    @property
    def script_id(self):
        return self._script_id

    @script_id.setter
    def script_id(self, new_id):
        self._script_id = new_id

    @property
    def on_variable_changed(self):
        return self._on_variable_changed

    @on_variable_changed.setter
    def on_variable_changed(self, val):
        self._on_variable_changed = val

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = new_name

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, new_value: float):
        self._value = new_value

    @property
    def conv_to_dict(self):
        return {self._name: self.value}


class VariableSlot(object):
    def __init__(self, max_num):
        self._max_num = max_num
        self._variables = [
            Variable('NaN', 0.0),
            Variable('NaN', 0.0),
            Variable('NaN', 0.0),
            Variable('NaN', 0.0),
        ]

    def one_variable(self, num):
        return self._variables[num]

    def get_variable(self, name):
        for variable in self._variables:
            if variable.name is name:
                return variable
        return None

    def set_variable(self, name, value):
        is_new = True
        for variable in self._variables:
            if variable.name is name:
                if variable.value is not value:
                    variable.on_variable_changed = True
                variable.value = value
                is_new = False

        if is_new:
            self.add_variable(Variable(name, value))

    def add_variable(self, variable: Variable):
        self._variables.append(variable)

    def get_variables(self):
        return self._variables

    def clear(self):
        self._variables.clear()
        self._variables.append(Variable('NaN', 0.0))
        self._variables.append(Variable('NaN', 0.0))
        self._variables.append(Variable('NaN', 0.0))
        self._variables.append(Variable('NaN', 0.0))
