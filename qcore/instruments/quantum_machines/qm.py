""" """

from labctrl import Instrument
from qm.QuantumMachine import QuantumMachine
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.QmJob import QmJob
from qm.qua._dsl import _ProgramScope

from qcore.instruments.quantum_machines.config_builder import QMConfigBuilder, QMConfig
from qcore.instruments.vaunix.lms import LMS
from qcore.elements.mode import Mode


class QM(Instrument):
    """By convention, we ensure only one QM is open at a given time"""

    def __init__(self, id: str | None = None, name: str = "QM") -> None:
        """ """
        self._status: bool = None

        self._qmm: QuantumMachinesManager = None
        self._qm: QuantumMachine = None
        self._qm_config: QMConfig | None = None
        self._qcb: QMConfigBuilder = QMConfigBuilder()

        super().__init__(id=id, name=name)

    def connect(self) -> None:
        """ """
        if self._qmm is not None:
            self.disconnect()
        self._qmm = QuantumMachinesManager(host=self.id)  # TODO error handling
        self._status = True

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

    def get_config(self) -> QMConfig | None:
        """ """
        return self._qm_config

    def execute(
        self,
        qua_program: _ProgramScope,
        modes: tuple[Mode],
        local_oscillators: tuple[LMS],
    ) -> QmJob:
        """ """
        self._qm_config = self._qcb.build_config(modes, local_oscillators)
        # TODO error handling, if exception, set status = False, else set True
        self._qm = self._qmm.open_qm(self._qm_config, close_other_machines=True)
        return self._qm.execute(qua_program)
