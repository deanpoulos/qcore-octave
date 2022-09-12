""" """

import numpy as np

from qcore.pulses.pulse import Pulse


class NumericalPulse(Pulse):
    """ """

    def __init__(
        self,
        path: str,
        name: str,
        length: int | None = None,  # None when no NumericalPulse is loaded from npzfile
        I_ampx: float = 1.0,
        Q_ampx: float = 1.0,
        pad: int | None = None,
    ) -> None:
        """ """
        super().__init__(name, length, I_ampx=I_ampx, Q_ampx=Q_ampx, pad=pad)

        self._path, self._pulse = None, None
        self._length, self._pad = None, None
        self.path = path  # will update _path, _pulse, _length, _pad

    @property
    def path(self) -> str:
        """ """
        return self._path

    @path.setter
    def path(self, value: str) -> None:
        """ """
        self._pulse = np.load(value)
        self._path = value
        self._length = len(self._pulse)
        cycle = Pulse.CLOCK_CYCLE
        self._pad = (cycle - self._length % cycle) if self._length % cycle else 0

    @property
    def length(self) -> int:
        """ """
        return self._length

    @property
    def pad(self) -> int:
        """ """
        return self._pad

    @property
    def total_I_ampx(self) -> float:
        """ """
        return Pulse.BASE_AMP * self.I_ampx

    @property
    def total_Q_ampx(self) -> float:
        """ """
        return Pulse.BASE_AMP * self.Q_ampx

    def sample(self) -> tuple[list, list]:
        """ """
        i_samples = np.real(self._pulse)
        q_samples = np.imag(self._pulse)
        pad = np.zeros(self.pad) if self.pad else []

        i_wave = np.concatenate((i_samples, pad))
        q_wave = np.concatenate((q_samples, pad))
        return (i_wave.tolist(), q_wave.tolist())
