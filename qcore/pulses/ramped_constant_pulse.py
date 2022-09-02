""" """

import numpy as np

from qcore.pulses.constant_pulse import ConstantPulse
from qcore.pulses.ramps import ramp_cos, ramp_tanh

RAMP_MAP = {"cos": ramp_cos, "tanh": ramp_tanh}


class RampedConstantPulse(ConstantPulse):
    """ """

    def __init__(
        self,
        name: str = "ramped_constant_pulse",
        ramp: int = 0,
        rampfn: str = "cos",
        **parameters,
    ) -> None:
        """ """
        self.ramp: int = ramp
        self.rampfn: str = rampfn
        super().__init__(name, **parameters)

    @property
    def total_length(self) -> None:
        """ """
        return self.ramp * 2 + self.length + self.pad

    def sample(self) -> tuple[float, float | None] | tuple[list, list | None]:
        """ """
        has_constant_waveform = not (self.pad or self.ramp)
        if has_constant_waveform:
            return self._sample_constant_waveform()
        else:
            return self._sample_arbitrary_waveform()

    def _sample_arbitrary_waveform(self) -> tuple[list, list | None]:
        rampfn = RAMP_MAP[self.rampfn] if self.rampfn is not None else False
        ramp_up = rampfn(self.ramp, up=True) if rampfn else []
        samples = np.ones(self.length)
        ramp_down = rampfn(self.ramp, up=False) if rampfn else []
        pad = np.zeros(self.pad) if self.pad else []

        i_wave = np.concatenate((ramp_up, samples, ramp_down, pad)) * self.total_I_amp
        q_wave = np.zeros(self.total_length)

        return i_wave, q_wave if self.has_mixed_waveforms() else i_wave, None
