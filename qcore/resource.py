""" """

import inspect
from typing import Any


class ResourceMetaclass(type):
    """ """

    def __init__(cls, name, bases, kwds) -> None:
        """ """
        super().__init__(name, bases, kwds)

        # find the parameters (gettable and settable) of the Resource class
        mro = inspect.getmro(cls)  # mro means method resolution order
        cls._properties = {
            k: v for c in mro for k, v in c.__dict__.items() if isinstance(v, property)
        }
        del cls._properties["parameters"]

    @property
    def properties(cls) -> set[str]:
        """ """
        return set(cls._properties.keys())

    @property
    def gettables(cls) -> set[str]:
        """ """
        return {k for k, v in cls._properties.items() if v.fget is not None}

    @property
    def settables(cls) -> set[str]:
        """ """
        return {k for k, v in cls._properties.items() if v.fset is not None}

    def __repr__(cls) -> str:
        """ """
        return f"<class '{cls.__name__}'>"


class Resource(metaclass=ResourceMetaclass):
    """ """

    def __init__(self, name: str, **parameters) -> None:
        """ """
        self._name = str(name)
        if parameters:  # set parameters with values supplied by the user, if available
            self.configure(**parameters)

    def __repr__(self) -> str:
        """ """
        return f"{self.__class__.__name__} '{self._name}'"

    @property
    def name(self) -> str:
        """ """
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """ """
        self._name = str(value)

    def _attributes(self) -> set[str]:
        """ """
        return {k for k in self.__dict__.keys() if not k.startswith("_")}

    @property
    def parameters(self) -> set[str]:
        """ """
        return self.__class__.properties | self._attributes()

    def configure(self, **parameters) -> None:
        """ """
        settables = self._attributes() | self.__class__.settables
        for name, value in parameters.items():
            if name in settables:
                setattr(self, name, value)

    def snapshot(self) -> dict[str, Any]:
        """ """
        gettables = self._attributes() | self.__class__.gettables
        return {name: getattr(self, name) for name in sorted(gettables)}
