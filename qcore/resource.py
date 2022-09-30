""" """

import inspect
from typing import Any

from qcore.parameter import Parameter


class ResourceMetaclass(type):
    """ """

    def __init__(cls, name, bases, kwds) -> None:
        """ """
        super().__init__(name, bases, kwds)

        # find the parameters (gettable and settable) of the Resource class
        mro = inspect.getmro(cls)  # mro means method resolution order
        cls.params = {
            k: v for c in mro for k, v in c.__dict__.items() if isinstance(v, Parameter)
        }
        cls.gettable_params = {k for k, v in cls.params.items() if v.fget is not None}
        cls.settable_params = {k for k, v in cls.params.items() if v.fset is not None}

    def __repr__(cls) -> str:
        """ """
        return f"<class '{cls.__name__}'>"


class Resource(metaclass=ResourceMetaclass):
    """ """

    name: str = Parameter()

    def __init__(self, name: str, **parameters) -> None:
        """ """
        self._name = str(name)
        if parameters:  # set parameters with values supplied by the user, if available
            self.configure(**parameters)

    def __repr__(self) -> str:
        """ """
        return f"{self.__class__.__name__} '{self._name}'"

    @name.getter
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
        return self.__class__.params.keys() | self._attributes()

    @property
    def gettables(self) -> set[str]:
        """ """
        return self._attributes() | self.__class__.gettable_params

    @property
    def settables(self) -> set[str]:
        """ """
        return self._attributes() | self.__class__.settable_params

    def configure(self, **parameters) -> None:
        """ """
        settables = self.settables
        for name, value in parameters.items():
            if name in settables:
                setattr(self, name, value)

    def snapshot(self) -> dict[str, Any]:
        """ """
        return {name: getattr(self, name) for name in sorted(self.gettables)}
