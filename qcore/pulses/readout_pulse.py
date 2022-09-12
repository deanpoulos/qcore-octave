""" """

from pathlib import Path

import numpy as np

from qcore.pulses.constant_pulse import ConstantPulse
from qcore.pulses.gaussian_pulse import GaussianPulse
from qcore.pulses.digital_waveform import DigitalWaveform
from qcore.pulses.pulse import Pulse


class ReadoutPulse(Pulse):
    """ """

    def __init__(
        self,
        name: str,
        weights: tuple[float, float, float, float] | str = (1.0, 0.0, 0.0, 1.0),
        threshold: float | None = None,  # not None only for Optimized weights
        **parameters,
    ) -> None:
        """ """
        # for constant Weights, specify tuple (i_cos, i_sin, q_cos, q_sin)
        # for optimized Weights, specify path string to npz file
        self.weights: tuple[float, float, float, float] | str = weights
        self.threshold: float | None = threshold
        super().__init__(name, digital_marker=DigitalWaveform("ADC_ON"), **parameters)

    @property
    def has_optimized_weights(self) -> bool:
        """ """
        try:
            return Path(self.weights).exists()
        except TypeError:
            return False

    def sample_integration_weights(self) -> tuple[dict[str, list], dict[str, list]]:
        """ """
        if self.has_optimized_weights:
            weights = np.load(self.weights)  # assume these are the correct length
            cos_weights = {"cosine": weights["I"][0], "sine": weights["I"][1]}
            sin_weights = {"cosine": weights["Q"][0], "sine": weights["Q"][1]}
        else:
            weights = [[(weight, self.total_length)] for weight in self.weights]
            cos_weights = {"cosine": weights[0], "sine": weights[1]}
            sin_weights = {"cosine": weights[2], "sine": weights[3]}
        return (cos_weights, sin_weights)


class ConstantReadoutPulse(ConstantPulse, ReadoutPulse):
    """ """


class GaussianReadoutPulse(GaussianPulse, ReadoutPulse):
    """ """
