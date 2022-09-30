""" """

from labctrl.logger import logger

from qcore.resource import Resource


class ConnectionError(Exception):
    """ """


class Instrument(Resource):
    """ """

    def __init__(self, id: str, **parameters) -> None:
        """ """
        self._id = id
        self.connect()
        super().__init__(**parameters)

    def __repr__(self) -> str:
        """ """
        return f"{self.__class__.__name__}#{self._id}"

    @property
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
            return {"id": self.id, "name": self.name, "status": False}
        return super().snapshot()


class DummyInstrument(Instrument):
    """ """

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

    @property
    def gettable(self) -> int:
        return 0

    @property
    def settable(self) -> int:
        return self._settable

    @settable.setter
    def settable(self, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError(f"{self} 'settable' must be of {int}.")
        self._settable = value

if __name__ == "__main__":
    obj = DummyInstrument(name="d", id="0")
    print(obj.gettables)
    print(type(obj))
    