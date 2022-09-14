""" """

from qcore.instruments import *


class InstrumentConfig(dict):
    """ """

    def __init__(self) -> None:
        """
        key: Instrument class
        value: list of ids corresponding to the instruments qcrew has of the given class
        """
        self[MS46522B] = ["VNA1"]
        self[QM] = [None]
        self[SC5503B] = [10002656]
        self[SC5511A] = [10002657]
        self[SA124] = ([19184645, 20234154],)
        self[LMS] = list(range(25330, 25338))
        self[GS200] = ["90X823743", "91X336839"]
