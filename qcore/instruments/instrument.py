""" """

import numpy as np

from qcore.helpers.logger import logger
from qcore.variables.parameter import Parameter
from qcore.resource import Resource

class ConnectionError(Exception):
    """ """


class Instrument(Resource):
    """ """

    id: str = Parameter()

    def __init__(self, id: str, **parameters) -> None:
        """ """
        self._id = str(id)
        self.connect()
        super().__init__(**parameters)

    def __repr__(self) -> str:
        """ """
        return f"{self.__class__.__name__}#{self._id}"

    @id.getter
    def id(self) -> str:
        """ """
        return str(self._id)

    @property
    def status(self) -> bool:
        """ """
        raise NotImplementedError("Subclasses must implement 'status'.")

    def connect(self) -> None:
        """ """
        raise NotImplementedError("Subclasses must implement 'connect()'.")

    def disconnect(self) -> None:
        """ """
        raise NotImplementedError("Subclasses must implement 'disconnect()'.")

    def configure(self, **parameters) -> None:
        """ """
        if not self.status:
            raise ConnectionError(f"{self} is not connected (status = False).")
        super().configure(**parameters)

    def snapshot(self) -> dict:
        """ """
        if not self.status:
            logger.warning(f"{self} is disconnected, returning a minimal snapshot.")
            return {"id": self.id, "name": self.name}
        return super().snapshot()


class DummyInstrument(Instrument):
    """ """

    gettable: int = Parameter()
    settable: int = Parameter()

    def __init__(self, **parameters) -> None:
        self._status = None
        super().__init__(**parameters)
        self._settable = 1

    def connect(self) -> None:
        """ """
        self._status = True

    def disconnect(self) -> None:
        """ """
        self._status = False

    @property
    def status(self) -> bool:
        return self._status

    @gettable.getter
    def gettable(self) -> int:
        return np.random.randint(0, 100)

    @settable.getter
    def settable(self) -> int:
        return self._settable

    @settable.setter
    def settable(self, value: int) -> None:
        self._settable = value
