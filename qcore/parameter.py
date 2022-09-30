""" """

import inspect
from typing import Any, Callable, get_type_hints, Type, Union


class MISSING:
    """Sentinel for missing parameter fields"""

    def __repr__(self):
        """ """
        return "<MISSING>"


class Parameter:
    """ """

    def __init__(
        self,
        bounds: Union[Callable, list, None] = None,
    ) -> None:
        """ """
        self._name, self.type = None, None  # set by __set_name__()
        self.fget, self.fset = None, None  # updated by getter() and setter()
        self.hint: str = None  # set by _parse_bounds()
        self._bound = self._parse_bounds(bounds)

    def _parse_bounds(self, bounds: Union[Callable, list, None]) -> Callable:
        """ """
        if bounds is None:
            self.hint = "unbounded"
            return lambda *_: True
        elif isinstance(bounds, list) and len(bounds) == 2:
            min, max = bounds
            self.hint = f"closed interval [{min}, {max}]"
            return lambda val, _: min <= val <= max
        elif isinstance(bounds, set):
            self.hint = f"discrete set of values {bounds}"
            return lambda val, _: val in bounds
        elif inspect.isfunction(bounds):
            num_args = len(inspect.signature(bounds).parameters)
            self.hint = f"tested by fn {bounds.__qualname__}"
            if num_args == 1:  # fn needs one argument which is the value to be tested
                return lambda val, _: bounds(val)
            elif num_args == 2:  # fn also needs the object the Parameter is bound to
                return lambda val, obj: bounds(val, obj)

    def __set_name__(self, cls: Type[Any], name: str):
        """ """
        type_hints = get_type_hints(cls)
        self.type = MISSING if name not in type_hints else type_hints[name]
        self._name = name

    def __get__(self, obj: Any, cls: Type[Any] = None) -> Any:
        """ """
        if obj is None:  # user wants to inspect this Parameter's object representation
            return self

        if self.fget is None:  # user has not specified a getter for this Parameter
            raise AttributeError(f"'{self._name}' is not gettable.")

        value = self.fget(obj)
        self.validate(value, obj)
        return value

    def __set__(self, obj: Any, value: Any) -> None:
        """ """
        if self.fset is None:
            raise AttributeError(f"'{self._name}' is not settable.")
        self.validate(value, obj)
        self.fset(obj, value)

    def validate(self, value: Any, obj: Any) -> None:
        """ """
        value = value if self.type is MISSING else self._typecheck(value)
        in_bounds = self._bound(value, obj)
        if not in_bounds:
            message = f"'{self._name}' {value = } is out of bounds. Range: {self.hint}."
            raise ValueError(message)

    def _typecheck(self, value: Any) -> Any:
        """ """
        try:
            self.type(value)
        except (TypeError, ValueError):
            message = f"Expect '{self._name}' value of {self.type}, got {type(value)}."
            raise TypeError(message) from None
        else:
            return value

    @property
    def name(self) -> str:
        """ """
        return self._name

    def getter(self, getter):
        """ """
        self.fget = getter
        return self

    def setter(self, setter):
        """ """
        self.fset = setter
        return self

    def is_gettable(self) -> bool:
        """ """
        return self.fget is not None

    def is_settable(self) -> bool:
        """ """
        return self.fset is not None
