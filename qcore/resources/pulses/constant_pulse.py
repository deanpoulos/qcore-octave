""" """

from typing import Union

import numpy as np

from qcore.pulses.pulse import Pulse


class ConstantPulse(Pulse):
    """ """

    def __init__(
        self,
        name: str,
        length: int = 1000,  # in ns
        I_ampx: float = 1.0,
        Q_ampx: Union[None, float] = 0.0,
        pad: int = 0,
        **parameters,
    ) -> None:
        """ """
        super().__init__(
            name=name,
            length=length,
            I_ampx=I_ampx,
            Q_ampx=Q_ampx,
            pad=pad,
            **parameters,
        )

    @property
    def total_I_amp(self) -> float:
        """ """
        return Pulse.BASE_AMP * self.I_ampx

    def sample(self):
        """ """
        has_constant_waveform = not self.pad
        if has_constant_waveform:
            return self._sample_constant_waveform()
        else:
            return self._sample_arbitrary_waveform()

    def _sample_constant_waveform(self):
        """ """
        total_amp = self.total_I_amp
        return (total_amp, 0.0) if self.has_mixed_waveforms() else (total_amp, None)

    def _sample_arbitrary_waveform(self):
        """ """
        samples = np.ones(self.length)
        pad = np.zeros(self.pad) if self.pad else []
        i_wave = (np.concatenate((samples, pad)) * self.total_I_amp).tolist()
        return (i_wave, 0.0) if self.has_mixed_waveforms() else (i_wave, None)
