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
            msg = f"Failed to configure {self} as it is not connected (status = False)."
            raise ConnectionError(msg)
        super().configure(**parameters)

    def snapshot(self) -> dict:
        """ """
        if not self.status:
            logger.warning(f"{self} has disconnected, returning a minimal snapshot.")
            return {"id": self.id, "name": self.name}
        return super().snapshot()
