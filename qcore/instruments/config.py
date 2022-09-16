""" """

from asyncio import streams
from qcore.instruments import *
from qcore.instruments.instrument import Instrument


class DummyInstrument(Instrument):
    """ """

    def __init__(self, **parameters) -> None:
        super().__init__(**parameters)
        self._dummy_settable = "YOU CAN SET ME"

    def connect(self) -> None:
        """ """
        print("dummy instrument connected")

    def disconnect(self) -> None:
        """ """
        print("dummy instrument disconnected")

    @property
    def status(self) -> bool:
        return True

    @property
    def dummy_gettable(self) -> str:
        return "GET THIS"

    @property
    def dummy_settable(self) -> str:
        return self._dummy_settable

    @dummy_settable.setter
    def dummy_settable(self, value) -> None:
        self._dummy_settable = value


class InstrumentConfig(dict):
    """ """

    def __init__(self) -> None:
        """
        key: Instrument class
        value: list of ids corresponding to the instruments qcrew has of the given class
        """
        self[MS46522B] = ["VNA1"]
        self[SC5503B] = ["10002656"]
        self[SC5511A] = ["10002657"]
        self[SA124] = ["19184645", "20234154"]
        self[LMS] = [str(id) for id in range(25330, 25338)]
        self[GS200] = ["90X823743", "91X336839"]
        self[DummyInstrument] = [""]
