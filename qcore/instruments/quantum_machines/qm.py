""" """

import numpy as np

from qm.QuantumMachine import QuantumMachine
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.QmJob import QmJob
from qm.qua._dsl import _ProgramScope

from qcore.helpers.logger import logger
from qcore.instruments.instrument import Instrument, ConnectionError
from qcore.instruments.quantum_machines.config_builder import QMConfigBuilder, QMConfig
from qcore.instruments.quantum_machines.result_fetcher import QMResultFetcher
from qcore.instruments.vaunix.lms import LMS
from qcore.elements.element import Element


class QM(Instrument):
    """By convention, we ensure only one QM is open at a given time"""

    def __init__(
        self, elements: tuple[Element] = None, oscillators: tuple[LMS] = None
    ) -> None:
        """ """
        self._status: bool = None

        self._qmm: QuantumMachinesManager = None
        self._qm: QuantumMachine = None
        self._config: QMConfig = None
        self._qcb: QMConfigBuilder = QMConfigBuilder()

        self._elements: tuple[Element] = elements
        self._oscillators: tuple[LMS] = oscillators
        
        self._job: QmJob = None
        self._qrf: QMResultFetcher = None

        super().__init__(id=None, name="QM")

    def __repr__(self) -> str:
        """ """
        return self.__class__.__name__

    def connect(self) -> None:
        """ """
        if self._qmm is not None:
            self.disconnect()
        try:
            self._qmm = QuantumMachinesManager()
        except Exception as err:
            raise ConnectionError(f"Failed to connect QM. Details: {err}.") from None
        else:
            self._status = True
            if self._elements is not None and self._oscillators is not None:
                self.open(self._elements, self._oscillators)

    def open(self, elements: tuple[Element], oscillators: tuple[LMS]) -> QuantumMachine:
        """ """
        self._config = self._qcb.build_config(elements, oscillators)
        self._qm = self._qmm.open_qm(self._config, close_other_machines=True)
        return self._qm

    def get_config(self) -> dict:
        """ """
        return self._qm.get_config()

    def disconnect(self) -> None:
        """ """
        if self._qm is not None:
            self._qm.close()
        self._qmm.close()
        self._status = False

    @property
    def status(self) -> bool:
        """ """
        return self._status

    def execute(self, qua_program: _ProgramScope) -> None:
        """ """
        if self._config is None or self._qm is None:
            logger.warning("Can't execute program, QM hasn't been opened with a config")
        else:
            # TODO error handling, if exception, set status = False, else set True
            self._job = self._qm.execute(qua_program)
            self._qrf = QMResultFetcher(self._job.result_handles)

    def is_processing(self) -> bool:
        """ """
        return self._qrf.is_done_fetching

    def fetch(self) -> tuple[dict[str, np.ndarray], int, int]:
        """ """
        return (self._qrf.fetch(), *self._qrf.counts)
